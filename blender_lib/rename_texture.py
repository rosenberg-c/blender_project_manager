"""Blender script to rename texture files and update all .blend file references."""

import bpy
import sys
import argparse
import os
import shutil

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def find_blend_files(root_path):
    """Find all .blend files under root path, excluding ignored directories."""
    ignore_dirs = {".git", ".svn", ".hg", "__pycache__", ".idea", ".vscode"}
    blend_files = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith(".")]

        for fname in filenames:
            if fname.lower().endswith(".blend") and not fname.startswith("."):
                blend_files.append(os.path.join(dirpath, fname))

    return blend_files


def rename_texture_on_disk(old_path, new_path, dry_run=True):
    """Rename/move texture file on disk.

    Args:
        old_path: Current path to texture file
        new_path: New path for texture file
        dry_run: If True, don't actually move the file

    Returns:
        Dictionary with result
    """
    result = {
        "success": False,
        "error": None,
        "moved": False
    }

    if not os.path.exists(old_path):
        result["error"] = f"Source file does not exist: {old_path}"
        return result

    if os.path.exists(new_path):
        result["error"] = f"Target file already exists: {new_path}"
        return result

    # Create target directory if needed
    target_dir = os.path.dirname(new_path)
    if not os.path.exists(target_dir):
        if not dry_run:
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                result["error"] = f"Could not create directory {target_dir}: {e}"
                return result

    # Move the file
    if not dry_run:
        try:
            shutil.move(old_path, new_path)
            result["moved"] = True
        except Exception as e:
            result["error"] = f"Could not move file: {e}"
            return result

    result["success"] = True
    return result


def update_image_references_in_blend(old_path_abs, new_path_abs, dry_run=True):
    """Update image references in the currently open .blend file.

    Args:
        old_path_abs: Absolute path to old texture file
        new_path_abs: Absolute path to new texture file
        dry_run: If True, don't actually save changes

    Returns:
        Dictionary with updated images
    """
    result = {
        "updated_images": [],
        "warnings": []
    }

    for img in bpy.data.images:
        if not img.filepath:
            continue

        original_path = img.filepath
        is_relative = original_path.startswith("//")

        # Resolve to absolute path
        abs_path = bpy.path.abspath(original_path)
        abs_path = os.path.normpath(os.path.realpath(abs_path))

        # Check if this image references our old texture
        if abs_path == old_path_abs:
            # Determine new path (preserve relative vs absolute)
            if is_relative:
                new_path = bpy.path.relpath(new_path_abs)
            else:
                new_path = new_path_abs

            result["updated_images"].append({
                "name": img.name,
                "old_path": original_path,
                "new_path": new_path
            })

            # Update the path if not dry run
            if not dry_run:
                img.filepath = new_path
                if hasattr(img, "filepath_raw"):
                    img.filepath_raw = new_path

    return result


def process_blend_files(root_dir, old_path_abs, new_path_abs, dry_run=True):
    """Process all .blend files to update image references.

    Args:
        root_dir: Project root directory
        old_path_abs: Absolute path to old texture
        new_path_abs: Absolute path to new texture
        dry_run: If True, don't save files

    Returns:
        Dictionary with results
    """
    result = {
        "updated_files": [],
        "errors": [],
        "warnings": []
    }

    # Find all .blend files
    blend_files = find_blend_files(root_dir)

    for blend_file in blend_files:
        try:
            # Open the blend file
            bpy.ops.wm.open_mainfile(filepath=blend_file)

            # Update image references
            update_result = update_image_references_in_blend(old_path_abs, new_path_abs, dry_run)

            if update_result["updated_images"]:
                result["updated_files"].append({
                    "file": blend_file,
                    "updated_images": update_result["updated_images"]
                })

                # Save if not dry run
                if not dry_run:
                    try:
                        bpy.ops.wm.save_mainfile()
                    except Exception as e:
                        result["errors"].append(f"Could not save {blend_file}: {e}")

            result["warnings"].extend(update_result["warnings"])

        except Exception as e:
            result["warnings"].append(f"Could not process {blend_file}: {e}")

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--old-path', required=True, help='Current path to texture file')
        parser.add_argument('--new-path', required=True, help='New path for texture file')
        parser.add_argument('--project-root', required=True, help='Project root directory')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        dry_run = args.dry_run == 'true'
        old_path_abs = os.path.normpath(os.path.realpath(args.old_path))
        new_path_abs = os.path.normpath(os.path.realpath(args.new_path))

        result = {
            "success": True,
            "file_moved": False,
            "updated_files": [],
            "updated_files_count": 0,
            "errors": [],
            "warnings": []
        }

        # Step 1: Rename the file on disk
        rename_result = rename_texture_on_disk(old_path_abs, new_path_abs, dry_run)

        if not rename_result["success"]:
            result["success"] = False
            result["errors"].append(rename_result["error"])
        else:
            result["file_moved"] = rename_result["moved"]

            # Step 2: Update all .blend file references
            update_result = process_blend_files(args.project_root, old_path_abs, new_path_abs, dry_run)

            result["updated_files"] = update_result["updated_files"]
            result["updated_files_count"] = len(update_result["updated_files"])
            result["errors"].extend(update_result["errors"])
            result["warnings"].extend(update_result["warnings"])

        # Output as JSON
        output_json(result)

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            file_moved=False,
            updated_files=[],
            updated_files_count=0
        )
        output_json(error_result)
        sys.exit(1)
