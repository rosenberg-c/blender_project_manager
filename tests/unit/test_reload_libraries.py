"""Unit tests for reload_libraries Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestReloadLibrariesPathHandling:
    """Tests for proper Path object handling in reload_libraries.py."""

    def test_reload_libraries_in_file_converts_paths_to_strings(self, tmp_path):
        """Test that Path objects are converted to strings when opening .blend files.

        Similar to the rename_texture bug fix, this ensures we don't pass
        PosixPath objects to bpy.ops.wm.open_mainfile.filepath.
        """
        # Setup: Create a test .blend file
        blend_file = tmp_path / "test.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock the bpy module
        mock_library = MagicMock()
        mock_library.name = "LinkedLib"
        mock_library.filepath = "//linked.blend"
        mock_library.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]

        # Import and patch
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import reload_libraries

            # Call the function
            result = reload_libraries.reload_libraries_in_file(
                blend_file_path=str(blend_file),
                dry_run=False
            )

        # Verify: open_mainfile was called with a STRING, not a Path object
        assert mock_bpy.ops.wm.open_mainfile.called, "open_mainfile should have been called"

        call_kwargs = mock_bpy.ops.wm.open_mainfile.call_args.kwargs
        assert 'filepath' in call_kwargs, "'filepath' kwarg missing"

        filepath_arg = call_kwargs['filepath']
        assert isinstance(filepath_arg, str), (
            f"filepath must be a string, got {type(filepath_arg).__name__}. "
            f"This would cause: 'WM_OT_open_mainfile.filepath expected a string type, not PosixPath'"
        )

    def test_reload_libraries_in_file_reloads_libraries(self, tmp_path):
        """Test that libraries are actually reloaded when dry_run=False."""
        # Setup
        blend_file = tmp_path / "test.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock libraries
        mock_lib1 = MagicMock()
        mock_lib1.name = "Library1"
        mock_lib1.filepath = "//lib1.blend"
        mock_lib1.reload = MagicMock()

        mock_lib2 = MagicMock()
        mock_lib2.name = "Library2"
        mock_lib2.filepath = "//lib2.blend"
        mock_lib2.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_lib1, mock_lib2]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import reload_libraries

            result = reload_libraries.reload_libraries_in_file(
                blend_file_path=str(blend_file),
                dry_run=False
            )

        # Verify: Both libraries were reloaded
        assert mock_lib1.reload.called, "Library1.reload() should have been called"
        assert mock_lib2.reload.called, "Library2.reload() should have been called"

        # Verify: File was saved after reloading
        assert mock_bpy.ops.wm.save_mainfile.called, "File should be saved after reloading libraries"

        # Verify: Result structure
        assert result["libraries_found"] == 2, "Should find 2 libraries"
        assert result["libraries_reloaded"] == 2, "Should reload 2 libraries"
        assert len(result["library_details"]) == 2, "Should have details for 2 libraries"

    def test_reload_libraries_dry_run_does_not_reload(self, tmp_path):
        """Test that dry_run=True does not actually reload libraries."""
        # Setup
        blend_file = tmp_path / "test.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        mock_library = MagicMock()
        mock_library.name = "TestLib"
        mock_library.filepath = "//test.blend"
        mock_library.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import reload_libraries

            result = reload_libraries.reload_libraries_in_file(
                blend_file_path=str(blend_file),
                dry_run=True
            )

        # Verify: Library reload was NOT called in dry run
        assert not mock_library.reload.called, "reload() should NOT be called in dry_run mode"

        # Verify: File was NOT saved in dry run
        assert not mock_bpy.ops.wm.save_mainfile.called, "File should NOT be saved in dry_run mode"

        # Verify: Result shows libraries found but not reloaded
        assert result["libraries_found"] == 1, "Should find 1 library"
        assert result["libraries_reloaded"] == 0, "Should reload 0 libraries in dry_run"

    def test_reload_all_libraries_processes_multiple_files(self, tmp_path):
        """Test that reload_all_libraries processes all .blend files in project."""
        # Setup: Create project structure
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create multiple .blend files
        blend1 = project_root / "scene1.blend"
        blend2 = project_root / "subdir" / "scene2.blend"
        blend2.parent.mkdir()

        blend1.write_bytes(b"FAKE_BLEND")
        blend2.write_bytes(b"FAKE_BLEND")

        # Mock: Each file has one library
        mock_library = MagicMock()
        mock_library.name = "LinkedLib"
        mock_library.filepath = "//linked.blend"
        mock_library.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import reload_libraries

            result = reload_libraries.reload_all_libraries(
                project_root=str(project_root),
                dry_run=False
            )

        # Verify: Both files were processed
        assert result["files_processed"] == 2, "Should process 2 .blend files"
        assert result["files_with_libraries"] == 2, "Both files have libraries"

        # Verify: open_mainfile was called twice (once per file)
        assert mock_bpy.ops.wm.open_mainfile.call_count == 2, "Should open 2 .blend files"

        # Verify: All calls used string paths
        for call in mock_bpy.ops.wm.open_mainfile.call_args_list:
            filepath_arg = call.kwargs['filepath']
            assert isinstance(filepath_arg, str), "All filepath args must be strings"

    def test_reload_all_libraries_returns_correct_structure(self, tmp_path):
        """Test that reload_all_libraries returns expected result structure."""
        # Setup: Empty project (no .blend files)
        project_root = tmp_path / "empty_project"
        project_root.mkdir()

        mock_bpy = MagicMock()

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import reload_libraries

            result = reload_libraries.reload_all_libraries(
                project_root=str(project_root),
                dry_run=True
            )

        # Verify: Result has expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "files_processed" in result, "Should have 'files_processed'"
        assert "files_with_libraries" in result, "Should have 'files_with_libraries'"
        assert "total_libraries_found" in result, "Should have 'total_libraries_found'"
        assert "total_libraries_reloaded" in result, "Should have 'total_libraries_reloaded'"
        assert "file_results" in result, "Should have 'file_results'"
        assert "errors" in result, "Should have 'errors'"
        assert "warnings" in result, "Should have 'warnings'"

        # Verify: Types
        assert isinstance(result["files_processed"], int), "'files_processed' should be int"
        assert isinstance(result["file_results"], list), "'file_results' should be list"
        assert isinstance(result["errors"], list), "'errors' should be list"
        assert isinstance(result["warnings"], list), "'warnings' should be list"
