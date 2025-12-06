"""Blender script to rebase internal paths in a .blend file after it has been moved."""

import bpy
import json
import sys
import argparse
import os
from pathlib import Path


def rebase_relative_path(original_path, old_blend_dir, new_blend_dir):
    """Given a Blender-style relative path starting with '//',
    compute a new relative path from new_blend_dir that still points
    to the same absolute file.

    Args:
        original_path: Path like '//../../textures/wood.jpg'
        old_blend_dir: Directory where blend file WAS located
        new_blend_dir: Directory where blend file IS NOW located

    Returns:
        New relative path from new_blend_dir
    """
    if not original_path.startswith("//"):
        return original_path

    # Remove '//' prefix
    rel_part = original_path[2:]

    # Resolve to absolute path from old location
    old_abs = os.path.normpath(os.path.join(old_blend_dir, rel_part))

    # Create new relative path from new location
    try:
        new_rel = os.path.relpath(old_abs, new_blend_dir)
        # Convert back slashes to forward slashes for Blender
        new_rel = new_rel.replace("\\", "/")
    except ValueError:
        # Can't make relative path (different drives on Windows)
        return original_path

    return "//" + new_rel


def rebase_blend_file(blend_path, old_dir, new_dir, dry_run=True):
    """Rebase all internal relative paths in a .blend file.

    The .blend file should already be at its new location.
    This function updates its internal paths to account for the move.

    Args:
        blend_path: Path to .blend file (at its current/new location)
        old_dir: Directory where the blend file WAS located
        new_dir: Directory where the blend file IS NOW located
        dry_run: If True, don't save changes

    Returns:
        Dictionary with results
    """
    result = {
        "success": True,
        "rebased_images": [],
        "rebased_libraries": [],
        "errors": [],
        "warnings": []
    }

    try:
        # Open the blend file at its current location
        bpy.ops.wm.open_mainfile(filepath=blend_path)

        old_dir_path = Path(old_dir)
        new_dir_path = Path(new_dir)

        # Rebase image paths
        for img in bpy.data.images:
            if not img.filepath:
                continue

            original_path = img.filepath

            # Only rebase relative paths
            if not original_path.startswith("//"):
                continue

            new_path = rebase_relative_path(original_path, str(old_dir_path), str(new_dir_path))

            if new_path != original_path:
                result["rebased_images"].append({
                    "name": img.name,
                    "old_path": original_path,
                    "new_path": new_path
                })

                if not dry_run:
                    img.filepath = new_path

        # Rebase library paths
        for lib in bpy.data.libraries:
            if not lib.filepath:
                continue

            original_path = lib.filepath

            # Only rebase relative paths
            if not original_path.startswith("//"):
                continue

            new_path = rebase_relative_path(original_path, str(old_dir_path), str(new_dir_path))

            if new_path != original_path:
                result["rebased_libraries"].append({
                    "name": lib.name,
                    "old_path": original_path,
                    "new_path": new_path
                })

                if not dry_run:
                    lib.filepath = new_path

        # Save the file if not dry run
        if not dry_run and (result["rebased_images"] or result["rebased_libraries"]):
            bpy.ops.wm.save_mainfile()

    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--blend-file', required=True, help='Path to .blend file (at current location)')
        parser.add_argument('--old-dir', required=True, help='Directory where file was located')
        parser.add_argument('--new-dir', required=True, help='Directory where file is now located')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        blend_path = os.path.abspath(args.blend_file)
        old_dir = os.path.abspath(args.old_dir)
        new_dir = os.path.abspath(args.new_dir)
        dry_run = args.dry_run == 'true'

        result = rebase_blend_file(blend_path, old_dir, new_dir, dry_run)

        # Output as JSON
        print("JSON_OUTPUT:" + json.dumps(result, indent=2))

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = {
            "success": False,
            "errors": [str(e)],
            "traceback": traceback.format_exc()
        }
        print("JSON_OUTPUT:" + json.dumps(error_result, indent=2))
        sys.exit(1)
