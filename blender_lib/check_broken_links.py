"""Blender script to find all broken links in .blend files.

Checks for:
- Broken library links (objects/collections from missing .blend files)
- Broken texture links (images from missing texture files)
- Broken collection links

This is useful for identifying missing dependencies in a project.
"""

import bpy
import sys
import argparse
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.file_scanner import find_blend_files


def check_broken_links_in_file(blend_file: Path):
    """Check a single .blend file for broken links.

    Args:
        blend_file: Path to the .blend file to check

    Returns:
        Dictionary with broken links found in this file
    """
    result = {
        "file": str(blend_file),
        "file_name": blend_file.name,
        "broken_libraries": [],
        "broken_textures": [],
        "broken_objects": [],
        "broken_collections": [],
        "total_broken": 0
    }

    try:
        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    except Exception as e:
        result["error"] = f"Could not open file: {str(e)}"
        return result

    # Check for broken library links
    for lib in bpy.data.libraries:
        lib_path = bpy.path.abspath(lib.filepath)

        if not lib_path or not os.path.exists(lib_path):
            linked_objects = [obj.name for obj in bpy.data.objects if obj.library == lib]
            linked_collections = [col.name for col in bpy.data.collections if col.library == lib]

            result["broken_libraries"].append({
                "library_name": lib.name,
                "library_filepath": lib.filepath,
                "resolved_path": lib_path,
                "linked_objects": linked_objects,
                "linked_collections": linked_collections,
                "objects_count": len(linked_objects),
                "collections_count": len(linked_collections)
            })
            result["total_broken"] += 1

    # Check for broken texture/image links
    for img in bpy.data.images:
        if img.packed_file:
            continue

        if not img.filepath:
            continue

        img_path = bpy.path.abspath(img.filepath)

        if not img_path or not os.path.exists(img_path):
            users_count = img.users

            result["broken_textures"].append({
                "image_name": img.name,
                "image_filepath": img.filepath,
                "resolved_path": img_path,
                "users_count": users_count,
                "size": [img.size[0], img.size[1]] if img.size[0] > 0 else [0, 0]
            })
            result["total_broken"] += 1

    return result


def check_all_files(project_root: str):
    """Check all .blend files in the project for broken links.

    Args:
        project_root: Root directory of the project

    Returns:
        Dictionary with all broken links found
    """
    result = {
        "files_with_broken_links": [],
        "total_files_checked": 0,
        "total_files_with_issues": 0,
        "total_broken_links": 0,
        "errors": [],
        "warnings": []
    }

    print(f"LOG: Scanning for .blend files in project...", flush=True)
    blend_files = find_blend_files(Path(project_root))
    print(f"LOG: Found {len(blend_files)} .blend files to check", flush=True)

    for i, blend_file in enumerate(blend_files, 1):
        print(f"LOG: Checking file {i}/{len(blend_files)}: {blend_file.name}", flush=True)
        result["total_files_checked"] += 1

        file_result = check_broken_links_in_file(blend_file)

        if "error" in file_result:
            result["errors"].append(f"{blend_file.name}: {file_result['error']}")
            continue

        if file_result["total_broken"] > 0:
            result["files_with_broken_links"].append(file_result)
            result["total_files_with_issues"] += 1
            result["total_broken_links"] += file_result["total_broken"]

            print(f"LOG: Found {file_result['total_broken']} broken link(s) in {blend_file.name}", flush=True)

    print(f"LOG: Check complete! Found {result['total_broken_links']} broken link(s) in {result['total_files_with_issues']} file(s)", flush=True)

    return result


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--project-root', required=True, help='Path to project root directory')

        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        result = check_all_files(args.project_root)

        output_json(result)
        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            files_with_broken_links=[],
            total_files_checked=0,
            total_files_with_issues=0,
            total_broken_links=0
        )
        output_json(error_result)
        sys.exit(1)
