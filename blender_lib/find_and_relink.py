"""Blender script to find missing files and relink them.

This script searches the project directory for files with matching names
and updates the paths in .blend files to point to the found files.
"""

import bpy
import sys
import argparse
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.file_scanner import find_blend_files


def find_missing_file_in_project(missing_filename: str, project_root: Path):
    """Search for a file by name in the project directory.

    Args:
        missing_filename: Name of the missing file
        project_root: Root directory to search

    Returns:
        List of matching file paths found
    """
    matches = []

    for path in project_root.rglob(missing_filename):
        if path.is_file():
            matches.append(path)

    return matches


def relink_broken_links_in_file(blend_file: Path, relink_map: dict):
    """Relink broken links in a single .blend file.

    Args:
        blend_file: Path to the .blend file
        relink_map: Dict mapping old paths to new paths

    Returns:
        Dictionary with results
    """
    result = {
        "file": str(blend_file),
        "file_name": blend_file.name,
        "relinked_libraries": 0,
        "relinked_textures": 0,
        "total_relinked": 0,
        "errors": []
    }

    try:
        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    except Exception as e:
        result["errors"].append(f"Could not open file: {str(e)}")
        return result

    for old_path, new_path in relink_map.items():
        for lib in bpy.data.libraries:
            lib_abs_path = bpy.path.abspath(lib.filepath)

            if lib_abs_path == old_path or lib.filepath == old_path:
                try:
                    lib.filepath = new_path
                    lib.reload()
                    result["relinked_libraries"] += 1
                    result["total_relinked"] += 1
                    print(f"LOG: Relinked library: {lib.name} -> {Path(new_path).name}", flush=True)
                except Exception as e:
                    result["errors"].append(f"Failed to relink library {lib.name}: {str(e)}")

        for img in bpy.data.images:
            if img.packed_file:
                continue

            if not img.filepath:
                continue

            img_abs_path = bpy.path.abspath(img.filepath)

            if img_abs_path == old_path or img.filepath == old_path:
                try:
                    img.filepath = new_path
                    img.reload()
                    result["relinked_textures"] += 1
                    result["total_relinked"] += 1
                    print(f"LOG: Relinked texture: {img.name} -> {Path(new_path).name}", flush=True)
                except Exception as e:
                    result["errors"].append(f"Failed to relink texture {img.name}: {str(e)}")

    if result["total_relinked"] > 0:
        try:
            bpy.ops.wm.save_mainfile()
            print(f"LOG: Saved changes to {blend_file.name}", flush=True)
        except Exception as e:
            result["errors"].append(f"Could not save file: {str(e)}")

    return result


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--broken-links', required=True, help='JSON string with broken links')
        parser.add_argument('--project-root', required=True, help='Project root directory')
        parser.add_argument('--mode', required=True, choices=['find', 'relink'], help='Mode: find or relink')
        parser.add_argument('--relink-map', required=False, help='JSON string with relink map (for relink mode)')

        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        project_root = Path(args.project_root)

        if args.mode == 'find':
            broken_links = json.loads(args.broken_links)

            result = {
                "found_files": [],
                "not_found": [],
                "errors": []
            }

            print(f"LOG: Searching for {len(broken_links)} missing file(s)...", flush=True)

            for link in broken_links:
                missing_path = link.get("path", "")
                missing_filename = Path(missing_path).name

                if not missing_filename:
                    continue

                print(f"LOG: Searching for {missing_filename}...", flush=True)

                matches = find_missing_file_in_project(missing_filename, project_root)

                if matches:
                    result["found_files"].append({
                        "original_link": link,
                        "missing_path": missing_path,
                        "missing_filename": missing_filename,
                        "found_paths": [str(m) for m in matches]
                    })
                    print(f"LOG: Found {len(matches)} match(es) for {missing_filename}", flush=True)
                else:
                    result["not_found"].append({
                        "original_link": link,
                        "missing_path": missing_path,
                        "missing_filename": missing_filename
                    })

            print(f"LOG: Search complete! Found {len(result['found_files'])} file(s)", flush=True)

            output_json(result)
            sys.exit(0)

        elif args.mode == 'relink':
            relink_map = json.loads(args.relink_map)

            result = {
                "files_relinked": [],
                "total_files_processed": 0,
                "total_relinked": 0,
                "errors": []
            }

            broken_links = json.loads(args.broken_links)

            files_to_process = {}
            for link in broken_links:
                file_path = link.get("file")
                if file_path not in files_to_process:
                    files_to_process[file_path] = {}

                old_path = link.get("path")
                if old_path in relink_map:
                    files_to_process[file_path][old_path] = relink_map[old_path]

            print(f"LOG: Relinking files in {len(files_to_process)} .blend file(s)...", flush=True)

            for file_path, file_relink_map in files_to_process.items():
                if not file_relink_map:
                    continue

                print(f"LOG: Processing {Path(file_path).name}...", flush=True)
                result["total_files_processed"] += 1

                file_result = relink_broken_links_in_file(Path(file_path), file_relink_map)

                if file_result["total_relinked"] > 0:
                    result["files_relinked"].append(file_result)
                    result["total_relinked"] += file_result["total_relinked"]

                if file_result["errors"]:
                    result["errors"].extend(file_result["errors"])

            print(f"LOG: Relink complete! Relinked {result['total_relinked']} file(s)", flush=True)

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
