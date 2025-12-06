"""Unit tests for file scanner."""

import pytest
from pathlib import Path

from core.file_scanner import (
    find_blend_files,
    find_texture_files,
    find_backup_files,
    get_file_type,
    is_texture_file,
    is_blend_file,
    calculate_directory_size,
    TEXTURE_EXTENSIONS,
    BLEND_EXTENSIONS
)


class TestFindBlendFiles:
    """Tests for find_blend_files function."""

    def test_find_in_single_directory(self, tmp_path):
        """Test finding .blend files in single directory."""
        # Create test files
        (tmp_path / "test1.blend").write_text("test")
        (tmp_path / "test2.blend").write_text("test")
        (tmp_path / "texture.png").write_text("test")

        result = find_blend_files(tmp_path, recursive=False)

        assert len(result) == 2
        assert all(f.suffix == ".blend" for f in result)

    def test_find_recursive(self, tmp_path):
        """Test finding .blend files recursively."""
        # Create nested structure
        (tmp_path / "root.blend").write_text("test")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.blend").write_text("test")

        result = find_blend_files(tmp_path, recursive=True)

        assert len(result) == 2
        assert any(f.name == "root.blend" for f in result)
        assert any(f.name == "nested.blend" for f in result)

    def test_ignore_hidden_files(self, tmp_path):
        """Test that hidden files are ignored."""
        (tmp_path / "visible.blend").write_text("test")
        (tmp_path / ".hidden.blend").write_text("test")

        result = find_blend_files(tmp_path)

        assert len(result) == 1
        assert result[0].name == "visible.blend"

    def test_ignore_directories(self, tmp_path):
        """Test that specified directories are ignored."""
        (tmp_path / "included.blend").write_text("test")

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "ignored.blend").write_text("test")

        result = find_blend_files(tmp_path)

        assert len(result) == 1
        assert result[0].name == "included.blend"

    def test_custom_ignore_dirs(self, tmp_path):
        """Test with custom ignore directories."""
        (tmp_path / "included.blend").write_text("test")

        custom_dir = tmp_path / "custom_ignore"
        custom_dir.mkdir()
        (custom_dir / "ignored.blend").write_text("test")

        result = find_blend_files(tmp_path, ignore_dirs={"custom_ignore"})

        assert len(result) == 1
        assert result[0].name == "included.blend"

    def test_nonexistent_directory(self):
        """Test with nonexistent directory."""
        result = find_blend_files(Path("/nonexistent/path"))

        assert len(result) == 0

    def test_sorted_output(self, tmp_path):
        """Test that results are sorted."""
        (tmp_path / "c.blend").write_text("test")
        (tmp_path / "a.blend").write_text("test")
        (tmp_path / "b.blend").write_text("test")

        result = find_blend_files(tmp_path)

        names = [f.name for f in result]
        assert names == sorted(names)


class TestFindTextureFiles:
    """Tests for find_texture_files function."""

    def test_find_default_extensions(self, tmp_path):
        """Test finding textures with default extensions."""
        (tmp_path / "texture.png").write_text("test")
        (tmp_path / "image.jpg").write_text("test")
        (tmp_path / "hdr.exr").write_text("test")
        (tmp_path / "not_texture.blend").write_text("test")

        result = find_texture_files(tmp_path)

        assert len(result) == 3
        assert all(f.suffix.lower() in TEXTURE_EXTENSIONS for f in result)

    def test_find_custom_extensions(self, tmp_path):
        """Test finding files with custom extensions."""
        (tmp_path / "image.png").write_text("test")
        (tmp_path / "image.jpg").write_text("test")

        result = find_texture_files(tmp_path, extensions={".png"})

        assert len(result) == 1
        assert result[0].suffix == ".png"

    def test_case_insensitive_extensions(self, tmp_path):
        """Test that extension matching is case-insensitive."""
        (tmp_path / "image.PNG").write_text("test")
        (tmp_path / "image.Jpg").write_text("test")

        result = find_texture_files(tmp_path)

        assert len(result) == 2

    def test_recursive_search(self, tmp_path):
        """Test recursive texture search."""
        (tmp_path / "root.png").write_text("test")
        subdir = tmp_path / "textures"
        subdir.mkdir()
        (subdir / "nested.png").write_text("test")

        result = find_texture_files(tmp_path, recursive=True)

        assert len(result) == 2

    def test_non_recursive_search(self, tmp_path):
        """Test non-recursive texture search."""
        (tmp_path / "root.png").write_text("test")
        subdir = tmp_path / "textures"
        subdir.mkdir()
        (subdir / "nested.png").write_text("test")

        result = find_texture_files(tmp_path, recursive=False)

        assert len(result) == 1
        assert result[0].name == "root.png"


class TestFindBackupFiles:
    """Tests for find_backup_files function."""

    def test_find_blend1_files(self, tmp_path):
        """Test finding .blend1 backup files."""
        (tmp_path / "file.blend").write_text("test")
        (tmp_path / "file.blend1").write_text("test")
        (tmp_path / "file.blend2").write_text("test")

        result = find_backup_files(tmp_path)

        assert len(result) == 2
        assert any(f.suffix == ".blend1" for f in result)
        assert any(f.suffix == ".blend2" for f in result)
        assert not any(f.suffix == ".blend" for f in result)

    def test_find_in_subdirectories(self, tmp_path):
        """Test finding backup files in subdirectories."""
        (tmp_path / "root.blend1").write_text("test")
        subdir = tmp_path / "scenes"
        subdir.mkdir()
        (subdir / "scene.blend1").write_text("test")

        result = find_backup_files(tmp_path)

        assert len(result) == 2

    def test_ignore_directories(self, tmp_path):
        """Test that ignored directories are skipped."""
        (tmp_path / "included.blend1").write_text("test")

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "ignored.blend1").write_text("test")

        result = find_backup_files(tmp_path)

        assert len(result) == 1


class TestGetFileType:
    """Tests for get_file_type function."""

    def test_blend_file(self):
        """Test identifying .blend file."""
        assert get_file_type(Path("test.blend")) == "blend"
        assert get_file_type(Path("TEST.BLEND")) == "blend"

    def test_texture_file(self):
        """Test identifying texture files."""
        assert get_file_type(Path("texture.png")) == "texture"
        assert get_file_type(Path("image.jpg")) == "texture"
        assert get_file_type(Path("hdr.exr")) == "texture"

    def test_other_file(self):
        """Test identifying other file types."""
        assert get_file_type(Path("script.py")) == "other"
        assert get_file_type(Path("document.txt")) == "other"


class TestIsTextureFile:
    """Tests for is_texture_file function."""

    def test_valid_texture_extensions(self):
        """Test valid texture file extensions."""
        assert is_texture_file(Path("image.png")) is True
        assert is_texture_file(Path("image.jpg")) is True
        assert is_texture_file(Path("image.exr")) is True

    def test_invalid_extensions(self):
        """Test invalid file extensions."""
        assert is_texture_file(Path("file.blend")) is False
        assert is_texture_file(Path("script.py")) is False

    def test_case_insensitive(self):
        """Test case-insensitive extension checking."""
        assert is_texture_file(Path("image.PNG")) is True
        assert is_texture_file(Path("IMAGE.JPG")) is True


class TestIsBlendFile:
    """Tests for is_blend_file function."""

    def test_blend_extension(self):
        """Test .blend extension."""
        assert is_blend_file(Path("test.blend")) is True
        assert is_blend_file(Path("TEST.BLEND")) is True

    def test_other_extensions(self):
        """Test non-.blend extensions."""
        assert is_blend_file(Path("test.blend1")) is False
        assert is_blend_file(Path("image.png")) is False


class TestCalculateDirectorySize:
    """Tests for calculate_directory_size function."""

    def test_calculate_simple(self, tmp_path):
        """Test calculating directory size."""
        (tmp_path / "file1.txt").write_bytes(b"a" * 100)
        (tmp_path / "file2.txt").write_bytes(b"b" * 200)

        size = calculate_directory_size(tmp_path)

        assert size == 300

    def test_calculate_with_pattern(self, tmp_path):
        """Test calculating size with file pattern."""
        (tmp_path / "image.png").write_bytes(b"a" * 100)
        (tmp_path / "file.txt").write_bytes(b"b" * 200)

        size = calculate_directory_size(tmp_path, pattern="*.png")

        assert size == 100

    def test_recursive_calculation(self, tmp_path):
        """Test recursive size calculation."""
        (tmp_path / "file1.txt").write_bytes(b"a" * 100)
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_bytes(b"b" * 200)

        size = calculate_directory_size(tmp_path)

        assert size == 300

    def test_nonexistent_directory(self):
        """Test with nonexistent directory."""
        size = calculate_directory_size(Path("/nonexistent"))

        assert size == 0

    def test_empty_directory(self, tmp_path):
        """Test with empty directory."""
        size = calculate_directory_size(tmp_path)

        assert size == 0
