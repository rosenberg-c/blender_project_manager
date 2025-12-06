"""Unit tests for operation planner."""

import pytest
from pathlib import Path

from core.operation_planner import (
    plan_directory_move,
    find_files_to_rebase_for_move,
    extract_moved_file_paths,
    should_rebase_path,
    MoveImpact
)


class TestPlanDirectoryMove:
    """Tests for plan_directory_move function."""

    def test_plan_simple_directory(self, tmp_path):
        """Test planning move for simple directory."""
        # Create source directory
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.blend").write_bytes(b"a" * 100)
        (source_dir / "texture.png").write_bytes(b"b" * 200)

        dest_dir = tmp_path / "dest"

        impact = plan_directory_move(source_dir, dest_dir)

        assert impact.total_files == 2
        assert impact.total_size == 300
        assert len(impact.files_to_move) == 2

    def test_plan_nested_directory(self, tmp_path):
        """Test planning move for nested directory structure."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "root.blend").write_text("test")

        subdir = source_dir / "textures"
        subdir.mkdir()
        (subdir / "wood.png").write_text("test")

        dest_dir = tmp_path / "dest"

        impact = plan_directory_move(source_dir, dest_dir)

        assert impact.total_files == 2
        assert len(impact.blend_files_affected) == 1

    def test_plan_empty_directory(self, tmp_path):
        """Test planning move for empty directory."""
        source_dir = tmp_path / "empty"
        source_dir.mkdir()
        dest_dir = tmp_path / "dest"

        impact = plan_directory_move(source_dir, dest_dir)

        assert impact.total_files == 0
        assert impact.total_size == 0

    def test_plan_nonexistent_directory(self, tmp_path):
        """Test planning move for nonexistent directory."""
        source_dir = tmp_path / "nonexistent"
        dest_dir = tmp_path / "dest"

        impact = plan_directory_move(source_dir, dest_dir)

        assert impact.total_files == 0
        assert len(impact.files_to_move) == 0

    def test_ignores_non_blend_non_texture(self, tmp_path):
        """Test that non-blend/texture files are ignored."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file.blend").write_text("test")
        (source_dir / "texture.png").write_text("test")
        (source_dir / "script.py").write_text("test")
        (source_dir / "readme.txt").write_text("test")

        dest_dir = tmp_path / "dest"

        impact = plan_directory_move(source_dir, dest_dir)

        # Should only count .blend and .png files
        assert impact.total_files == 2


class TestFindFilesToRebaseForMove:
    """Tests for find_files_to_rebase_for_move function."""

    def test_find_blend_files_excluding_moved(self, sample_project_structure):
        """Test finding .blend files that need rebasing."""
        project_root = sample_project_structure

        moved_files = [
            project_root / "scenes" / "main.blend"
        ]

        files_to_rebase = find_files_to_rebase_for_move(moved_files, project_root)

        # Should find secondary.blend and props.blend, but not main.blend
        assert len(files_to_rebase) == 2
        assert all(f.suffix == ".blend" for f in files_to_rebase)
        assert not any(f.name == "main.blend" for f in files_to_rebase)

    def test_all_blend_files_moved(self, sample_project_structure):
        """Test when all .blend files are moved."""
        project_root = sample_project_structure

        # Find all blend files
        all_blend = list(project_root.rglob("*.blend"))

        files_to_rebase = find_files_to_rebase_for_move(all_blend, project_root)

        # No files need rebasing
        assert len(files_to_rebase) == 0


class TestExtractMovedFilePaths:
    """Tests for extract_moved_file_paths function."""

    def test_extract_absolute_paths(self, tmp_path):
        """Test extracting absolute paths."""
        file1 = tmp_path / "file1.blend"
        file2 = tmp_path / "file2.png"
        file1.write_text("test")
        file2.write_text("test")

        old_parent = tmp_path

        paths = extract_moved_file_paths([file1, file2], old_parent)

        assert len(paths) == 2
        assert all(Path(p).is_absolute() for p in paths)
        assert str(file1.resolve()) in paths
        assert str(file2.resolve()) in paths


class TestShouldRebasePath:
    """Tests for should_rebase_path function."""

    def test_absolute_path_not_rebased(self, tmp_path):
        """Test that absolute paths are not rebased."""
        blend_dir = tmp_path / "scenes"
        blend_dir.mkdir()

        result = should_rebase_path(
            "/absolute/path/texture.png",
            set(),
            blend_dir
        )

        assert result is False

    def test_relative_path_to_external_file(self, tmp_path):
        """Test rebasing relative path to external file."""
        blend_dir = tmp_path / "scenes"
        blend_dir.mkdir()

        # Create the referenced texture
        textures_dir = tmp_path / "textures"
        textures_dir.mkdir()
        texture = textures_dir / "wood.png"
        texture.write_text("test")

        # This texture was NOT moved
        moved_files = set()

        result = should_rebase_path(
            "//textures/wood.png",
            moved_files,
            blend_dir
        )

        # Should rebase because texture wasn't moved
        assert result is True

    def test_relative_path_to_moved_file(self, tmp_path):
        """Test not rebasing relative path to co-moved file."""
        blend_dir = tmp_path / "scenes"
        blend_dir.mkdir()

        # Create the referenced texture
        textures_dir = blend_dir / "textures"
        textures_dir.mkdir()
        texture = textures_dir / "wood.png"
        texture.write_text("test")

        # This texture WAS moved (same parent dir)
        moved_files = {str(texture.resolve())}

        result = should_rebase_path(
            "//textures/wood.png",
            moved_files,
            blend_dir
        )

        # Should NOT rebase because texture was also moved
        assert result is False

    def test_parent_directory_reference(self, tmp_path):
        """Test with parent directory references."""
        blend_dir = tmp_path / "scenes" / "interior"
        blend_dir.mkdir(parents=True)

        # Create referenced texture
        textures_dir = tmp_path / "textures"
        textures_dir.mkdir()
        texture = textures_dir / "wood.png"
        texture.write_text("test")

        moved_files = set()

        result = should_rebase_path(
            "//../../textures/wood.png",
            moved_files,
            blend_dir
        )

        assert result is True
