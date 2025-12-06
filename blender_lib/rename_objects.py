"""Blender script to rename objects and collections and update linked references."""

import bpy
import json
import sys
import argparse
import os
from pathlib import Path

# Add parent directory to path so we can import core module
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_scanner import find_blend_files


def rename_local_items(item_names, find_text, replace_text, dry_run=True):
    """Rename LOCAL objects and collections (not linked) with find/replace.

    Args:
        item_names: List of object/collection names to rename
        find_text: Text to find in names
        replace_text: Text to replace with
        dry_run: If True, don't actually rename, just preview

    Returns:
        Dictionary with rename operations
    """
    result = {
        "renamed": [],
        "errors": [],
        "warnings": []
    }

    if not find_text:
        result["errors"].append("Find text cannot be empty")
        return result

    # Process objects (only local, not linked)
    for obj in bpy.data.objects:
        # Skip linked objects
        if obj.library is not None:
            continue

        if obj.name in item_names:
            if find_text in obj.name:
                new_name = obj.name.replace(find_text, replace_text)

                # Check if new name already exists
                if new_name != obj.name and new_name in bpy.data.objects:
                    result["warnings"].append(
                        f"Object '{new_name}' already exists, skipping '{obj.name}'"
                    )
                    continue

                result["renamed"].append({
                    "type": "object",
                    "old_name": obj.name,
                    "new_name": new_name
                })

                # Actually rename if not dry run
                if not dry_run:
                    obj.name = new_name
                    # Also rename data block if it has the same name
                    if obj.data and obj.data.name == obj.name.replace(replace_text, find_text):
                        obj.data.name = new_name
            else:
                result["warnings"].append(
                    f"Find text '{find_text}' not found in object '{obj.name}'"
                )

    # Process collections (only local, not linked)
    for col in bpy.data.collections:
        # Skip linked collections
        if col.library is not None:
            continue

        if col.name in item_names:
            if find_text in col.name:
                new_name = col.name.replace(find_text, replace_text)

                # Check if new name already exists
                if new_name != col.name and new_name in bpy.data.collections:
                    result["warnings"].append(
                        f"Collection '{new_name}' already exists, skipping '{col.name}'"
                    )
                    continue

                result["renamed"].append({
                    "type": "collection",
                    "old_name": col.name,
                    "new_name": new_name
                })

                # Actually rename if not dry run
                if not dry_run:
                    col.name = new_name
            else:
                result["warnings"].append(
                    f"Find text '{find_text}' not found in collection '{col.name}'"
                )

    return result


def remap_linked_references(lib_path, renamed_items, root_dir, dry_run=True):
    """Update linked references in other .blend files.

    Args:
        lib_path: Absolute path to the library .blend file
        renamed_items: List of dicts with 'type', 'old_name', 'new_name'
        root_dir: Project root directory to search for .blend files
        dry_run: If True, don't actually save changes

    Returns:
        Dictionary with updated files count and details
    """
    result = {
        "updated_files": [],
        "errors": [],
        "warnings": []
    }

    lib_abs = os.path.abspath(lib_path)

    # Find all .blend files in project
    all_blend_files = [str(f) for f in find_blend_files(Path(root_dir))]

    for blend_file in all_blend_files:
        # Skip the library file itself
        if os.path.abspath(blend_file) == lib_abs:
            continue

        # Open the file
        try:
            bpy.ops.wm.open_mainfile(filepath=blend_file)
        except Exception as e:
            result["warnings"].append(f"Could not open {blend_file}: {e}")
            continue

        file_changed = False

        # Check if this file uses our library
        matching_libs = [
            lib for lib in bpy.data.libraries
            if os.path.abspath(bpy.path.abspath(lib.filepath)) == lib_abs
        ]

        if not matching_libs:
            continue  # This file doesn't use our library

        # Process each renamed item
        for item in renamed_items:
            id_type = item["type"]
            old_name = item["old_name"]
            new_name = item["new_name"]

            for lib in matching_libs:
                # Find old linked IDs
                if id_type == "object":
                    old_ids = [obj for obj in bpy.data.objects
                              if obj.library is lib and obj.name == old_name]
                else:  # collection
                    old_ids = [col for col in bpy.data.collections
                              if col.library is lib and col.name == old_name]

                if not old_ids:
                    continue

                # Mark that this file will change
                file_changed = True

                # In dry-run mode, don't actually try to link and remap
                if dry_run:
                    continue

                # Execute mode: actually perform the remap
                # Link the new ID from library
                try:
                    with bpy.data.libraries.load(lib_abs, link=True) as (data_from, data_to):
                        if id_type == "object":
                            if new_name in data_from.objects:
                                data_to.objects = [new_name]
                        else:  # collection
                            if new_name in data_from.collections:
                                data_to.collections = [new_name]
                except Exception as e:
                    result["warnings"].append(f"Could not link {new_name} from library: {e}")
                    continue

                # Find the newly linked ID
                if id_type == "object":
                    new_id = next((obj for obj in bpy.data.objects
                                  if obj.name == new_name and obj.library is lib), None)
                else:
                    new_id = next((col for col in bpy.data.collections
                                  if col.name == new_name and col.library is lib), None)

                if new_id is None:
                    result["warnings"].append(f"Could not find newly linked {id_type} '{new_name}'")
                    continue

                # Remap old IDs to new ID
                for old_id in old_ids:
                    old_id.user_remap(new_id)

                    # Remove old ID
                    if id_type == "object":
                        bpy.data.objects.remove(old_id)
                    else:
                        bpy.data.collections.remove(old_id)

        if file_changed:
            result["updated_files"].append(blend_file)
            if not dry_run:
                try:
                    bpy.ops.wm.save_mainfile()
                except Exception as e:
                    result["errors"].append(f"Could not save {blend_file}: {e}")

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--blend-file', required=True, help='Path to .blend file')
        parser.add_argument('--project-root', required=True, help='Path to project root directory')
        parser.add_argument('--item-names', required=True, help='Comma-separated list of item names')
        parser.add_argument('--find', required=True, help='Text to find')
        parser.add_argument('--replace', required=True, help='Text to replace with')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Load the blend file
        bpy.ops.wm.open_mainfile(filepath=args.blend_file)

        # Parse item names
        item_names = [name.strip() for name in args.item_names.split(',') if name.strip()]

        # Perform local rename
        dry_run = args.dry_run == 'true'
        result = rename_local_items(item_names, args.find, args.replace, dry_run)

        # Save library file if not dry run and changes were made
        if not dry_run and result["renamed"]:
            bpy.ops.wm.save_mainfile()
            result["saved"] = True
        else:
            result["saved"] = False

        # Update linked references in other files
        if result["renamed"]:
            remap_result = remap_linked_references(
                args.blend_file,
                result["renamed"],
                args.project_root,
                dry_run
            )

            # Merge results
            result["updated_files"] = remap_result["updated_files"]
            result["updated_files_count"] = len(remap_result["updated_files"])
            result["warnings"].extend(remap_result["warnings"])
            result["errors"].extend(remap_result["errors"])
        else:
            result["updated_files"] = []
            result["updated_files_count"] = 0

        # Output as JSON
        print("JSON_OUTPUT:" + json.dumps(result, indent=2))

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "renamed": [],
            "errors": [str(e)],
            "warnings": [],
            "updated_files": [],
            "updated_files_count": 0
        }
        print("JSON_OUTPUT:" + json.dumps(error_result, indent=2))
        sys.exit(1)
