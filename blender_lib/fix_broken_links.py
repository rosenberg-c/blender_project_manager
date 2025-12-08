"""Blender script to fix broken links by removing them from .blend files.

This script removes broken library links and broken texture references from .blend files.
For library links, it removes the linked objects/collections.
For textures, it removes the image datablocks.
"""

import bpy
import sys
import argparse
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def fix_broken_links_in_file(blend_file: Path, links_to_fix: list):
    """Fix broken links in a single .blend file.

    Args:
        blend_file: Path to the .blend file
        links_to_fix: List of broken links to fix (from check_broken_links.py)

    Returns:
        Dictionary with results
    """
    result = {
        "file": str(blend_file),
        "file_name": blend_file.name,
        "fixed_libraries": 0,
        "fixed_textures": 0,
        "total_fixed": 0,
        "errors": []
    }

    try:
        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    except Exception as e:
        result["errors"].append(f"Could not open file: {str(e)}")
        return result

    for link in links_to_fix:
        link_type = link.get("type")
        link_name = link.get("name")
        missing_path = link.get("path")

        if link_type == "Library":
            for lib in bpy.data.libraries:
                lib_path = bpy.path.abspath(lib.filepath)

                if not lib_path or not os.path.exists(lib_path):
                    if lib.name == link_name or lib_path == missing_path or lib.filepath == missing_path:
                        try:
                            linked_objects = [obj for obj in bpy.data.objects if obj.library == lib]
                            for obj in linked_objects:
                                bpy.data.objects.remove(obj)

                            linked_collections = [col for col in bpy.data.collections if col.library == lib]
                            for col in linked_collections:
                                bpy.data.collections.remove(col)

                            result["fixed_libraries"] += 1
                            result["total_fixed"] += 1
                            print(f"LOG: Removed broken library link: {link_name}", flush=True)
                        except Exception as e:
                            result["errors"].append(f"Failed to remove library {link_name}: {str(e)}")
                        break

        elif link_type == "Texture":
            for img in bpy.data.images:
                if img.packed_file:
                    continue

                if not img.filepath:
                    continue

                img_path = bpy.path.abspath(img.filepath)

                if not img_path or not os.path.exists(img_path):
                    if img.name == link_name or img_path == missing_path or img.filepath == missing_path:
                        try:
                            bpy.data.images.remove(img)
                            result["fixed_textures"] += 1
                            result["total_fixed"] += 1
                            print(f"LOG: Removed broken texture: {link_name}", flush=True)
                        except Exception as e:
                            result["errors"].append(f"Failed to remove texture {link_name}: {str(e)}")
                        break

    if result["total_fixed"] > 0:
        try:
            bpy.ops.wm.save_mainfile()
            print(f"LOG: Saved changes to {blend_file.name}", flush=True)
        except Exception as e:
            result["errors"].append(f"Could not save file: {str(e)}")

    return result


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--links-to-fix', required=True, help='JSON string with links to fix')

        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        links_data = json.loads(args.links_to_fix)

        result = {
            "files_fixed": [],
            "total_files_processed": 0,
            "total_fixed": 0,
            "errors": [],
            "warnings": []
        }

        files_to_process = {}
        for link in links_data:
            file_path = link.get("file")
            if file_path not in files_to_process:
                files_to_process[file_path] = []
            files_to_process[file_path].append(link)

        print(f"LOG: Processing {len(files_to_process)} file(s)...", flush=True)

        for file_path, links in files_to_process.items():
            print(f"LOG: Fixing broken links in {Path(file_path).name}...", flush=True)
            result["total_files_processed"] += 1

            file_result = fix_broken_links_in_file(Path(file_path), links)

            if file_result["total_fixed"] > 0:
                result["files_fixed"].append(file_result)
                result["total_fixed"] += file_result["total_fixed"]

            if file_result["errors"]:
                result["errors"].extend(file_result["errors"])

        print(f"LOG: Fix complete! Fixed {result['total_fixed']} broken link(s) in {len(result['files_fixed'])} file(s)", flush=True)

        output_json(result)
        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            files_fixed=[],
            total_files_processed=0,
            total_fixed=0
        )
        output_json(error_result)
        sys.exit(1)
