"""Unit tests for path utilities."""

import pytest
from pathlib import Path

from core.path_utils import (
    rebase_relative_path,
    resolve_blender_path,
    make_blender_relative,
    is_blender_path_relative,
    normalize_path_separators,
    get_path_depth
)


class TestRebaseRelativePath:
    """Tests for rebase_relative_path function."""

    def test_rebase_simple_relative_path(self):
        """Test rebasing a simple relative path."""
        old_dir = Path("/project/scenes")
        new_dir = Path("/project/exported/scenes")
        original = "//../../textures/wood.jpg"

        result = rebase_relative_path(original, old_dir, new_dir)

        # From /project/scenes, ../../textures is /textures
        # From /project/exported/scenes, ../../../textures is /textures
        assert result == "//../../../textures/wood.jpg"

    def test_rebase_same_level_move(self):
        """Test rebasing when moving to same directory level."""
        old_dir = Path("/project/scenes")
        new_dir = Path("/project/assets")
        original = "//textures/wood.jpg"

        result = rebase_relative_path(original, old_dir, new_dir)

        # Both are at same level, but different dirs
        assert result.startswith("//")
        assert "wood.jpg" in result

    def test_rebase_absolute_path_unchanged(self):
        """Test that absolute paths are not rebased."""
        old_dir = Path("/project/scenes")
        new_dir = Path("/project/exported")
        original = "/absolute/path/to/texture.jpg"

        result = rebase_relative_path(original, old_dir, new_dir)

        assert result == original

    def test_rebase_empty_relative_part(self):
        """Test rebasing path with empty relative part."""
        old_dir = Path("/project/scenes")
        new_dir = Path("/project/scenes/subfolder")
        original = "//"  # Just the prefix

        result = rebase_relative_path(original, old_dir, new_dir)

        assert result.startswith("//")

    def test_rebase_with_backslashes(self):
        """Test rebasing path with Windows-style backslashes."""
        old_dir = Path("/project/scenes")
        new_dir = Path("/project/exported")
        original = "//..\\textures\\wood.jpg"

        result = rebase_relative_path(original, old_dir, new_dir)

        # Should normalize to forward slashes
        assert "\\" not in result
        assert "/" in result
        assert result.startswith("//")

    def test_rebase_deep_nesting(self):
        """Test rebasing with deeply nested paths."""
        old_dir = Path("/a/b/c/d")
        new_dir = Path("/a/b")
        original = "//../../../textures/wood.jpg"

        result = rebase_relative_path(original, old_dir, new_dir)

        assert result.startswith("//")


class TestResolveBlenderPath:
    """Tests for resolve_blender_path function."""

    def test_resolve_relative_path(self):
        """Test resolving a Blender relative path."""
        blend_dir = Path("/project/scenes")
        blender_path = "//textures/wood.jpg"

        result = resolve_blender_path(blender_path, blend_dir)

        assert result == Path("/project/scenes/textures/wood.jpg")

    def test_resolve_absolute_path(self):
        """Test resolving an absolute path."""
        blend_dir = Path("/project/scenes")
        blender_path = "/absolute/path/to/texture.jpg"

        result = resolve_blender_path(blender_path, blend_dir)

        assert result == Path("/absolute/path/to/texture.jpg")

    def test_resolve_parent_directory_reference(self):
        """Test resolving path with parent directory references."""
        blend_dir = Path("/project/scenes/interior")
        blender_path = "//../../textures/wood.jpg"

        result = resolve_blender_path(blender_path, blend_dir)

        # Should normalize the path
        assert "textures/wood.jpg" in str(result)


class TestMakeBlenderRelative:
    """Tests for make_blender_relative function."""

    def test_make_relative_simple(self):
        """Test converting absolute to relative path."""
        abs_path = Path("/project/textures/wood.jpg")
        blend_dir = Path("/project/scenes")

        result = make_blender_relative(abs_path, blend_dir)

        assert result.startswith("//")
        assert "wood.jpg" in result

    def test_make_relative_same_directory(self):
        """Test converting path in same directory."""
        abs_path = Path("/project/scenes/texture.jpg")
        blend_dir = Path("/project/scenes")

        result = make_blender_relative(abs_path, blend_dir)

        assert result == "//texture.jpg"

    def test_make_relative_parent_directory(self):
        """Test converting path in parent directory."""
        abs_path = Path("/project/texture.jpg")
        blend_dir = Path("/project/scenes/interior")

        result = make_blender_relative(abs_path, blend_dir)

        assert result.startswith("//")
        assert ".." in result


class TestIsBlenderPathRelative:
    """Tests for is_blender_path_relative function."""

    def test_relative_path(self):
        """Test identifying relative path."""
        assert is_blender_path_relative("//textures/wood.jpg") is True

    def test_absolute_path(self):
        """Test identifying absolute path."""
        assert is_blender_path_relative("/absolute/path/texture.jpg") is False

    def test_empty_path(self):
        """Test empty path."""
        assert is_blender_path_relative("") is False

    def test_just_slashes(self):
        """Test path with just slashes."""
        assert is_blender_path_relative("//") is True


class TestNormalizePathSeparators:
    """Tests for normalize_path_separators function."""

    def test_normalize_backslashes(self):
        """Test normalizing Windows backslashes."""
        path = "textures\\wood\\oak.jpg"
        result = normalize_path_separators(path)
        assert result == "textures/wood/oak.jpg"

    def test_normalize_mixed_separators(self):
        """Test normalizing mixed separators."""
        path = "textures/wood\\oak.jpg"
        result = normalize_path_separators(path)
        assert result == "textures/wood/oak.jpg"

    def test_normalize_already_normalized(self):
        """Test path already using forward slashes."""
        path = "textures/wood/oak.jpg"
        result = normalize_path_separators(path)
        assert result == "textures/wood/oak.jpg"


class TestGetPathDepth:
    """Tests for get_path_depth function."""

    def test_single_file(self):
        """Test depth of single file (no directories)."""
        assert get_path_depth("file.jpg") == 0
        assert get_path_depth("//file.jpg") == 0

    def test_one_level_deep(self):
        """Test depth of one directory level."""
        assert get_path_depth("textures/wood.jpg") == 1
        assert get_path_depth("//textures/wood.jpg") == 1

    def test_multiple_levels(self):
        """Test depth of multiple directory levels."""
        assert get_path_depth("assets/textures/wood/oak.jpg") == 3
        assert get_path_depth("//assets/textures/wood/oak.jpg") == 3

    def test_parent_references(self):
        """Test depth with parent directory references."""
        assert get_path_depth("../textures/wood.jpg") == 2
        assert get_path_depth("//../textures/wood.jpg") == 2
