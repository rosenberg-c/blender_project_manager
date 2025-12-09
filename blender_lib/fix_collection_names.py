"""Blender script to remap broken collection name references to new names.

This script updates collection references when a collection has been renamed in the
source library file, handling both instance mode and individual mode linking.
"""

import bpy
import sys
import argparse
import os
import json
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def remap_instance_collection(
    library_path: str,
    old_collection_name: str,
    new_collection_name: str,
    instance_object_name: str
) -> Dict:
    """Remap a collection that's linked in instance mode.

    Instance mode: Collection is instanced via an Empty object with instance_collection property.

    Args:
        library_path: Path to the library file
        old_collection_name: Current (broken) collection name
        new_collection_name: New collection name to link
        instance_object_name: Name of the Empty object that instances the collection

    Returns:
        Dictionary with remapping result
    """
    result = {
        "success": False,
        "old_name": old_collection_name,
        "new_name": new_collection_name,
        "mode": "instance",
        "errors": []
    }

    try:
        # Find the Empty object that instances this collection
        empty = bpy.data.objects.get(instance_object_name)
        if not empty:
            result["errors"].append(f"Instance object '{instance_object_name}' not found")
            return result

        if empty.instance_type != 'COLLECTION':
            result["errors"].append(f"Object '{instance_object_name}' is not a collection instance")
            return result

        # Get the old collection reference
        old_collection = bpy.data.collections.get(old_collection_name)

        # Link the new collection from the library
        print(f"LOG: Linking new collection '{new_collection_name}' from library", flush=True)
        with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
            if new_collection_name in data_from.collections:
                data_to.collections = [col for col in data_from.collections if col == new_collection_name]
            else:
                result["errors"].append(f"Collection '{new_collection_name}' not found in library")
                return result

        # Get the newly linked collection
        new_collection = bpy.data.collections.get(new_collection_name)
        if not new_collection:
            result["errors"].append(f"Failed to link collection '{new_collection_name}'")
            return result

        # Update the Empty's instance_collection to point to the new collection
        print(f"LOG: Updating instance object '{instance_object_name}' to use new collection", flush=True)
        empty.instance_collection = new_collection

        # Remove the old collection if it exists and has no users
        if old_collection:
            # Check if the old collection is still being used elsewhere
            if old_collection.users == 0:
                print(f"LOG: Removing unused old collection '{old_collection_name}'", flush=True)
                bpy.data.collections.remove(old_collection)
            else:
                print(f"LOG: Old collection '{old_collection_name}' still has {old_collection.users} user(s), keeping it", flush=True)

        result["success"] = True
        print(f"LOG: ✓ Successfully remapped instance collection from '{old_collection_name}' to '{new_collection_name}'", flush=True)

    except Exception as e:
        result["errors"].append(f"Error remapping instance collection: {str(e)}")
        print(f"LOG: ERROR: {str(e)}", flush=True)

    return result


def remap_individual_collection(
    library_path: str,
    old_collection_name: str,
    new_collection_name: str
) -> Dict:
    """Remap a collection that's linked in individual mode.

    Individual mode: Collection is directly linked into the scene hierarchy.

    Args:
        library_path: Path to the library file
        old_collection_name: Current (broken) collection name
        new_collection_name: New collection name to link

    Returns:
        Dictionary with remapping result
    """
    result = {
        "success": False,
        "old_name": old_collection_name,
        "new_name": new_collection_name,
        "mode": "individual",
        "errors": []
    }

    try:
        # Find the old collection
        old_collection = bpy.data.collections.get(old_collection_name)
        if not old_collection:
            result["errors"].append(f"Collection '{old_collection_name}' not found")
            return result

        # Find parent collections that contain the old collection
        parent_collections = []
        for col in bpy.data.collections:
            if old_collection.name in [c.name for c in col.children]:
                parent_collections.append(col)

        print(f"LOG: Found {len(parent_collections)} parent collection(s) for '{old_collection_name}'", flush=True)

        # Link the new collection from the library
        print(f"LOG: Linking new collection '{new_collection_name}' from library", flush=True)
        with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
            if new_collection_name in data_from.collections:
                data_to.collections = [col for col in data_from.collections if col == new_collection_name]
            else:
                result["errors"].append(f"Collection '{new_collection_name}' not found in library")
                return result

        # Get the newly linked collection
        new_collection = bpy.data.collections.get(new_collection_name)
        if not new_collection:
            result["errors"].append(f"Failed to link collection '{new_collection_name}'")
            return result

        # Add the new collection to all parent collections where the old one was
        for parent_col in parent_collections:
            if new_collection.name not in [c.name for c in parent_col.children]:
                print(f"LOG: Adding '{new_collection_name}' to parent collection '{parent_col.name}'", flush=True)
                parent_col.children.link(new_collection)

        # Remove the old collection from parent collections
        for parent_col in parent_collections:
            if old_collection.name in [c.name for c in parent_col.children]:
                print(f"LOG: Removing '{old_collection_name}' from parent collection '{parent_col.name}'", flush=True)
                parent_col.children.unlink(old_collection)

        # Remove the old collection if it has no users
        if old_collection.users == 0:
            print(f"LOG: Removing unused old collection '{old_collection_name}'", flush=True)
            bpy.data.collections.remove(old_collection)
        else:
            print(f"LOG: Old collection '{old_collection_name}' still has {old_collection.users} user(s), keeping it", flush=True)

        result["success"] = True
        print(f"LOG: ✓ Successfully remapped individual collection from '{old_collection_name}' to '{new_collection_name}'", flush=True)

    except Exception as e:
        result["errors"].append(f"Error remapping individual collection: {str(e)}")
        print(f"LOG: ERROR: {str(e)}", flush=True)

    return result


def remap_collection_references(blend_file: Path, remappings: List[Dict]) -> Dict:
    """Remap multiple collection references in a blend file.

    Args:
        blend_file: Path to the .blend file to modify
        remappings: List of remapping instructions, each containing:
            - library_name: Name of the library
            - library_filepath: Path to the library file
            - old_collection_name: Current collection name
            - new_collection_name: New collection name
            - link_mode: "instance" or "individual"
            - instance_object_name: (optional) Name of instance object for instance mode

    Returns:
        Dictionary with remapping results
    """
    result = {
        "file": str(blend_file),
        "file_name": blend_file.name,
        "remapped_collections": [],
        "failed_remappings": [],
        "total_remapped": 0,
        "total_failed": 0
    }

    try:
        bpy.ops.wm.open_mainfile(filepath=str(blend_file))
    except Exception as e:
        result["error"] = f"Could not open file: {str(e)}"
        return result

    print(f"LOG: Processing {len(remappings)} collection remapping(s) in {blend_file.name}", flush=True)

    # Process each remapping
    for remap in remappings:
        library_filepath = remap.get("library_filepath")
        old_name = remap.get("old_collection_name")
        new_name = remap.get("new_collection_name")
        link_mode = remap.get("link_mode", "individual")
        instance_object_name = remap.get("instance_object_name")

        # Resolve library path to absolute
        library_path = bpy.path.abspath(library_filepath)

        print(f"LOG: Remapping '{old_name}' → '{new_name}' (mode: {link_mode})", flush=True)

        # Perform remapping based on link mode
        if link_mode == "instance":
            if not instance_object_name:
                result["failed_remappings"].append({
                    "old_name": old_name,
                    "new_name": new_name,
                    "error": "Instance mode requires instance_object_name"
                })
                result["total_failed"] += 1
                continue

            remap_result = remap_instance_collection(
                library_path,
                old_name,
                new_name,
                instance_object_name
            )
        else:
            remap_result = remap_individual_collection(
                library_path,
                old_name,
                new_name
            )

        # Track results
        if remap_result["success"]:
            result["remapped_collections"].append({
                "old_name": old_name,
                "new_name": new_name,
                "mode": link_mode
            })
            result["total_remapped"] += 1
        else:
            result["failed_remappings"].append({
                "old_name": old_name,
                "new_name": new_name,
                "errors": remap_result["errors"]
            })
            result["total_failed"] += 1

    # Save the file if any remappings succeeded
    if result["total_remapped"] > 0:
        print(f"LOG: Saving file with {result['total_remapped']} remapped collection(s)", flush=True)
        bpy.ops.wm.save_mainfile()
        print(f"LOG: ✓ File saved successfully", flush=True)
    else:
        print(f"LOG: No successful remappings, file not saved", flush=True)

    return result


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Remap collection name references in a .blend file"
        )
        parser.add_argument('--blend-file', required=True, help='Path to .blend file to modify')
        parser.add_argument('--remappings', required=True, help='JSON string with remapping instructions')

        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Parse remappings JSON
        remappings = json.loads(args.remappings)

        result = remap_collection_references(Path(args.blend_file), remappings)

        output_json(result)
        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            file="",
            file_name="",
            remapped_collections=[],
            failed_remappings=[],
            total_remapped=0,
            total_failed=0
        )
        output_json(error_result)
        sys.exit(1)
