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
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.file_scanner import find_blend_files


def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


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


def find_similar_files_in_project(missing_filename: str, project_root: Path, min_similarity: float = 0.6):
    """Search for files with similar names in the project directory.

    Args:
        missing_filename: Name of the missing file
        project_root: Root directory to search
        min_similarity: Minimum similarity ratio (0.0 to 1.0)

    Returns:
        List of tuples: (file_path, similarity_ratio) sorted by similarity
    """
    missing_name = Path(missing_filename).stem.lower()
    missing_ext = Path(missing_filename).suffix.lower()

    similar_files = []

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue

        if missing_ext and path.suffix.lower() != missing_ext:
            continue

        candidate_name = path.stem.lower()
        ratio = similarity_ratio(missing_name, candidate_name)

        if ratio >= min_similarity and ratio < 1.0:
            similar_files.append((path, ratio))

    similar_files.sort(key=lambda x: x[1], reverse=True)

    return similar_files[:5]


def relink_broken_links_in_file(blend_file: Path, links_with_new_paths: list):
    """Relink broken links in a single .blend file.

    Args:
        blend_file: Path to the .blend file
        links_with_new_paths: List of link dicts with 'name', 'type', and 'new_path'

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

    for link_info in links_with_new_paths:
        link_type = link_info.get("type")
        link_name = link_info.get("name")
        new_path = link_info.get("new_path")

        # Convert to relative path (with // prefix) for portability
        try:
            relative_path = bpy.path.relpath(new_path)
        except:
            # If conversion fails, use absolute path
            relative_path = new_path

        if link_type == "Library":
            for lib in bpy.data.libraries:
                if lib.name == link_name:
                    try:
                        old_path = lib.filepath
                        old_resolved = bpy.path.abspath(old_path)
                        lib.filepath = relative_path
                        lib.reload()
                        result["relinked_libraries"] += 1
                        result["total_relinked"] += 1
                        print(f"LOG: Relinked library: {lib.name}", flush=True)
                        print(f"LOG:   Old: stored='{old_path}', resolved='{old_resolved}'", flush=True)
                        print(f"LOG:   New: stored='{relative_path}', resolved='{new_path}'", flush=True)
                    except Exception as e:
                        result["errors"].append(f"Failed to relink library {lib.name}: {str(e)}")
                        print(f"LOG: ⚠️ Error relinking library {lib.name}: {str(e)}", flush=True)
                    break

        elif link_type == "Texture":
            for img in bpy.data.images:
                if img.packed_file:
                    continue

                if img.name == link_name:
                    try:
                        old_path = img.filepath
                        old_resolved = bpy.path.abspath(old_path)
                        img.filepath = relative_path
                        img.reload()
                        result["relinked_textures"] += 1
                        result["total_relinked"] += 1
                        print(f"LOG: Relinked texture: {img.name}", flush=True)
                        print(f"LOG:   Old: stored='{old_path}', resolved='{old_resolved}'", flush=True)
                        print(f"LOG:   New: stored='{relative_path}', resolved='{new_path}'", flush=True)
                    except Exception as e:
                        result["errors"].append(f"Failed to relink texture {img.name}: {str(e)}")
                        print(f"LOG: ⚠️ Error relinking texture {img.name}: {str(e)}", flush=True)
                    break

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
                "similar_files": [],
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

                exact_matches = find_missing_file_in_project(missing_filename, project_root)

                if exact_matches:
                    result["found_files"].append({
                        "original_link": link,
                        "missing_path": missing_path,
                        "missing_filename": missing_filename,
                        "found_paths": [str(m) for m in exact_matches]
                    })
                    print(f"LOG: Found {len(exact_matches)} exact match(es) for {missing_filename}", flush=True)
                else:
                    print(f"LOG: No exact match for {missing_filename}, searching for similar files...", flush=True)
                    similar_matches = find_similar_files_in_project(missing_filename, project_root)

                    if similar_matches:
                        result["similar_files"].append({
                            "original_link": link,
                            "missing_path": missing_path,
                            "missing_filename": missing_filename,
                            "similar_matches": [
                                {
                                    "path": str(path),
                                    "similarity": round(ratio * 100, 1)
                                }
                                for path, ratio in similar_matches
                            ]
                        })
                        print(f"LOG: Found {len(similar_matches)} similar match(es) for {missing_filename}", flush=True)
                    else:
                        result["not_found"].append({
                            "original_link": link,
                            "missing_path": missing_path,
                            "missing_filename": missing_filename
                        })
                        print(f"LOG: No matches found for {missing_filename}", flush=True)

            print(f"LOG: Search complete! Found {len(result['found_files'])} exact and {len(result['similar_files'])} similar match(es)", flush=True)

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
                    files_to_process[file_path] = []

                old_path = link.get("path")
                if old_path in relink_map:
                    files_to_process[file_path].append({
                        "type": link.get("type"),
                        "name": link.get("name"),
                        "new_path": relink_map[old_path]
                    })

            print(f"LOG: Relinking files in {len(files_to_process)} .blend file(s)...", flush=True)

            for file_path, links_to_relink in files_to_process.items():
                if not links_to_relink:
                    continue

                print(f"LOG: Processing {Path(file_path).name}...", flush=True)
                result["total_files_processed"] += 1

                file_result = relink_broken_links_in_file(Path(file_path), links_to_relink)

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
