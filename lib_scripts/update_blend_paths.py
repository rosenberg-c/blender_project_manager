"""Update image/library paths in a .blend file.

This script is called via Blender subprocess to update paths after
a file has been moved/renamed.

Usage:
    blender --background --python update_blend_paths.py -- \
        --blend-file /path/to/file.blend \
        --old-path /old/location \
        --new-path /new/location
"""

import json
import os
import sys

import bpy


def parse_args():
    """Parse command-line arguments."""
    if "--" not in sys.argv:
        print("ERROR: No arguments provided")
        return None

    idx = sys.argv.index("--") + 1
    args = sys.argv[idx:]

    blend_file = None
    old_path = None
    new_path = None

    i = 0
    while i < len(args):
        if args[i] == "--blend-file" and i + 1 < len(args):
            blend_file = args[i + 1]
            i += 2
        elif args[i] == "--old-path" and i + 1 < len(args):
            old_path = args[i + 1]
            i += 2
        elif args[i] == "--new-path" and i + 1 < len(args):
            new_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not all([blend_file, old_path, new_path]):
        print("ERROR: Missing required arguments")
        return None

    return {
        "blend_file": blend_file,
        "old_path": old_path,
        "new_path": new_path
    }


def update_paths(blend_file, old_path, new_path):
    """Update paths in blend file."""
    bpy.ops.wm.open_mainfile(filepath=blend_file)

    changes = []

    # Update image paths
    for img in bpy.data.images:
        if not img.filepath:
            continue

        original_path = img.filepath
        is_relative = original_path.startswith("//")

        abs_path = bpy.path.abspath(original_path)

        if old_path in abs_path:
            new_abs_path = abs_path.replace(old_path, new_path)

            if is_relative:
                new_img_path = bpy.path.relpath(new_abs_path)
            else:
                new_img_path = new_abs_path

            changes.append({
                "type": "image",
                "name": img.name,
                "old": original_path,
                "new": new_img_path
            })

            img.filepath = new_img_path
            if hasattr(img, 'filepath_raw'):
                img.filepath_raw = new_img_path

    # Update library paths
    for lib in bpy.data.libraries:
        if not lib.filepath:
            continue

        original_path = lib.filepath
        is_relative = original_path.startswith("//")

        abs_path = os.path.realpath(bpy.path.abspath(original_path))

        if old_path in abs_path:
            new_abs_path = abs_path.replace(old_path, new_path)

            if is_relative:
                new_lib_path = bpy.path.relpath(new_abs_path)
            else:
                new_lib_path = new_abs_path

            changes.append({
                "type": "library",
                "name": lib.name,
                "old": original_path,
                "new": new_lib_path
            })

            lib.filepath = new_lib_path

    # Save if changes were made
    if changes:
        bpy.ops.wm.save_mainfile()

    return changes


def main():
    """Main entry point."""
    args = parse_args()
    if not args:
        sys.exit(1)

    try:
        changes = update_paths(
            args["blend_file"],
            args["old_path"],
            args["new_path"]
        )
        result = {
            "success": True,
            "changes_count": len(changes),
            "changes": changes
        }
        print("JSON_OUTPUT:", json.dumps(result, indent=2))
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
        print("JSON_OUTPUT:", json.dumps(result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
