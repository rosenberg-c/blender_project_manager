"""Unit tests for check_broken_links Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestCheckBrokenLinksPathHandling:
    """Tests for proper Path object handling in check_broken_links.py."""

    def test_check_broken_links_converts_paths_to_strings(self, tmp_path):
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
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))

        # Import and patch
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import check_broken_links

            # Call the function
            result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify: open_mainfile was called with STRING arguments, not Path objects
        assert mock_bpy.ops.wm.open_mainfile.called
        call_kwargs = mock_bpy.ops.wm.open_mainfile.call_args.kwargs
        assert 'filepath' in call_kwargs
        assert isinstance(call_kwargs['filepath'], str), (
            f"filepath must be a string, got {type(call_kwargs['filepath']).__name__}"
        )


class TestCheckBrokenLinksDetection:
    """Tests for broken link detection logic."""

    def test_detects_missing_library(self, tmp_path):
        """Test that missing library files are detected."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock library that points to non-existent file
        missing_lib_path = str(project_root / "missing.blend")
        mock_library = MagicMock()
        mock_library.name = "missing.blend"
        mock_library.filepath = f"//{missing_lib_path}"

        # Mock linked objects
        mock_obj = MagicMock()
        mock_obj.name = "LinkedCube"
        mock_obj.library = mock_library

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = [mock_obj]
        mock_bpy.data.collections = []
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: missing_lib_path

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('check_broken_links.os.path.exists', return_value=False):
                import check_broken_links
                result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify broken library detected
        assert result["total_broken"] == 1
        assert len(result["broken_libraries"]) == 1
        assert result["broken_libraries"][0]["library_name"] == "missing.blend"
        assert result["broken_libraries"][0]["objects_count"] == 1

    def test_detects_missing_texture(self, tmp_path):
        """Test that missing texture files are detected."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock image that points to non-existent file
        missing_img_path = str(project_root / "missing.png")
        mock_image = MagicMock()
        mock_image.name = "missing.png"
        mock_image.filepath = f"//textures/missing.png"
        mock_image.packed_file = None
        mock_image.library = None  # Not from linked library
        mock_image.users = 3
        mock_image.size = [1024, 1024]

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: missing_img_path

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('check_broken_links.os.path.exists', return_value=False):
                import check_broken_links
                result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify broken texture detected
        assert result["total_broken"] == 1
        assert len(result["broken_textures"]) == 1
        assert result["broken_textures"][0]["image_name"] == "missing.png"
        assert result["broken_textures"][0]["users_count"] == 3

    def test_skips_packed_textures(self, tmp_path):
        """Test that packed (embedded) textures are skipped."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock packed image
        mock_image = MagicMock()
        mock_image.name = "packed.png"
        mock_image.filepath = "//textures/packed.png"
        mock_image.packed_file = MagicMock()  # Has packed file
        mock_image.library = None

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import check_broken_links
            result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify no broken links (packed image was skipped)
        assert result["total_broken"] == 0
        assert len(result["broken_textures"]) == 0

    def test_skips_textures_from_linked_libraries(self, tmp_path):
        """Test that textures from linked libraries are skipped.

        This is critical - textures from linked libraries should only be
        validated in their own library file, not from the file that links to them.
        """
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "library.blend"

        # Mock image from linked library
        mock_image = MagicMock()
        mock_image.name = "texture_from_lib.png"
        mock_image.filepath = "//textures/texture.png"
        mock_image.packed_file = None
        mock_image.library = mock_library  # From linked library!

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import check_broken_links
            result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify no broken links (library texture was skipped)
        assert result["total_broken"] == 0
        assert len(result["broken_textures"]) == 0

    def test_detects_valid_library(self, tmp_path):
        """Test that existing library files are NOT reported as broken."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Create actual library file
        lib_file = project_root / "library.blend"
        lib_file.write_bytes(b"FAKE_BLEND")

        mock_library = MagicMock()
        mock_library.name = "library.blend"
        mock_library.filepath = f"//library.blend"

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: str(lib_file)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('check_broken_links.os.path.exists', return_value=True):
                import check_broken_links
                result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify no broken links
        assert result["total_broken"] == 0
        assert len(result["broken_libraries"]) == 0

    def test_detects_valid_texture(self, tmp_path):
        """Test that existing texture files are NOT reported as broken."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Create actual texture file
        textures_dir = project_root / "textures"
        textures_dir.mkdir()
        texture_file = textures_dir / "wood.png"
        texture_file.write_bytes(b"FAKE_PNG")

        mock_image = MagicMock()
        mock_image.name = "wood.png"
        mock_image.filepath = "//textures/wood.png"
        mock_image.packed_file = None
        mock_image.library = None

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: str(texture_file)

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('check_broken_links.os.path.exists', return_value=True):
                import check_broken_links
                result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify no broken links
        assert result["total_broken"] == 0
        assert len(result["broken_textures"]) == 0

    def test_handles_empty_filepath(self, tmp_path):
        """Test that images with empty filepath are skipped."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock image with empty filepath
        mock_image = MagicMock()
        mock_image.name = "generated.png"
        mock_image.filepath = ""  # Empty filepath
        mock_image.packed_file = None
        mock_image.library = None

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            import check_broken_links
            result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify no broken links (empty filepath was skipped)
        assert result["total_broken"] == 0
        assert len(result["broken_textures"]) == 0

    def test_multiple_broken_links(self, tmp_path):
        """Test detecting multiple broken links in one file."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock broken library
        mock_library = MagicMock()
        mock_library.name = "missing_lib.blend"
        mock_library.filepath = "//missing_lib.blend"

        # Mock broken texture
        mock_image = MagicMock()
        mock_image.name = "missing_tex.png"
        mock_image.filepath = "//missing_tex.png"
        mock_image.packed_file = None
        mock_image.library = None
        mock_image.users = 1
        mock_image.size = [512, 512]

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('check_broken_links.os.path.exists', return_value=False):
                import check_broken_links
                result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify both broken links detected
        assert result["total_broken"] == 2
        assert len(result["broken_libraries"]) == 1
        assert len(result["broken_textures"]) == 1


class TestCheckBrokenLinksResultStructure:
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
            import check_broken_links
            result = check_broken_links.check_broken_links_in_file(blend_file)

        # Verify result structure
        assert "file" in result
        assert "file_name" in result
        assert "broken_libraries" in result
        assert "broken_textures" in result
        assert "total_broken" in result
        assert isinstance(result["broken_libraries"], list)
        assert isinstance(result["broken_textures"], list)
        assert isinstance(result["total_broken"], int)
