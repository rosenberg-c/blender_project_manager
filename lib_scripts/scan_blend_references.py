"""Scan a .blend file for image and library references.

This script is called via Blender subprocess to extract all references
from a .blend file.

Usage:
    blender --background --python scan_blend_references.py -- \
        --blend-file /path/to/file.blend
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
    i = 0
    while i < len(args):
        if args[i] == "--blend-file" and i + 1 < len(args):
            blend_file = args[i + 1]
            i += 2
        else:
            i += 1

    if not blend_file:
        print("ERROR: Missing --blend-file argument")
        return None

    return {"blend_file": blend_file}


def scan_references(blend_path):
    """Scan blend file for references."""
    bpy.ops.wm.open_mainfile(filepath=blend_path)

    references = {
        "blend_path": blend_path,
        "images": [],
        "libraries": []
    }

    # Scan images
    for img in bpy.data.images:
        if img.filepath:
            img_ref = {
                "name": img.name,
                "filepath": img.filepath,
                "is_relative": img.filepath.startswith("//"),
                "resolved": bpy.path.abspath(img.filepath),
                "exists": os.path.exists(bpy.path.abspath(img.filepath))
            }
            references["images"].append(img_ref)

    # Scan libraries
    for lib in bpy.data.libraries:
        if lib.filepath:
            lib_ref = {
                "name": lib.name,
                "filepath": lib.filepath,
                "is_relative": lib.filepath.startswith("//"),
                "resolved": bpy.path.abspath(lib.filepath),
                "exists": os.path.exists(bpy.path.abspath(lib.filepath)),
                "objects": [obj.name for obj in bpy.data.objects if obj.library == lib],
                "collections": [col.name for col in bpy.data.collections if col.library == lib]
            }
            references["libraries"].append(lib_ref)

    return references


def main():
    """Main entry point."""
    args = parse_args()
    if not args:
        sys.exit(1)

    try:
        references = scan_references(args["blend_file"])
        print("JSON_OUTPUT:", json.dumps(references, indent=2))
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
