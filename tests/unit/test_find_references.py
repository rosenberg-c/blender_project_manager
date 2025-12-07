"""Unit tests for find_references Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestFindReferencesPathHandling:
    """Tests for proper Path object handling in find_references.py."""

    def test_find_references_converts_paths_to_strings(self, tmp_path):
        """Test that Path objects are converted to strings when opening .blend files.

        Ensures we don't pass PosixPath objects to bpy.ops.wm.open_mainfile.filepath.
        """
        # Setup: Create project structure
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create target file and referencing file
        target_file = project_root / "library.blend"
        ref_file = project_root / "scene.blend"

        target_file.write_bytes(b"FAKE_BLEND")
        ref_file.write_bytes(b"FAKE_BLEND")

        # Mock library that references the target
        mock_library = MagicMock()
        mock_library.name = "Library"
        mock_library.filepath = str(target_file)
        mock_library.filepath_resolved = str(target_file)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.path.abspath = lambda p: str(target_file)

        # Import and patch
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            # Call the function
            result = find_references.find_references_to_file(
                target_file=str(target_file),
                project_root=str(project_root)
            )

        # Verify: open_mainfile was called with STRING arguments, not Path objects
        if mock_bpy.ops.wm.open_mainfile.called:
            for call in mock_bpy.ops.wm.open_mainfile.call_args_list:
                kwargs = call.kwargs
                if 'filepath' in kwargs:
                    filepath_arg = kwargs['filepath']
                    assert isinstance(filepath_arg, str), (
                        f"filepath must be a string, got {type(filepath_arg).__name__}. "
                        f"This causes: 'WM_OT_open_mainfile.filepath expected a string type, not PosixPath'"
                    )


class TestFindReferencesLogic:
    """Tests for find_references core functionality."""

    def test_find_references_identifies_referencing_files(self, tmp_path):
        """Test that files linking to target are identified."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_file = project_root / "library.blend"
        ref_file1 = project_root / "scene1.blend"
        ref_file2 = project_root / "scene2.blend"

        target_file.write_bytes(b"FAKE_BLEND")
        ref_file1.write_bytes(b"FAKE_BLEND")
        ref_file2.write_bytes(b"FAKE_BLEND")

        # Mock: scene1 references target, scene2 doesn't
        def mock_open_mainfile(filepath):
            if "scene1" in filepath:
                # This file has a library link to target
                mock_lib = MagicMock()
                mock_lib.name = "LibraryLink"
                mock_lib.filepath = str(target_file)
                mock_bpy.data.libraries = [mock_lib]
            else:
                # This file has no libraries
                mock_bpy.data.libraries = []

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock(side_effect=mock_open_mainfile)
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.path.abspath = lambda p: str(target_file)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_file(
                target_file=str(target_file),
                project_root=str(project_root)
            )

        # Verify: scene1.blend should be in referencing_files
        referencing_files = result.get("referencing_files", [])
        assert len(referencing_files) == 1, "Should find 1 referencing file"
        assert "scene1.blend" in referencing_files[0]["file_name"]

    def test_find_references_excludes_target_file(self, tmp_path):
        """Test that the target file doesn't appear in its own references."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_file = project_root / "library.blend"
        target_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_file(
                target_file=str(target_file),
                project_root=str(project_root)
            )

        # Verify: Target file was not scanned (can't reference itself)
        assert result["files_scanned"] == 0, "Target file should not be scanned"

    def test_find_references_returns_correct_structure(self, tmp_path):
        """Test that the result has the expected structure."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_file = project_root / "library.blend"
        target_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_file(
                target_file=str(target_file),
                project_root=str(project_root)
            )

        # Verify: Result has expected structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "target_file" in result
        assert "target_name" in result
        assert "referencing_files" in result
        assert "files_scanned" in result
        assert "errors" in result
        assert "warnings" in result

        # Verify: Types
        assert isinstance(result["referencing_files"], list)
        assert isinstance(result["files_scanned"], int)
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)

    def test_find_references_counts_linked_items(self, tmp_path):
        """Test that linked objects and collections are counted."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_file = project_root / "library.blend"
        ref_file = project_root / "scene.blend"

        target_file.write_bytes(b"FAKE_BLEND")
        ref_file.write_bytes(b"FAKE_BLEND")

        # Mock library with linked objects and collections
        mock_library = MagicMock()
        mock_library.name = "Library"
        mock_library.filepath = str(target_file)

        # Mock linked objects
        mock_obj1 = MagicMock()
        mock_obj1.name = "LinkedCube"
        mock_obj1.library = mock_library

        mock_obj2 = MagicMock()
        mock_obj2.name = "LinkedSphere"
        mock_obj2.library = mock_library

        # Mock linked collection
        mock_col = MagicMock()
        mock_col.name = "LinkedCollection"
        mock_col.library = mock_library

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = [mock_obj1, mock_obj2]
        mock_bpy.data.collections = [mock_col]
        mock_bpy.path.abspath = lambda p: str(target_file)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_file(
                target_file=str(target_file),
                project_root=str(project_root)
            )

        # Verify: Linked items are counted
        assert len(result["referencing_files"]) == 1
        ref_info = result["referencing_files"][0]
        assert ref_info["linked_objects_count"] == 2, "Should count 2 linked objects"
        assert ref_info["linked_collections_count"] == 1, "Should count 1 linked collection"
        assert "LinkedCube" in ref_info["linked_objects"]
        assert "LinkedSphere" in ref_info["linked_objects"]
        assert "LinkedCollection" in ref_info["linked_collections"]
