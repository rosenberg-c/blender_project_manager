"""Path rebasing operations for moving Blender files.

Refactored from the original scripts with added dry-run support for previewing changes.
"""

import os
from pathlib import Path
from typing import List

import bpy

from .models import PathChange


class PathRebaser:
    """Handles path rebasing when files or .blend files are moved."""

    @staticmethod
    def rebase_relative_path(original_path: str,
                            old_blend_dir: Path,
                            new_blend_dir: Path) -> str:
        """Convert Blender relative path when blend file moves.

        When a .blend file moves to a new directory, its relative paths (//)
        need to be updated to still point to the same absolute locations.

        Args:
            original_path: Blender path starting with '//'
            old_blend_dir: Directory where blend currently lives
            new_blend_dir: Directory where blend will move to

        Returns:
            New relative path that points to same absolute location

        Example:
            >>> old_dir = Path("/project/scenes")
            >>> new_dir = Path("/project/exported/scenes")
            >>> PathRebaser.rebase_relative_path("//../../textures/wood.jpg", old_dir, new_dir)
            "//../../../textures/wood.jpg"
        """
        if not original_path.startswith("//"):
            return original_path

        # Strip leading '//' and normalize slashes
        rel = original_path[2:].replace("\\", "/")

        # Get absolute path as seen from old blend directory
        abs_from_old = os.path.normpath(os.path.join(str(old_blend_dir), rel))

        # Calculate new relative path from new blend directory
        new_rel = os.path.relpath(abs_from_old, str(new_blend_dir))
        new_rel = new_rel.replace("\\", "/")

        return "//" + new_rel

    def update_blend_paths(self,
                          blend_path: Path,
                          old_location: Path,
                          new_location: Path,
                          dry_run: bool = False) -> List[PathChange]:
        """Update image/library paths in a blend file when a file moves.

        Args:
            blend_path: The .blend file to update
            old_location: Old path of moved file/directory
            new_location: New path of moved file/directory
            dry_run: If True, return changes without applying

        Returns:
            List of PathChange objects describing what changed
        """
        changes = []

        # Must be run inside Blender
        if not dry_run:
            bpy.ops.wm.open_mainfile(filepath=str(blend_path))

        blend_dir = blend_path.parent
        old_path_str = str(old_location)
        new_path_str = str(new_location)

        # Update image paths
        for img in bpy.data.images:
            if not img.filepath:
                continue

            original_path = img.filepath
            is_relative = original_path.startswith("//")

            # Get absolute path
            abs_path = bpy.path.abspath(original_path)

            # Check if this image references the moved file
            if old_path_str in abs_path:
                new_abs_path = abs_path.replace(old_path_str, new_path_str)

                if abs_path == new_abs_path:
                    continue  # No change needed

                # Convert back to relative/absolute based on original style
                if is_relative:
                    new_path = bpy.path.relpath(new_abs_path)
                else:
                    new_path = new_abs_path

                changes.append(PathChange(
                    file_path=blend_path,
                    item_type='image',
                    item_name=img.name,
                    old_path=original_path,
                    new_path=new_path,
                    status='ok'
                ))

                if not dry_run:
                    img.filepath = new_path
                    if hasattr(img, 'filepath_raw'):
                        img.filepath_raw = new_path

        # Update library paths
        for lib in bpy.data.libraries:
            if not lib.filepath:
                continue

            original_path = lib.filepath
            is_relative = original_path.startswith("//")

            abs_path_raw = bpy.path.abspath(original_path)
            abs_path = os.path.realpath(abs_path_raw)

            # Check if this library references the moved file
            if old_path_str in abs_path:
                new_abs_path = abs_path.replace(old_path_str, new_path_str)

                if abs_path == new_abs_path:
                    continue

                # Convert back to relative/absolute based on original style
                if is_relative:
                    new_path = bpy.path.relpath(new_abs_path)
                else:
                    new_path = new_abs_path

                changes.append(PathChange(
                    file_path=blend_path,
                    item_type='library',
                    item_name=lib.name,
                    old_path=original_path,
                    new_path=new_path,
                    status='ok'
                ))

                if not dry_run:
                    lib.filepath = new_path

        # Save if changes were made
        if not dry_run and changes:
            bpy.ops.wm.save_mainfile()

        return changes

    def rebase_blend_internal_paths(self,
                                   blend_path: Path,
                                   old_blend_location: Path,
                                   new_blend_location: Path,
                                   dry_run: bool = False) -> List[PathChange]:
        """Rebase internal relative paths when a .blend file itself moves.

        When a .blend file moves to a new directory, all its relative paths
        need to be rebased to still point to the same absolute files.

        Args:
            blend_path: The .blend file to update (currently at old_blend_location)
            old_blend_location: Current location of the .blend file
            new_blend_location: Where the .blend file will be moved to
            dry_run: If True, return changes without applying

        Returns:
            List of PathChange objects
        """
        changes = []

        if not dry_run:
            bpy.ops.wm.open_mainfile(filepath=str(blend_path))

        old_dir = old_blend_location.parent
        new_dir = new_blend_location.parent

        # Rebase image paths
        for img in bpy.data.images:
            if not img.filepath:
                continue

            original_path = img.filepath
            if not original_path.startswith("//"):
                continue  # Skip absolute paths

            new_path = self.rebase_relative_path(original_path, old_dir, new_dir)

            if new_path != original_path:
                changes.append(PathChange(
                    file_path=blend_path,
                    item_type='image',
                    item_name=img.name,
                    old_path=original_path,
                    new_path=new_path,
                    status='ok'
                ))

                if not dry_run:
                    img.filepath = new_path
                    if hasattr(img, 'filepath_raw'):
                        img.filepath_raw = new_path

        # Rebase library paths
        for lib in bpy.data.libraries:
            if not lib.filepath:
                continue

            original_path = lib.filepath
            if not original_path.startswith("//"):
                continue  # Skip absolute paths

            new_path = self.rebase_relative_path(original_path, old_dir, new_dir)

            if new_path != original_path:
                changes.append(PathChange(
                    file_path=blend_path,
                    item_type='library',
                    item_name=lib.name,
                    old_path=original_path,
                    new_path=new_path,
                    status='ok'
                ))

                if not dry_run:
                    lib.filepath = new_path

        # Save to new location if not dry run
        if not dry_run:
            bpy.ops.wm.save_mainfile(filepath=str(new_blend_location))

        return changes
