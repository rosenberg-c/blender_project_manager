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


class TestFindTexturereferences:
    """Tests for finding references to texture files."""

    def test_find_texture_references_identifies_usage(self, tmp_path):
        """Test that files using a texture are identified."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_texture = project_root / "textures" / "wood.png"
        target_texture.parent.mkdir()
        target_texture.write_bytes(b"FAKE_IMAGE")

        scene_file = project_root / "scene.blend"
        scene_file.write_bytes(b"FAKE_BLEND")

        # Mock image that uses the texture
        mock_image = MagicMock()
        mock_image.name = "WoodTexture"
        mock_image.filepath = str(target_texture)
        mock_image.size = [2048, 2048]

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: str(target_texture)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_texture(
                target_file=str(target_texture),
                project_root=str(project_root)
            )

        # Verify: scene.blend should be in referencing_files
        referencing_files = result.get("referencing_files", [])
        assert len(referencing_files) == 1, "Should find 1 file using the texture"
        assert "scene.blend" in referencing_files[0]["file_name"]
        assert referencing_files[0]["images_count"] == 1

    def test_is_texture_file_identifies_textures(self):
        """Test that texture files are correctly identified."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy before importing
        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            # Should identify as textures
            assert find_references.is_texture_file("texture.png") is True
            assert find_references.is_texture_file("image.jpg") is True
            assert find_references.is_texture_file("map.exr") is True
            assert find_references.is_texture_file("hdri.hdr") is True
            assert find_references.is_texture_file("normal.tiff") is True

            # Should not identify as textures
            assert find_references.is_texture_file("model.blend") is False
            assert find_references.is_texture_file("script.py") is False
            assert find_references.is_texture_file("data.json") is False

    def test_find_references_routes_to_correct_function(self, tmp_path):
        """Test that find_references_to_file routes to the correct function based on file type."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Test texture file
        texture_file = project_root / "texture.png"
        texture_file.write_bytes(b"FAKE_IMAGE")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.images = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_file(
                target_file=str(texture_file),
                project_root=str(project_root)
            )

        # Verify: Should route to texture function
        assert result.get("file_type") == "texture"

    def test_texture_skip_generated_images(self, tmp_path):
        """Test that generated/packed images without filepath are skipped."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        target_texture = project_root / "texture.png"
        target_texture.write_bytes(b"FAKE_IMAGE")

        scene_file = project_root / "scene.blend"
        scene_file.write_bytes(b"FAKE_BLEND")

        # Mock image without filepath (generated image)
        mock_generated = MagicMock()
        mock_generated.name = "GeneratedImage"
        mock_generated.filepath = ""  # No filepath

        # Mock image with filepath
        mock_real = MagicMock()
        mock_real.name = "RealTexture"
        mock_real.filepath = str(target_texture)
        mock_real.size = [1024, 1024]

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.images = [mock_generated, mock_real]
        mock_bpy.path.abspath = lambda p: str(target_texture) if p else ""

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import find_references

            result = find_references.find_references_to_texture(
                target_file=str(target_texture),
                project_root=str(project_root)
            )

        # Verify: Only the real texture should be counted, not generated
        referencing_files = result.get("referencing_files", [])
        assert len(referencing_files) == 1
        assert referencing_files[0]["images_count"] == 1
        images = referencing_files[0]["images"]
        assert len(images) == 1
        assert images[0]["name"] == "RealTexture"
