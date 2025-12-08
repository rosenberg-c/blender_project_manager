"""Unit tests for find_and_relink Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest
import json


class TestSimilarityRatio:
    """Tests for the similarity_ratio function."""

    def test_identical_strings(self):
        """Test that identical strings have 100% similarity."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy before importing
        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import similarity_ratio

            result = similarity_ratio("texture.png", "texture.png")
            assert result == 1.0

    def test_similar_strings(self):
        """Test that similar strings have high similarity."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import similarity_ratio

            result = similarity_ratio("wood.jpg", "wooden.jpg")
            assert result > 0.6  # Should be fairly similar

    def test_different_strings(self):
        """Test that different strings have low similarity."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import similarity_ratio

            result = similarity_ratio("abc", "xyz")
            assert result < 0.3  # Should be very different

    def test_case_insensitive(self):
        """Test that similarity is case-insensitive."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import similarity_ratio

            result1 = similarity_ratio("Texture.PNG", "texture.png")
            result2 = similarity_ratio("texture.png", "texture.png")
            assert result1 == result2


class TestFindMissingFileInProject:
    """Tests for finding exact file matches."""

    def test_finds_exact_match(self, tmp_path):
        """Test that exact filename matches are found."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        target_file = textures_dir / "wood.png"
        target_file.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_missing_file_in_project

            matches = find_missing_file_in_project("wood.png", project_root)

            assert len(matches) == 1
            assert matches[0] == target_file

    def test_finds_multiple_matches(self, tmp_path):
        """Test that multiple files with same name are all found."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        dir1 = project_root / "dir1"
        dir1.mkdir()
        dir2 = project_root / "dir2"
        dir2.mkdir()

        file1 = dir1 / "texture.png"
        file2 = dir2 / "texture.png"
        file1.write_bytes(b"FAKE_PNG")
        file2.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_missing_file_in_project

            matches = find_missing_file_in_project("texture.png", project_root)

            assert len(matches) == 2
            assert file1 in matches
            assert file2 in matches

    def test_no_match_found(self, tmp_path):
        """Test that empty list is returned when no match found."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_missing_file_in_project

            matches = find_missing_file_in_project("missing.png", project_root)

            assert len(matches) == 0


class TestFindSimilarFilesInProject:
    """Tests for finding similar file matches."""

    def test_finds_similar_files(self, tmp_path):
        """Test that files with similar names are found."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        similar_file = textures_dir / "wooden_texture.png"
        similar_file.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_similar_files_in_project

            matches = find_similar_files_in_project("wood_texture.png", project_root, min_similarity=0.6)

            assert len(matches) > 0
            # Check that first match is the similar file with a similarity ratio
            file_path, ratio = matches[0]
            assert file_path == similar_file
            assert 0.6 <= ratio < 1.0

    def test_respects_min_similarity(self, tmp_path):
        """Test that files below minimum similarity are excluded."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        # Create files with different similarity levels
        similar_file = textures_dir / "wood.png"
        dissimilar_file = textures_dir / "completely_different.png"
        similar_file.write_bytes(b"FAKE_PNG")
        dissimilar_file.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_similar_files_in_project

            matches = find_similar_files_in_project("wooden.png", project_root, min_similarity=0.6)

            # Similar file should be found, dissimilar should not
            found_files = [path for path, ratio in matches]
            assert similar_file in found_files
            assert dissimilar_file not in found_files

    def test_filters_by_extension(self, tmp_path):
        """Test that only files with same extension are considered."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        png_file = textures_dir / "wood.png"
        jpg_file = textures_dir / "wood.jpg"
        png_file.write_bytes(b"FAKE_PNG")
        jpg_file.write_bytes(b"FAKE_JPG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_similar_files_in_project

            matches = find_similar_files_in_project("wooden.png", project_root, min_similarity=0.6)

            # Only PNG file should be found
            found_files = [path for path, ratio in matches]
            assert png_file in found_files
            assert jpg_file not in found_files

    def test_returns_top_5_matches(self, tmp_path):
        """Test that only top 5 matches are returned."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        # Create 10 files with varying similarity
        for i in range(10):
            file = textures_dir / f"wood{i}.png"
            file.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_similar_files_in_project

            matches = find_similar_files_in_project("wood.png", project_root, min_similarity=0.6)

            # Should return at most 5 matches
            assert len(matches) <= 5

    def test_sorted_by_similarity_descending(self, tmp_path):
        """Test that matches are sorted by similarity (highest first)."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        textures_dir = project_root / "textures"
        textures_dir.mkdir()

        # Create files with different similarity levels
        for name in ["wood.png", "wooden.png", "woods.png"]:
            file = textures_dir / name
            file.write_bytes(b"FAKE_PNG")

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import find_similar_files_in_project

            matches = find_similar_files_in_project("wood.png", project_root, min_similarity=0.6)

            # Check that similarity ratios are in descending order
            ratios = [ratio for path, ratio in matches]
            assert ratios == sorted(ratios, reverse=True)


class TestRelinkBrokenLinks:
    """Tests for relinking broken links."""

    def test_relinks_library_by_name(self, tmp_path):
        """Test that library is matched by name and relinked."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        new_lib_file = project_root / "library.blend"
        new_lib_file.write_bytes(b"FAKE_BLEND")

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "library.blend"
        mock_library.filepath = "//old_path/library.blend"
        mock_library.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))
        mock_bpy.path.relpath = lambda p: f"//{Path(p).relative_to(project_root)}"

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import relink_broken_links_in_file

            links_to_relink = [{
                "type": "Library",
                "name": "library.blend",
                "new_path": str(new_lib_file)
            }]

            result = relink_broken_links_in_file(blend_file, links_to_relink)

        # Verify library was relinked
        assert result["relinked_libraries"] == 1
        assert result["total_relinked"] == 1
        assert mock_library.reload.called
        assert mock_bpy.ops.wm.save_mainfile.called

    def test_relinks_texture_by_name(self, tmp_path):
        """Test that texture is matched by name and relinked."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        new_texture_file = project_root / "wood.png"
        new_texture_file.write_bytes(b"FAKE_PNG")

        # Mock image
        mock_image = MagicMock()
        mock_image.name = "wood.png"
        mock_image.filepath = "//old_path/wood.png"
        mock_image.packed_file = None
        mock_image.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.images = [mock_image]
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))
        mock_bpy.path.relpath = lambda p: f"//{Path(p).relative_to(project_root)}"

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import relink_broken_links_in_file

            links_to_relink = [{
                "type": "Texture",
                "name": "wood.png",
                "new_path": str(new_texture_file)
            }]

            result = relink_broken_links_in_file(blend_file, links_to_relink)

        # Verify texture was relinked
        assert result["relinked_textures"] == 1
        assert result["total_relinked"] == 1
        assert mock_image.reload.called
        assert mock_bpy.ops.wm.save_mainfile.called

    def test_uses_relative_paths(self, tmp_path):
        """Test that relative paths (with //) are used when relinking."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        new_lib_file = project_root / "library.blend"
        new_lib_file.write_bytes(b"FAKE_BLEND")

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "library.blend"
        mock_library.filepath = "//old_path/library.blend"
        mock_library.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.images = []
        mock_bpy.path.abspath = lambda p: str(project_root / p.replace("//", ""))
        mock_bpy.path.relpath = lambda p: f"//library.blend"  # Simulate relative path conversion

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import relink_broken_links_in_file

            links_to_relink = [{
                "type": "Library",
                "name": "library.blend",
                "new_path": str(new_lib_file)
            }]

            result = relink_broken_links_in_file(blend_file, links_to_relink)

        # Verify relative path was used
        assert mock_library.filepath.startswith("//")

    def test_skips_packed_textures(self, tmp_path):
        """Test that packed textures are skipped during relink."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        # Mock packed image
        mock_image = MagicMock()
        mock_image.name = "packed.png"
        mock_image.packed_file = MagicMock()  # Has packed file
        mock_image.reload = MagicMock()

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.images = [mock_image]

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import relink_broken_links_in_file

            links_to_relink = [{
                "type": "Texture",
                "name": "packed.png",
                "new_path": str(project_root / "packed.png")
            }]

            result = relink_broken_links_in_file(blend_file, links_to_relink)

        # Verify packed texture was skipped
        assert result["relinked_textures"] == 0
        assert result["total_relinked"] == 0
        assert not mock_image.reload.called

    def test_no_save_if_nothing_relinked(self, tmp_path):
        """Test that file is not saved if no links were relinked."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.ops.wm.save_mainfile = MagicMock()
        mock_bpy.data.libraries = []
        mock_bpy.data.images = []

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from find_and_relink import relink_broken_links_in_file

            links_to_relink = [{
                "type": "Library",
                "name": "nonexistent.blend",
                "new_path": str(project_root / "nonexistent.blend")
            }]

            result = relink_broken_links_in_file(blend_file, links_to_relink)

        # Verify file was not saved
        assert result["total_relinked"] == 0
        assert not mock_bpy.ops.wm.save_mainfile.called
