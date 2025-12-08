"""Unit tests for path_operations module."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestPathRebaserRebasePath:
    """Tests for PathRebaser.rebase_relative_path static method."""

    def test_rebase_relative_path_delegates_to_core(self):
        """Test that rebase_relative_path delegates to core.path_utils."""
        # Mock bpy first
        mock_bpy = MagicMock()

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            with patch('blender_lib.path_operations.rebase_relative_path') as mock_rebase:
                mock_rebase.return_value = "//new/path.png"

                result = PathRebaser.rebase_relative_path(
                    "//old/path.png",
                    Path("/project/old_dir"),
                    Path("/project/new_dir")
                )

                # Verify delegation occurred
                mock_rebase.assert_called_once_with(
                    "//old/path.png",
                    Path("/project/old_dir"),
                    Path("/project/new_dir")
                )
                assert result == "//new/path.png"


class TestPathRebaserUpdateBlendPaths:
    """Tests for PathRebaser.update_blend_paths method."""

    def test_update_blend_paths_dry_run_no_changes(self, tmp_path):
        """Test dry run with no path changes needed."""
        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = []
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "scene.blend"

            changes = rebaser.update_blend_paths(
                blend_path,
                old_location=Path("/old/texture.png"),
                new_location=Path("/new/texture.png"),
                dry_run=True
            )

            # Verify no files were opened in dry run
            assert not mock_bpy.ops.wm.open_mainfile.called
            assert changes == []

    def test_update_blend_paths_image_relative_path(self, tmp_path):
        """Test updating relative image path when file moves."""
        # Mock image with relative path
        mock_image = MagicMock()
        mock_image.name = "texture.png"
        mock_image.filepath = "//textures/texture.png"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.data.libraries = []
        mock_bpy.path.abspath.return_value = "/project/textures/texture.png"
        mock_bpy.path.relpath.return_value = "//new_textures/texture.png"

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "scene.blend"

            changes = rebaser.update_blend_paths(
                blend_path,
                old_location=Path("/project/textures"),
                new_location=Path("/project/new_textures"),
                dry_run=True
            )

            assert len(changes) == 1
            assert changes[0].item_type == "image"
            assert changes[0].item_name == "texture.png"
            assert changes[0].old_path == "//textures/texture.png"
            assert changes[0].new_path == "//new_textures/texture.png"
            assert changes[0].status == "ok"

    def test_update_blend_paths_library_relative_path(self, tmp_path):
        """Test updating relative library path when file moves."""
        # Mock library with relative path
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//libs/assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = []
        mock_bpy.data.libraries = [mock_library]
        mock_bpy.path.abspath.return_value = "/project/libs/assets.blend"
        mock_bpy.path.relpath.return_value = "//new_libs/assets.blend"

        with patch('os.path.realpath', return_value="/project/libs/assets.blend"):
            with patch.dict('sys.modules', {'bpy': mock_bpy}):
                from blender_lib.path_operations import PathRebaser

                rebaser = PathRebaser()
                blend_path = tmp_path / "scene.blend"

                changes = rebaser.update_blend_paths(
                    blend_path,
                    old_location=Path("/project/libs"),
                    new_location=Path("/project/new_libs"),
                    dry_run=True
                )

                assert len(changes) == 1
                assert changes[0].item_type == "library"
                assert changes[0].item_name == "assets.blend"
                assert changes[0].old_path == "//libs/assets.blend"
                assert changes[0].new_path == "//new_libs/assets.blend"

    def test_update_blend_paths_skips_empty_filepath(self, tmp_path):
        """Test that images with empty filepath are skipped."""
        # Mock image with no filepath
        mock_image = MagicMock()
        mock_image.name = "generated"
        mock_image.filepath = ""

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "scene.blend"

            changes = rebaser.update_blend_paths(
                blend_path,
                old_location=Path("/old"),
                new_location=Path("/new"),
                dry_run=True
            )

            assert changes == []

    def test_update_blend_paths_multiple_changes(self, tmp_path):
        """Test updating multiple images and libraries."""
        # Mock images
        mock_image1 = MagicMock()
        mock_image1.name = "tex1.png"
        mock_image1.filepath = "//textures/tex1.png"

        mock_image2 = MagicMock()
        mock_image2.name = "tex2.png"
        mock_image2.filepath = "//textures/tex2.png"

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//libs/assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image1, mock_image2]
        mock_bpy.data.libraries = [mock_library]

        def mock_abspath(path):
            if path == "//textures/tex1.png":
                return "/project/textures/tex1.png"
            elif path == "//textures/tex2.png":
                return "/project/textures/tex2.png"
            elif path == "//libs/assets.blend":
                return "/project/libs/assets.blend"
            return path

        mock_bpy.path.abspath.side_effect = mock_abspath
        mock_bpy.path.relpath.side_effect = lambda p: p.replace("/project/", "//")

        with patch('os.path.realpath', side_effect=lambda x: x):
            with patch.dict('sys.modules', {'bpy': mock_bpy}):
                from blender_lib.path_operations import PathRebaser

                rebaser = PathRebaser()
                blend_path = tmp_path / "scene.blend"

                changes = rebaser.update_blend_paths(
                    blend_path,
                    old_location=Path("/project"),
                    new_location=Path("/new_project"),
                    dry_run=True
                )

                # Should have 2 image changes + 1 library change
                assert len(changes) == 3
                image_changes = [c for c in changes if c.item_type == "image"]
                library_changes = [c for c in changes if c.item_type == "library"]
                assert len(image_changes) == 2
                assert len(library_changes) == 1


class TestPathRebaserRebaseBlendInternalPaths:
    """Tests for PathRebaser.rebase_blend_internal_paths method."""

    def test_rebase_blend_internal_paths_dry_run_no_images(self, tmp_path):
        """Test dry run with no images or libraries."""
        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = []
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            changes = rebaser.rebase_blend_internal_paths(
                blend_path,
                old_blend_location=tmp_path / "old" / "scene.blend",
                new_blend_location=tmp_path / "new" / "scene.blend",
                dry_run=True
            )

            assert changes == []

    def test_rebase_blend_internal_paths_image(self, tmp_path):
        """Test rebasing relative image path when blend file moves."""
        # Mock image with relative path
        mock_image = MagicMock()
        mock_image.name = "texture.png"
        mock_image.filepath = "//textures/texture.png"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            with patch.object(rebaser, 'rebase_relative_path', return_value="../textures/texture.png") as mock_rebase:
                changes = rebaser.rebase_blend_internal_paths(
                    blend_path,
                    old_blend_location=tmp_path / "old" / "scene.blend",
                    new_blend_location=tmp_path / "new" / "scene.blend",
                    dry_run=True
                )

                # Verify rebase was called
                mock_rebase.assert_called_once_with(
                    "//textures/texture.png",
                    tmp_path / "old",
                    tmp_path / "new"
                )

                assert len(changes) == 1
                assert changes[0].item_type == "image"
                assert changes[0].item_name == "texture.png"
                assert changes[0].old_path == "//textures/texture.png"
                assert changes[0].new_path == "../textures/texture.png"

    def test_rebase_blend_internal_paths_library(self, tmp_path):
        """Test rebasing relative library path when blend file moves."""
        # Mock library with relative path
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//libs/assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = []
        mock_bpy.data.libraries = [mock_library]

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            with patch.object(rebaser, 'rebase_relative_path', return_value="../../old/libs/assets.blend") as mock_rebase:
                changes = rebaser.rebase_blend_internal_paths(
                    blend_path,
                    old_blend_location=tmp_path / "old" / "scene.blend",
                    new_blend_location=tmp_path / "new" / "subdir" / "scene.blend",
                    dry_run=True
                )

                mock_rebase.assert_called_once()
                assert len(changes) == 1
                assert changes[0].item_type == "library"
                assert changes[0].item_name == "assets.blend"

    def test_rebase_blend_internal_paths_skips_absolute_paths(self, tmp_path):
        """Test that absolute paths are not rebased."""
        # Mock image with absolute path
        mock_image = MagicMock()
        mock_image.name = "texture.png"
        mock_image.filepath = "/absolute/path/texture.png"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            changes = rebaser.rebase_blend_internal_paths(
                blend_path,
                old_blend_location=tmp_path / "old" / "scene.blend",
                new_blend_location=tmp_path / "new" / "scene.blend",
                dry_run=True
            )

            # Absolute path should be skipped
            assert changes == []

    def test_rebase_blend_internal_paths_skips_unchanged_paths(self, tmp_path):
        """Test that unchanged paths don't create change entries."""
        # Mock image with relative path
        mock_image = MagicMock()
        mock_image.name = "texture.png"
        mock_image.filepath = "//textures/texture.png"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image]
        mock_bpy.data.libraries = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            # Rebase returns same path (no change needed)
            with patch.object(rebaser, 'rebase_relative_path', return_value="//textures/texture.png"):
                changes = rebaser.rebase_blend_internal_paths(
                    blend_path,
                    old_blend_location=tmp_path / "old" / "scene.blend",
                    new_blend_location=tmp_path / "old" / "scene.blend",  # Same location
                    dry_run=True
                )

                # No changes should be recorded
                assert changes == []

    def test_rebase_blend_internal_paths_multiple_items(self, tmp_path):
        """Test rebasing multiple images and libraries."""
        # Mock images
        mock_image1 = MagicMock()
        mock_image1.name = "tex1.png"
        mock_image1.filepath = "//textures/tex1.png"

        mock_image2 = MagicMock()
        mock_image2.name = "tex2.png"
        mock_image2.filepath = "//textures/tex2.png"

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//libs/assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.data.images = [mock_image1, mock_image2]
        mock_bpy.data.libraries = [mock_library]

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from blender_lib.path_operations import PathRebaser

            rebaser = PathRebaser()
            blend_path = tmp_path / "old" / "scene.blend"

            # All paths will be rebased
            with patch.object(rebaser, 'rebase_relative_path', side_effect=[
                "../textures/tex1.png",
                "../textures/tex2.png",
                "../libs/assets.blend"
            ]):
                changes = rebaser.rebase_blend_internal_paths(
                    blend_path,
                    old_blend_location=tmp_path / "old" / "scene.blend",
                    new_blend_location=tmp_path / "new" / "scene.blend",
                    dry_run=True
                )

                assert len(changes) == 3
                image_changes = [c for c in changes if c.item_type == "image"]
                library_changes = [c for c in changes if c.item_type == "library"]
                assert len(image_changes) == 2
                assert len(library_changes) == 1
