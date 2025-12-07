"""Blender script to move a .blend file and rebase all internal relative paths."""

import bpy
import sys
import argparse
import os
import shutil

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def rebase_relative_path(original_path, old_scene_dir, new_scene_dir):
    """Given a Blender-style relative path starting with '//',
    compute a new relative path from new_scene_dir that still points
    to the same absolute file.

    Args:
        original_path: Original relative path (e.g., '//textures/image.png')
        old_scene_dir: Directory of the old .blend file
        new_scene_dir: Directory where .blend will be moved to

    Returns:
        New relative path string (still starting with '//')
    """
    # Strip leading '//' and normalize
    rel = original_path[2:]
    rel = rel.replace("\\", "/")

    # Absolute path as seen from the old scene dir
    abs_from_old = os.path.normpath(os.path.join(old_scene_dir, rel))

    # New relative path from new scene dir
    new_rel = os.path.relpath(abs_from_old, new_scene_dir)
    new_rel = new_rel.replace("\\", "/")

    return "//" + new_rel


def move_scene_and_rebase(old_scene_path, new_scene_path, delete_old=False, dry_run=True):
    """Move a .blend file and rebase all internal relative paths.

    Args:
        old_scene_path: Current path to .blend file
        new_scene_path: New path for .blend file
        delete_old: Whether to delete the old file after moving
        dry_run: If True, don't actually save or move files

    Returns:
        Dictionary with results
    """
    result = {
        "success": True,
        "file_moved": False,
        "old_deleted": False,
        "rebased_images": [],
        "rebased_libraries": [],
        "errors": [],
        "warnings": []
    }

    # Validation
    if not os.path.exists(old_scene_path):
        result["success"] = False
        result["errors"].append(f"Source file does not exist: {old_scene_path}")
        return result

    if os.path.exists(new_scene_path) and not dry_run:
        result["success"] = False
        result["errors"].append(f"Target file already exists: {new_scene_path}")
        return result

    try:
        # Open the old scene
        bpy.ops.wm.open_mainfile(filepath=old_scene_path)

        old_scene_dir = os.path.dirname(old_scene_path)
        new_scene_dir = os.path.dirname(new_scene_path)

        # Rebase image paths
        for img in bpy.data.images:
            if not img.filepath:
                continue

            original_path = img.filepath
            if not original_path.startswith("//"):
                # Absolute or other form; skip
                continue

            new_path = rebase_relative_path(original_path, old_scene_dir, new_scene_dir)
            if new_path != original_path:
                result["rebased_images"].append({
                    "name": img.name,
                    "old_path": original_path,
                    "new_path": new_path
                })

                if not dry_run:
                    img.filepath = new_path
                    if hasattr(img, "filepath_raw"):
                        img.filepath_raw = new_path

        # Rebase library paths
        for lib in bpy.data.libraries:
            if not lib.filepath:
                continue

            original_path = lib.filepath
            if not original_path.startswith("//"):
                # Absolute; skip
                continue

            new_path = rebase_relative_path(original_path, old_scene_dir, new_scene_dir)
            if new_path != original_path:
                result["rebased_libraries"].append({
                    "name": lib.name,
                    "old_path": original_path,
                    "new_path": new_path
                })

                if not dry_run:
                    lib.filepath = new_path

        # Save to new location if not dry run
        if not dry_run:
            # Create target directory if needed
            new_dir = os.path.dirname(new_scene_path)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir, exist_ok=True)

            bpy.ops.wm.save_mainfile(filepath=new_scene_path)
            result["file_moved"] = True

            # Delete old file if requested
            if delete_old:
                try:
                    os.remove(old_scene_path)
                    result["old_deleted"] = True
                except Exception as e:
                    result["warnings"].append(f"Could not delete old file: {e}")

    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--old-scene', required=True, help='Current path to .blend file')
        parser.add_argument('--new-scene', required=True, help='New path for .blend file')
        parser.add_argument('--delete-old', choices=['true', 'false'], default='false', help='Delete old file')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        old_scene_abs = os.path.abspath(args.old_scene)
        new_scene_abs = os.path.abspath(args.new_scene)
        delete_old = args.delete_old == 'true'
        dry_run = args.dry_run == 'true'

        result = move_scene_and_rebase(old_scene_abs, new_scene_abs, delete_old, dry_run)

        # Output as JSON
        output_json(result)

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            file_moved=False,
            old_deleted=False,
            rebased_images=[],
            rebased_libraries=[],
            traceback=traceback.format_exc()
        )
        output_json(error_result)
        sys.exit(1)
