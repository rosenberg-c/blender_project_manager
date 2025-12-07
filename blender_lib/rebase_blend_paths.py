"""Blender script to rebase internal paths in a .blend file after it has been moved."""

import bpy
import sys
import argparse
import os
from pathlib import Path

# Add parent directory to path so we can import core module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import shared utilities
from blender_lib.script_utils import output_json, create_error_result, create_success_result

from core.path_utils import rebase_relative_path


def rebase_blend_file(blend_path, old_dir, new_dir, moved_files_old_paths=None, dry_run=True):
    """Rebase all internal relative paths in a .blend file.

    The .blend file should already be at its new location.
    This function updates its internal paths to account for the move.

    If moved_files_old_paths is provided, paths pointing to those files
    will NOT be rebased (since those files moved with this .blend file,
    the relative relationship is preserved).

    Args:
        blend_path: Path to .blend file (at its current/new location)
        old_dir: Directory where the blend file WAS located
        new_dir: Directory where the blend file IS NOW located
        moved_files_old_paths: List of old absolute paths of files that were also moved
        dry_run: If True, don't save changes

    Returns:
        Dictionary with results
    """
    result = {
        "success": True,
        "rebased_images": [],
        "rebased_libraries": [],
        "skipped_paths": [],
        "errors": [],
        "warnings": []
    }

    try:
        # Open the blend file at its current location
        bpy.ops.wm.open_mainfile(filepath=blend_path)

        old_dir_path = Path(old_dir)
        new_dir_path = Path(new_dir)

        # Convert moved files list to a set for faster lookup
        moved_files_set = set()
        if moved_files_old_paths:
            moved_files_set = {os.path.normpath(str(p)) for p in moved_files_old_paths}

        # Rebase image paths
        for img in bpy.data.images:
            if not img.filepath:
                continue

            original_path = img.filepath

            # Only rebase relative paths
            if not original_path.startswith("//"):
                continue

            # Resolve the original path to absolute from OLD location
            rel_part = original_path[2:]
            old_abs_path = os.path.normpath(os.path.join(str(old_dir_path), rel_part))

            # Check if this file was also moved
            if old_abs_path in moved_files_set:
                # File was also moved - keep relative path unchanged
                result["skipped_paths"].append({
                    "name": img.name,
                    "path": original_path,
                    "reason": "Referenced file was also moved"
                })
                continue

            # File was NOT moved - rebase the path
            new_path = rebase_relative_path(original_path, old_dir_path, new_dir_path)

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

            # Resolve the original path to absolute from OLD location
            rel_part = original_path[2:]
            old_abs_path = os.path.normpath(os.path.join(str(old_dir_path), rel_part))

            # Check if this file was also moved
            if old_abs_path in moved_files_set:
                # File was also moved - keep relative path unchanged
                result["skipped_paths"].append({
                    "name": lib.name,
                    "path": original_path,
                    "reason": "Referenced file was also moved"
                })
                continue

            # File was NOT moved - rebase the path
            new_path = rebase_relative_path(original_path, old_dir_path, new_dir_path)

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
        parser.add_argument('--moved-files', default='', help='Comma-separated list of old absolute paths of moved files')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        blend_path = os.path.abspath(args.blend_file)
        old_dir = os.path.abspath(args.old_dir)
        new_dir = os.path.abspath(args.new_dir)
        dry_run = args.dry_run == 'true'

        # Parse moved files list
        moved_files = []
        if args.moved_files:
            moved_files = [f.strip() for f in args.moved_files.split(',') if f.strip()]

        result = rebase_blend_file(blend_path, old_dir, new_dir, moved_files, dry_run)

        # Output as JSON
        output_json(result)

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc()
        )
        output_json(error_result)
        sys.exit(1)
