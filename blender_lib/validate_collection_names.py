"""Blender script to validate that linked collection names still exist in their source files.

This script checks for collections that are linked from library files where the file exists,
but the specific collection name has been renamed or deleted in the source file.
"""

import bpy
import sys
import argparse
import os
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def similarity_ratio(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def get_collections_from_library(library_path: Path) -> List[str]:
    """Get list of collection names from a library file without linking.

    Args:
        library_path: Path to the library .blend file

    Returns:
        List of collection names available in the library
    """
    collections = []

    try:
        # Use library load in list-only mode (link=False) to read available data
        with bpy.data.libraries.load(str(library_path), link=False) as (data_from, data_to):
            collections = list(data_from.collections)

        print(f"LOG: Found {len(collections)} collections in library: {library_path.name}", flush=True)

    except Exception as e:
        print(f"LOG: ERROR reading collections from {library_path}: {str(e)}", flush=True)

    return collections


def detect_link_mode(collection_name: str, library: bpy.types.Library) -> Dict[str, Optional[str]]:
    """Detect how a collection is linked (instance mode vs individual mode).

    Instance mode: Collection is instanced via an Empty object with instance_collection property
    Individual mode: Collection is directly linked into the scene hierarchy

    Args:
        collection_name: Name of the collection to check
        library: The library object the collection is linked from

    Returns:
        Dictionary with "mode" ("instance" or "individual") and optional "instance_object_name"
    """
    # Get the actual collection object from the current file
    collection = bpy.data.collections.get(collection_name)

    if not collection:
        print(f"LOG: Collection '{collection_name}' not found in current file", flush=True)
        return {
            "mode": "individual",
            "instance_object_name": None
        }

    # Check for instance mode: Look for Empty objects with this collection as instance_collection
    for obj in bpy.data.objects:
        if obj.instance_type == 'COLLECTION' and obj.instance_collection:
            # Compare the actual collection object, not name
            if obj.instance_collection == collection:
                print(f"LOG: Collection '{collection_name}' linked as instance via Empty '{obj.name}'", flush=True)
                return {
                    "mode": "instance",
                    "instance_object_name": obj.name
                }

    # If not found as instance, it must be individual mode (directly linked)
    print(f"LOG: Collection '{collection_name}' linked in individual mode", flush=True)
    return {
        "mode": "individual",
        "instance_object_name": None
    }


def find_similar_collection_names(missing_name: str, available: List[str], threshold: float = 0.6) -> List[Dict[str, any]]:
    """Find similar collection names using fuzzy matching.

    Args:
        missing_name: The collection name that wasn't found
        available: List of available collection names in the library
        threshold: Minimum similarity ratio (0.0 to 1.0) to include in results

    Returns:
        List of dictionaries with "name" and "similarity" keys, sorted by similarity (best first)
    """
    matches = []

    for name in available:
        similarity = similarity_ratio(missing_name, name)
        if similarity >= threshold:
            matches.append({
                "name": name,
                "similarity": round(similarity, 3)
            })

    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x["similarity"], reverse=True)

    # Return top 5 matches
    return matches[:5]


def validate_collection_names_in_file(blend_file: Path) -> Dict:
    """Validate that linked collection names exist in their source library files.

    This checks collections linked from libraries where the file exists, but the
    specific collection name may have been renamed or deleted.

    Args:
        blend_file: Path to the .blend file to check

    Returns:
        Dictionary with broken collection references found
    """
    result = {
        "file": str(blend_file),
        "file_name": blend_file.name,
        "broken_collection_refs": [],
        "total_broken": 0
    }

    try:
        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    except Exception as e:
        result["error"] = f"Could not open file: {str(e)}"
        return result

    print(f"LOG: Validating collection names in: {blend_file.name}", flush=True)

    # Iterate through all libraries that exist (file-level check already passed)
    for lib in bpy.data.libraries:
        # Resolve library path
        lib_path = bpy.path.abspath(lib.filepath)

        # Only check libraries where the file exists
        if not lib_path or not os.path.exists(lib_path):
            print(f"LOG: Skipping library '{lib.name}' - file doesn't exist", flush=True)
            continue

        print(f"LOG: Checking collections in library: {lib.name}", flush=True)

        # Get collections linked from this library in the current file
        linked_collections = [col for col in bpy.data.collections if col.library == lib]

        if not linked_collections:
            print(f"LOG: No collections linked from library '{lib.name}'", flush=True)
            continue

        print(f"LOG: Found {len(linked_collections)} linked collection(s) from '{lib.name}'", flush=True)

        # Get actual collections available in the library file
        available_collections = get_collections_from_library(Path(lib_path))

        # Check each linked collection
        for col in linked_collections:
            collection_name = col.name

            # Check if this collection name exists in the source library
            if collection_name not in available_collections:
                print(f"LOG: ⚠️ Broken collection reference: '{collection_name}' not found in '{lib.name}'", flush=True)

                # Find similar names
                suggestions = find_similar_collection_names(collection_name, available_collections)

                # Detect link mode
                link_info = detect_link_mode(collection_name, lib)

                broken_ref = {
                    "library_name": lib.name,
                    "library_filepath": lib.filepath,
                    "resolved_library_path": lib_path,
                    "collection_name": collection_name,
                    "available_collections": available_collections,
                    "suggested_matches": suggestions,
                    "link_mode": link_info["mode"],
                    "instance_object_name": link_info["instance_object_name"]
                }

                result["broken_collection_refs"].append(broken_ref)
                result["total_broken"] += 1

                if suggestions:
                    best_match = suggestions[0]
                    print(f"LOG:    Best match: '{best_match['name']}' ({best_match['similarity']*100:.0f}%)", flush=True)
            else:
                print(f"LOG: ✓ Collection OK: '{collection_name}'", flush=True)

    if result["total_broken"] > 0:
        print(f"LOG: Found {result['total_broken']} broken collection reference(s) in {blend_file.name}", flush=True)
    else:
        print(f"LOG: All collection references are valid in {blend_file.name}", flush=True)

    return result


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Validate that linked collection names exist in their source files"
        )
        parser.add_argument('--blend-file', required=True, help='Path to .blend file to check')

        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        result = validate_collection_names_in_file(Path(args.blend_file))

        output_json(result)
        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            file="",
            file_name="",
            broken_collection_refs=[],
            total_broken=0
        )
        output_json(error_result)
        sys.exit(1)
