"""Scan multiple .blend files for references to a target file in a single Blender session.

This is much faster than launching Blender separately for each file.

Usage:
    blender --background --python batch_scan_references.py -- \
        --blend-files /path/to/file1.blend,/path/to/file2.blend,... \
        --target-file /path/to/target.blend
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

    blend_files = None
    target_file = None

    i = 0
    while i < len(args):
        if args[i] == "--blend-files" and i + 1 < len(args):
            blend_files = args[i + 1]
            i += 2
        elif args[i] == "--target-file" and i + 1 < len(args):
            target_file = args[i + 1]
            i += 2
        else:
            i += 1

    if not blend_files or not target_file:
        print("ERROR: Missing required arguments")
        return None

    return {
        "blend_files": [f.strip() for f in blend_files.split(",") if f.strip()],
        "target_file": target_file
    }


def scan_file_for_target(blend_path, target_abs_path):
    """Scan a single blend file for references to target file.

    Args:
        blend_path: Path to .blend file to scan
        target_abs_path: Absolute path to target file we're looking for

    Returns:
        Dictionary with reference information
    """
    result = {
        "blend_file": blend_path,
        "has_references": False,
        "images": [],
        "libraries": [],
        "error": None
    }

    try:
        # Open the blend file
        bpy.ops.wm.open_mainfile(filepath=blend_path)

        # Check images
        for img in bpy.data.images:
            if not img.filepath:
                continue

            resolved = bpy.path.abspath(img.filepath)
            resolved_abs = os.path.abspath(resolved)
            if resolved_abs == target_abs_path:
                result["has_references"] = True
                result["images"].append({
                    "name": img.name,
                    "filepath": img.filepath
                })

        # Check libraries
        for lib in bpy.data.libraries:
            if not lib.filepath:
                continue

            resolved = bpy.path.abspath(lib.filepath)
            resolved_abs = os.path.abspath(resolved)
            if resolved_abs == target_abs_path:
                result["has_references"] = True
                result["libraries"].append({
                    "name": lib.name,
                    "filepath": lib.filepath
                })

    except Exception as e:
        result["error"] = str(e)

    return result


def main():
    """Main entry point."""
    args = parse_args()
    if not args:
        sys.exit(1)

    target_abs = os.path.abspath(args["target_file"])

    results = {
        "target_file": args["target_file"],
        "files_scanned": 0,
        "files_with_references": [],
        "scan_results": []
    }

    for blend_file in args["blend_files"]:
        if not os.path.exists(blend_file):
            continue

        scan_result = scan_file_for_target(blend_file, target_abs)
        results["scan_results"].append(scan_result)
        results["files_scanned"] += 1

        if scan_result["has_references"]:
            results["files_with_references"].append(blend_file)

    print("JSON_OUTPUT:", json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
