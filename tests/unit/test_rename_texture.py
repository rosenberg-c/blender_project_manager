"""Unit tests for rename_texture Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest


class TestRenameTexturePathHandling:
    """Tests for proper Path object handling in rename_texture.py."""

    def test_process_blend_files_converts_paths_to_strings(self, tmp_path):
        """Test that Path objects are converted to strings when opening .blend files.

        This test verifies the fix for the bug where PosixPath objects were passed
        directly to bpy.ops.wm.open_mainfile.filepath, causing the error:
        "WM_OT_open_mainfile.filepath expected a string type, not PosixPath"
        """
        # Setup: Create a project structure with .blend files
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create some dummy .blend files
        blend1 = project_root / "scene1.blend"
        blend2 = project_root / "subdir" / "scene2.blend"
        blend2.parent.mkdir()

        blend1.write_bytes(b"FAKE_BLEND")
        blend2.write_bytes(b"FAKE_BLEND")

        # Create texture files
        old_texture = project_root / "old_texture.png"
        new_texture = project_root / "new_texture.png"
        old_texture.write_bytes(b"FAKE_PNG")

        # Mock the bpy module (Blender Python API)
        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.images = []  # No images in test files

        # Import and patch the rename_texture module
        import sys
        import importlib

        # Add blender_lib to path if not already there
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Import the module with mocked bpy
            if 'rename_texture' in sys.modules:
                importlib.reload(sys.modules['rename_texture'])
            import rename_texture

            # Call the function that processes .blend files
            result = rename_texture.process_blend_files(
                root_dir=str(project_root),
                old_path_abs=str(old_texture.resolve()),
                new_path_abs=str(new_texture.resolve()),
                dry_run=True
            )

        # Verify: Check that open_mainfile was called with STRING arguments, not Path objects
        assert mock_bpy.ops.wm.open_mainfile.called, "open_mainfile should have been called"

        # Get all calls to open_mainfile
        calls = mock_bpy.ops.wm.open_mainfile.call_args_list

        # Verify we opened the correct number of files
        assert len(calls) == 2, f"Expected 2 blend files to be opened, got {len(calls)}"

        # Check each call to ensure filepath is a string, not a Path
        for i, call_obj in enumerate(calls):
            # call_obj is a call() object, get the kwargs
            kwargs = call_obj.kwargs
            assert 'filepath' in kwargs, f"Call {i}: 'filepath' kwarg missing"

            filepath_arg = kwargs['filepath']

            # CRITICAL ASSERTION: Must be a string, not a Path object
            assert isinstance(filepath_arg, str), (
                f"Call {i}: filepath must be a string, got {type(filepath_arg).__name__}. "
                f"This causes the error: 'WM_OT_open_mainfile.filepath expected a string type, not PosixPath'"
            )

            # Verify it's one of our test files
            assert filepath_arg.endswith('.blend'), f"Call {i}: Expected .blend file, got {filepath_arg}"

    def test_process_blend_files_returns_correct_structure(self, tmp_path):
        """Test that process_blend_files returns the expected result structure."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "test.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        old_texture = project_root / "old.png"
        new_texture = project_root / "new.png"
        old_texture.write_bytes(b"FAKE_PNG")

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.images = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import rename_texture

            result = rename_texture.process_blend_files(
                root_dir=str(project_root),
                old_path_abs=str(old_texture.resolve()),
                new_path_abs=str(new_texture.resolve()),
                dry_run=True
            )

        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'updated_files' in result, "Result should have 'updated_files' key"
        assert 'errors' in result, "Result should have 'errors' key"
        assert 'warnings' in result, "Result should have 'warnings' key"

        # Verify types
        assert isinstance(result['updated_files'], list), "'updated_files' should be a list"
        assert isinstance(result['errors'], list), "'errors' should be a list"
        assert isinstance(result['warnings'], list), "'warnings' should be a list"

    def test_updated_files_contain_string_paths(self, tmp_path):
        """Test that updated_files in result contain string paths, not Path objects."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "test.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        old_texture = project_root / "old.png"
        new_texture = project_root / "new.png"
        old_texture.write_bytes(b"FAKE_PNG")

        # Mock bpy with an image that references the old texture
        mock_image = MagicMock()
        mock_image.filepath = "//" + old_texture.name
        mock_image.name = "test_image"

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: str(old_texture) if old_texture.name in p else p
        mock_bpy.path.relpath = lambda p: "//" + Path(p).name

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import rename_texture

            result = rename_texture.process_blend_files(
                root_dir=str(project_root),
                old_path_abs=str(old_texture.resolve()),
                new_path_abs=str(new_texture.resolve()),
                dry_run=True
            )

        # Verify: If there are updated files, their 'file' field should be strings
        for file_info in result['updated_files']:
            assert isinstance(file_info['file'], str), (
                f"File path in updated_files must be a string, got {type(file_info['file']).__name__}"
            )
