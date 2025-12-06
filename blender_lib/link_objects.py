"""Blender script to link objects/collections from one .blend file to another."""

import bpy
import json
import sys
import argparse
from pathlib import Path


def link_items(source_file, target_scene, item_names, item_types, target_collection_name, link_mode='instance', dry_run=True):
    """Link objects/collections from source file into target scene.

    Args:
        source_file: Path to source .blend file
        target_scene: Name of scene to link into
        item_names: List of item names to link
        item_types: List of types ('object' or 'collection') for each item
        target_collection_name: Name of collection to create/use in target
        link_mode: 'instance' (Blender default) or 'individual' (separate links)
        dry_run: If True, only preview without making changes

    Returns:
        Dictionary with operation results
    """
    result = {
        "success": False,
        "linked_items": [],
        "errors": [],
        "warnings": [],
        "target_scene": target_scene,
        "target_collection": target_collection_name,
        "dry_run": dry_run
    }

    try:
        # Verify target scene exists
        if target_scene not in bpy.data.scenes:
            result["errors"].append(f"Scene '{target_scene}' not found in target file")
            return result

        # Set target scene as active
        bpy.context.window.scene = bpy.data.scenes[target_scene]

        # Verify source file exists
        source_path = Path(source_file)
        if not source_path.exists():
            result["errors"].append(f"Source file not found: {source_file}")
            return result

        # Separate objects and collections
        objects_to_link = []
        collections_to_link = []

        for item_name, item_type in zip(item_names, item_types):
            if item_type == 'object':
                objects_to_link.append(item_name)
            elif item_type == 'collection':
                collections_to_link.append(item_name)

        # Check for naming conflicts with target collection
        if target_collection_name in item_names:
            result["errors"].append(
                f"Target collection name '{target_collection_name}' conflicts with item being linked. "
                f"Please choose a different collection name."
            )
            return result

        # Check if target collection exists
        target_collection_exists = target_collection_name in bpy.data.collections

        if dry_run:
            # Preview mode - check what would happen

            if link_mode == 'instance':
                # Instance mode: Only ONE collection allowed
                if len(collections_to_link) != 1 or objects_to_link:
                    result["errors"].append("Instance mode requires exactly one collection to be selected")
                    return result

                col_name = collections_to_link[0]
                instance_name = f"{col_name}"

                # Load source file to check collection
                with bpy.data.libraries.load(source_file, link=False) as (data_from, data_to):
                    if col_name in data_from.collections:
                        # Check if collection already linked
                        if col_name in bpy.data.collections:
                            result["errors"].append(f"Collection '{col_name}' already exists in target file")
                        # Check if instance object already exists
                        elif instance_name in bpy.data.objects:
                            result["errors"].append(f"Collection instance '{instance_name}' already exists in target file")
                        else:
                            result["linked_items"].append({
                                "name": col_name,
                                "type": "collection_instance",
                                "status": "will_link"
                            })
                    else:
                        result["errors"].append(f"Collection '{col_name}' not found in source file")

                # Check target collection
                if target_collection_name not in bpy.data.collections:
                    result["target_collection_status"] = "will_create"
                else:
                    result["target_collection_status"] = "exists"

                result["success"] = len(result["errors"]) == 0

            else:
                # Individual mode: Check all items
                # Load source file to check what's available
                with bpy.data.libraries.load(source_file, link=False) as (data_from, data_to):
                    # Check objects
                    for obj_name in objects_to_link:
                        if obj_name in data_from.objects:
                            # Check if already exists in target
                            if obj_name in bpy.data.objects:
                                result["errors"].append(f"Object '{obj_name}' already exists in target file")
                            else:
                                result["linked_items"].append({
                                    "name": obj_name,
                                    "type": "object",
                                    "status": "will_link"
                                })
                        else:
                            result["warnings"].append(f"Object '{obj_name}' not found in source file")

                    # Check collections
                    for col_name in collections_to_link:
                        if col_name in data_from.collections:
                            # Check if already exists in target
                            if col_name in bpy.data.collections:
                                result["errors"].append(f"Collection '{col_name}' already exists in target file")
                            else:
                                result["linked_items"].append({
                                    "name": col_name,
                                    "type": "collection",
                                    "status": "will_link"
                                })
                        else:
                            result["warnings"].append(f"Collection '{col_name}' not found in source file")

                # Check target collection
                if not target_collection_exists:
                    result["target_collection_status"] = "will_create"
                else:
                    result["target_collection_status"] = "exists"

                result["success"] = len(result["errors"]) == 0

        else:
            # Execute mode - actually link the items

            # Stop if there are pre-existing errors
            if result["errors"]:
                return result

            if link_mode == 'instance':
                # Instance mode: Link collection as collection instance (Blender default)
                # This mode only supports linking ONE collection
                if len(collections_to_link) != 1 or objects_to_link:
                    result["errors"].append("Instance mode requires exactly one collection to be selected")
                    return result

                col_name = collections_to_link[0]
                instance_name = f"{col_name}"

                # Check for duplicates before linking
                if col_name in bpy.data.collections:
                    result["errors"].append(f"Collection '{col_name}' already exists in target file")
                    return result

                if instance_name in bpy.data.objects:
                    result["errors"].append(f"Collection instance '{instance_name}' already exists in target file")
                    return result

                # Link the collection
                with bpy.data.libraries.load(source_file, link=True) as (data_from, data_to):
                    if col_name in data_from.collections:
                        data_to.collections = [col for col in data_from.collections if col == col_name]
                    else:
                        result["errors"].append(f"Collection '{col_name}' not found in source file")
                        return result

                # Get the linked collection
                linked_collection = bpy.data.collections.get(col_name)
                if not linked_collection:
                    result["errors"].append(f"Failed to link collection '{col_name}'")
                    return result

                # Create or get target collection
                if target_collection_name not in bpy.data.collections:
                    target_collection = bpy.data.collections.new(target_collection_name)
                    bpy.context.scene.collection.children.link(target_collection)
                    result["target_collection_status"] = "created"
                else:
                    target_collection = bpy.data.collections[target_collection_name]
                    result["target_collection_status"] = "existed"

                # Create a collection instance (Empty object that instances the collection)
                # This creates the orange "instance" behavior in Blender
                instance_name = f"{col_name}"

                # Create an empty object
                empty = bpy.data.objects.new(instance_name, None)

                # Set it to instance the linked collection
                empty.instance_type = 'COLLECTION'
                empty.instance_collection = linked_collection

                # Add the empty to the target collection (not scene root)
                target_collection.objects.link(empty)

                result["linked_items"].append({
                    "name": col_name,
                    "type": "collection_instance",
                    "status": "linked"
                })

                # Save the file
                bpy.ops.wm.save_mainfile()
                result["success"] = True

            else:
                # Individual mode: Link each item separately into a target collection
                linked_objects = []
                linked_collections = []

                with bpy.data.libraries.load(source_file, link=True) as (data_from, data_to):
                    # Link objects
                    for obj_name in objects_to_link:
                        if obj_name in data_from.objects:
                            # Check for duplicates
                            if obj_name in bpy.data.objects:
                                result["errors"].append(f"Object '{obj_name}' already exists in target file")
                            else:
                                data_to.objects = [obj for obj in data_from.objects if obj == obj_name]
                        else:
                            result["warnings"].append(f"Object '{obj_name}' not found in source file")

                    # Link collections
                    for col_name in collections_to_link:
                        if col_name in data_from.collections:
                            # Check for duplicates
                            if col_name in bpy.data.collections:
                                result["errors"].append(f"Collection '{col_name}' already exists in target file")
                            else:
                                data_to.collections = [col for col in data_from.collections if col == col_name]
                        else:
                            result["warnings"].append(f"Collection '{col_name}' not found in source file")

                # If there were duplicate errors, don't continue
                if result["errors"]:
                    return result

                # After loading, linked items are in bpy.data but need to be added to scene
                linked_objects = [obj for obj in bpy.data.objects if obj.name in objects_to_link and obj.library]
                linked_collections = [col for col in bpy.data.collections if col.name in collections_to_link and col.library]

                # Create or get target collection
                if target_collection_name not in bpy.data.collections:
                    target_collection = bpy.data.collections.new(target_collection_name)
                    bpy.context.scene.collection.children.link(target_collection)
                    result["target_collection_status"] = "created"
                else:
                    target_collection = bpy.data.collections[target_collection_name]
                    result["target_collection_status"] = "existed"

                # Add linked objects directly to target collection
                for obj in linked_objects:
                    if obj.name not in target_collection.objects:
                        target_collection.objects.link(obj)
                        result["linked_items"].append({
                            "name": obj.name,
                            "type": "object",
                            "status": "linked"
                        })

                # Add linked collections directly to target collection
                for col in linked_collections:
                    if col.name not in [c.name for c in target_collection.children]:
                        target_collection.children.link(col)
                        result["linked_items"].append({
                            "name": col.name,
                            "type": "collection",
                            "status": "linked"
                        })

                # Save the file
                bpy.ops.wm.save_mainfile()

                result["success"] = len(result["errors"]) == 0

    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        result["success"] = False

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--target-file', required=True, help='Path to target .blend file')
        parser.add_argument('--target-scene', required=True, help='Scene name in target file')
        parser.add_argument('--source-file', required=True, help='Path to source .blend file')
        parser.add_argument('--item-names', required=True, help='Comma-separated list of item names')
        parser.add_argument('--item-types', required=True, help='Comma-separated list of item types')
        parser.add_argument('--target-collection', required=True, help='Target collection name')
        parser.add_argument('--link-mode', default='instance', help='instance or individual')
        parser.add_argument('--dry-run', default='true', help='true or false')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Load the target blend file
        bpy.ops.wm.open_mainfile(filepath=args.target_file)

        # Parse item names and types
        item_names = [name.strip() for name in args.item_names.split(',') if name.strip()]
        item_types = [t.strip() for t in args.item_types.split(',') if t.strip()]

        # Validate
        if len(item_names) != len(item_types):
            raise ValueError("Number of item names must match number of item types")

        # Parse dry-run flag
        dry_run = args.dry_run.lower() == 'true'

        # Parse link mode
        link_mode = args.link_mode.lower()

        # Execute link operation
        result = link_items(
            args.source_file,
            args.target_scene,
            item_names,
            item_types,
            args.target_collection,
            link_mode,
            dry_run
        )

        # Output as JSON
        print("JSON_OUTPUT:" + json.dumps(result, indent=2))

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "linked_items": [],
            "errors": [str(e)],
            "warnings": []
        }
        print("JSON_OUTPUT:" + json.dumps(error_result, indent=2))
        sys.exit(1)
