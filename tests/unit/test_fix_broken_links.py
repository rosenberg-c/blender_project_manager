"""Unit tests for fix_broken_links Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestFixBrokenLinksPathHandling:
    """Tests for proper Path object handling in fix_broken_links.py."""

    def test_fix_broken_links_converts_paths_to_strings(self, tmp_path):
        """Test that Path objects are converted to strings when opening .blend files.

        Ensures we don't pass PosixPath objects to bpy.ops.wm.open_mainfile.filepath.
        """
        # Setup: Create project structure
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock bpy with no broken links
        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.images = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []

        # Import and patch
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import fix_broken_links

            # Call the function
            result = fix_broken_links.fix_broken_links_in_file(blend_file, [])

        # Verify: open_mainfile was called with STRING arguments, not Path objects
        assert mock_bpy.ops.wm.open_mainfile.called
        call_kwargs = mock_bpy.ops.wm.open_mainfile.call_args.kwargs
        assert 'filepath' in call_kwargs
        assert isinstance(call_kwargs['filepath'], str), (
            f"filepath must be a string, got {type(call_kwargs['filepath']).__name__}"
        )


class TestFixBrokenLinksRemoval:
    """Tests for removing broken links."""

    def test_removes_broken_library(self, tmp_path):
        """Test that broken library and its objects/collections are removed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock broken library
        mock_library = MagicMock()
        mock_library.name = "missing.blend"
        mock_library.filepath = "//missing.blend"

        # Mock linked objects
        mock_obj1 = MagicMock()
        mock_obj1.name = "LinkedCube"
        mock_obj1.library = mock_library

        mock_obj2 = MagicMock()
        mock_obj2.name = "LinkedSphere"
        mock_obj2.library = mock_library

        # Mock linked collections
        mock_col = MagicMock()
        mock_col.name = "LinkedCollection"
        mock_col.library = mock_library

        # Track what was removed
        removed_objects = []
        removed_collections = []

        # Create mock collections with remove methods
        mock_objects = MagicMock()
        mock_objects.__iter__ = lambda self: iter([mock_obj1, mock_obj2])
        mock_objects.remove = lambda obj: removed_objects.append(obj)

        mock_collections = MagicMock()
        mock_collections.__iter__ = lambda self: iter([mock_col])
        mock_collections.remove = lambda col: removed_collections.append(col)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = mock_objects
        mock_bpy.data.collections = mock_collections
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: str(project_root / "missing.blend")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('fix_broken_links.os.path.exists', return_value=False):
                import fix_broken_links

                links_to_fix = [{
                    "type": "Library",
                    "name": "missing.blend",
                    "path": str(project_root / "missing.blend")
                }]

                result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify library was fixed
        assert result["fixed_libraries"] == 1
        assert result["total_fixed"] == 1

        # Verify objects and collections were removed
        assert len(removed_objects) == 2
        assert mock_obj1 in removed_objects
        assert mock_obj2 in removed_objects
        assert len(removed_collections) == 1
        assert mock_col in removed_collections

        # Verify file was saved
        assert mock_bpy.ops.wm.save_mainfile.called

    def test_removes_broken_texture(self, tmp_path):
        """Test that broken texture is removed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock broken texture
        mock_image = MagicMock()
        mock_image.name = "missing.png"
        mock_image.filepath = "//textures/missing.png"
        mock_image.packed_file = None

        # Track what was removed
        removed_images = []

        # Create mock images with remove method
        mock_images = MagicMock()
        mock_images.__iter__ = lambda self: iter([mock_image])
        mock_images.remove = lambda img: removed_images.append(img)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = mock_images
        mock_bpy.path.abspath = lambda p: str(project_root / "textures" / "missing.png")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('fix_broken_links.os.path.exists', return_value=False):
                import fix_broken_links

                links_to_fix = [{
                    "type": "Texture",
                    "name": "missing.png",
                    "path": str(project_root / "textures" / "missing.png")
                }]

                result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify texture was fixed
        assert result["fixed_textures"] == 1
        assert result["total_fixed"] == 1

        # Verify image was removed
        assert len(removed_images) == 1
        assert mock_image in removed_images

        # Verify file was saved
        assert mock_bpy.ops.wm.save_mainfile.called

    def test_skips_packed_textures(self, tmp_path):
        """Test that packed textures are not removed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock packed image
        mock_image = MagicMock()
        mock_image.name = "packed.png"
        mock_image.filepath = "//textures/packed.png"
        mock_image.packed_file = MagicMock()  # Has packed file

        removed_images = []

        # Create mock images with remove method
        mock_images = MagicMock()
        mock_images.__iter__ = lambda self: iter([mock_image])
        mock_images.remove = lambda img: removed_images.append(img)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = mock_images

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import fix_broken_links

            links_to_fix = [{
                "type": "Texture",
                "name": "packed.png",
                "path": str(project_root / "textures" / "packed.png")
            }]

            result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify packed texture was not removed
        assert result["fixed_textures"] == 0
        assert result["total_fixed"] == 0
        assert len(removed_images) == 0
        assert not mock_bpy.ops.wm.save_mainfile.called

    def test_handles_empty_filepath(self, tmp_path):
        """Test that images with empty filepath are skipped."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock image with empty filepath
        mock_image = MagicMock()
        mock_image.name = "generated.png"
        mock_image.filepath = ""
        mock_image.packed_file = None

        removed_images = []

        # Create mock images with remove method
        mock_images = MagicMock()
        mock_images.__iter__ = lambda self: iter([mock_image])
        mock_images.remove = lambda img: removed_images.append(img)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = mock_images

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import fix_broken_links

            links_to_fix = [{
                "type": "Texture",
                "name": "generated.png",
                "path": ""
            }]

            result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify image with empty filepath was skipped
        assert result["fixed_textures"] == 0
        assert len(removed_images) == 0

    def test_no_save_if_nothing_fixed(self, tmp_path):
        """Test that file is not saved if no links were fixed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import fix_broken_links

            links_to_fix = [{
                "type": "Library",
                "name": "nonexistent.blend",
                "path": str(project_root / "nonexistent.blend")
            }]

            result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify nothing was fixed and file was not saved
        assert result["total_fixed"] == 0
        assert not mock_bpy.ops.wm.save_mainfile.called

    def test_fixes_multiple_broken_links(self, tmp_path):
        """Test fixing multiple broken links in one file."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock broken library
        mock_library = MagicMock()
        mock_library.name = "missing_lib.blend"
        mock_library.filepath = "//missing_lib.blend"

        mock_obj = MagicMock()
        mock_obj.library = mock_library

        # Mock broken texture
        mock_image = MagicMock()
        mock_image.name = "missing_tex.png"
        mock_image.filepath = "//missing_tex.png"
        mock_image.packed_file = None

        removed_objects = []
        removed_images = []

        # Create mock collections with remove methods
        mock_objects = MagicMock()
        mock_objects.__iter__ = lambda self: iter([mock_obj])
        mock_objects.remove = lambda obj: removed_objects.append(obj)

        mock_images = MagicMock()
        mock_images.__iter__ = lambda self: iter([mock_image])
        mock_images.remove = lambda img: removed_images.append(img)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = mock_objects
        mock_bpy.data.collections = []
        mock_bpy.data.images = mock_images
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('fix_broken_links.os.path.exists', return_value=False):
                import fix_broken_links

                links_to_fix = [
                    {
                        "type": "Library",
                        "name": "missing_lib.blend",
                        "path": str(project_root / "missing_lib.blend")
                    },
                    {
                        "type": "Texture",
                        "name": "missing_tex.png",
                        "path": str(project_root / "missing_tex.png")
                    }
                ]

                result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify both were fixed
        assert result["fixed_libraries"] == 1
        assert result["fixed_textures"] == 1
        assert result["total_fixed"] == 2
        assert len(removed_objects) == 1
        assert len(removed_images) == 1
        assert mock_bpy.ops.wm.save_mainfile.called

    def test_does_not_remove_valid_links(self, tmp_path):
        """Test that valid (non-broken) links are not removed."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Create valid library file
        lib_file = project_root / "library.blend"
        lib_file.write_bytes(b"FAKE_BLEND")

        # Mock valid library
        mock_library = MagicMock()
        mock_library.name = "library.blend"
        mock_library.filepath = "//library.blend"

        mock_obj = MagicMock()
        mock_obj.library = mock_library

        removed_objects = []

        # Create mock objects with remove method
        mock_objects = MagicMock()
        mock_objects.__iter__ = lambda self: iter([mock_obj])
        mock_objects.remove = lambda obj: removed_objects.append(obj)

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = mock_objects
        mock_bpy.data.collections = []
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: str(lib_file)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('fix_broken_links.os.path.exists', return_value=True):
                import fix_broken_links

                links_to_fix = [{
                    "type": "Library",
                    "name": "library.blend",
                    "path": str(lib_file)
                }]

                result = fix_broken_links.fix_broken_links_in_file(blend_file, links_to_fix)

        # Verify valid link was NOT removed
        assert result["fixed_libraries"] == 0
        assert result["total_fixed"] == 0
        assert len(removed_objects) == 0


class TestFixBrokenLinksResultStructure:
    """Tests for the result dictionary structure."""

    def test_result_contains_all_fields(self, tmp_path):
        """Test that result dictionary contains all expected fields."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import fix_broken_links
            result = fix_broken_links.fix_broken_links_in_file(blend_file, [])

        # Verify result structure
        assert "file" in result
        assert "file_name" in result
        assert "fixed_libraries" in result
        assert "fixed_textures" in result
        assert "total_fixed" in result
        assert "errors" in result
        assert isinstance(result["fixed_libraries"], int)
        assert isinstance(result["fixed_textures"], int)
        assert isinstance(result["total_fixed"], int)
        assert isinstance(result["errors"], list)
