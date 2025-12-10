"""Blender script to link objects/collections from one .blend file to another."""

import bpy
import sys
import argparse
from pathlib import Path
import os

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def find_layer_collection(layer_collection, collection_name):
    """Recursively find a layer collection by name."""
    if layer_collection.name == collection_name:
        return layer_collection
    for child in layer_collection.children:
        found = find_layer_collection(child, collection_name)
        if found:
            return found
    return None


def link_items(source_file, target_scene, item_names, item_types, target_collection_name, link_mode='instance', dry_run=True, hide_viewport=False):
    """Link objects/collections from source file into target scene.

    Args:
        source_file: Path to source .blend file
        target_scene: Name of scene to link into
        item_names: List of item names to link
        item_types: List of types ('object' or 'collection') for each item
        target_collection_name: Name of collection to create/use in target
        link_mode: 'instance' (Blender default) or 'individual' (separate links)
        dry_run: If True, only preview without making changes
        hide_viewport: If True, hide the target collection (eye icon) in outliner

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

        # Check for naming conflicts with target collection (only if collection name is provided)
        if target_collection_name and target_collection_name in item_names:
            result["errors"].append(
                f"Target collection name '{target_collection_name}' conflicts with item being linked. "
                f"Please choose a different collection name."
            )
            return result

        # Check if target collection exists (only if collection name is provided)
        target_collection_exists = target_collection_name and target_collection_name in bpy.data.collections

        if dry_run:
            # Preview mode - check what would happen

            if link_mode == 'instance':
                # Instance mode: Only ONE item (collection or object) allowed
                total_items = len(collections_to_link) + len(objects_to_link)
                if total_items != 1:
                    result["errors"].append("Instance mode requires exactly ONE collection or object to be selected")
                    return result

                # Handle collection instance
                if collections_to_link:
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

                # Handle object instance
                elif objects_to_link:
                    obj_name = objects_to_link[0]
                    instance_name = f"{obj_name}"

                    # Load source file to check object
                    with bpy.data.libraries.load(source_file, link=False) as (data_from, data_to):
                        if obj_name in data_from.objects:
                            # Check if object already linked
                            if obj_name in bpy.data.objects:
                                result["errors"].append(f"Object '{obj_name}' already exists in target file")
                            # Check if instance object already exists
                            elif instance_name in bpy.data.objects:
                                result["errors"].append(f"Object instance '{instance_name}' already exists in target file")
                            else:
                                result["linked_items"].append({
                                    "name": obj_name,
                                    "type": "object_instance",
                                    "status": "will_link"
                                })
                        else:
                            result["errors"].append(f"Object '{obj_name}' not found in source file")

                # Check target collection (only if collection name is provided)
                if target_collection_name:
                    if target_collection_name not in bpy.data.collections:
                        result["target_collection_status"] = "will_create"
                    else:
                        result["target_collection_status"] = "exists"
                else:
                    result["target_collection_status"] = "not_needed"

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

                # Check target collection (only if collection name is provided)
                if target_collection_name:
                    if not target_collection_exists:
                        result["target_collection_status"] = "will_create"
                    else:
                        result["target_collection_status"] = "exists"
                else:
                    result["target_collection_status"] = "not_needed"

                result["success"] = len(result["errors"]) == 0

        else:
            # Execute mode - actually link the items

            # Stop if there are pre-existing errors
            if result["errors"]:
                return result

            if link_mode == 'instance':
                # Instance mode: Link collection or object as instance
                # This mode only supports linking ONE item (collection or object)
                total_items = len(collections_to_link) + len(objects_to_link)
                if total_items != 1:
                    result["errors"].append("Instance mode requires exactly ONE collection or object to be selected")
                    return result

                # Create or get target collection (or use scene collection if no name provided)
                if target_collection_name:
                    if target_collection_name not in bpy.data.collections:
                        target_collection = bpy.data.collections.new(target_collection_name)
                        bpy.context.scene.collection.children.link(target_collection)
                        result["target_collection_status"] = "created"
                    else:
                        target_collection = bpy.data.collections[target_collection_name]
                        result["target_collection_status"] = "existed"
                else:
                    # No collection specified - use scene's main collection
                    target_collection = bpy.context.scene.collection
                    result["target_collection_status"] = "not_needed"

                # Handle collection instance
                if collections_to_link:
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

                    # Create a collection instance (Empty object that instances the collection)
                    empty = bpy.data.objects.new(instance_name, None)
                    empty.instance_type = 'COLLECTION'
                    empty.instance_collection = linked_collection

                    # Add the empty to the target collection
                    target_collection.objects.link(empty)

                    # Hide the empty object if requested and no collection name
                    if hide_viewport and not target_collection_name:
                        empty.hide_set(True)

                    result["linked_items"].append({
                        "name": col_name,
                        "type": "collection_instance",
                        "status": "linked"
                    })

                # Handle object instance
                elif objects_to_link:
                    obj_name = objects_to_link[0]
                    instance_name = f"{obj_name}"

                    # Check for duplicates before linking
                    if obj_name in bpy.data.objects:
                        result["errors"].append(f"Object '{obj_name}' already exists in target file")
                        return result

                    # Link the object
                    with bpy.data.libraries.load(source_file, link=True) as (data_from, data_to):
                        if obj_name in data_from.objects:
                            data_to.objects = [obj for obj in data_from.objects if obj == obj_name]
                        else:
                            result["errors"].append(f"Object '{obj_name}' not found in source file")
                            return result

                    # Get the linked object
                    linked_object = bpy.data.objects.get(obj_name)
                    if not linked_object:
                        result["errors"].append(f"Failed to link object '{obj_name}'")
                        return result

                    # Add the linked object to the target collection
                    target_collection.objects.link(linked_object)

                    # Hide the object if requested and no collection name
                    if hide_viewport and not target_collection_name:
                        linked_object.hide_set(True)

                    result["linked_items"].append({
                        "name": obj_name,
                        "type": "object_instance",
                        "status": "linked"
                    })

                # Hide the target collection (eye icon) if requested (only if we created a collection)
                if hide_viewport and target_collection_name:
                    # Access the layer collection to set the eye icon visibility
                    layer_collection = bpy.context.view_layer.layer_collection
                    target_layer_col = find_layer_collection(layer_collection, target_collection_name)
                    if target_layer_col:
                        target_layer_col.hide_viewport = True

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

                # Create or get target collection (or use scene collection if no name provided)
                if target_collection_name:
                    if target_collection_name not in bpy.data.collections:
                        target_collection = bpy.data.collections.new(target_collection_name)
                        bpy.context.scene.collection.children.link(target_collection)
                        result["target_collection_status"] = "created"
                    else:
                        target_collection = bpy.data.collections[target_collection_name]
                        result["target_collection_status"] = "existed"
                else:
                    # No collection specified - use scene's main collection
                    target_collection = bpy.context.scene.collection
                    result["target_collection_status"] = "not_needed"

                # Hide the target collection (eye icon) if requested (only if we created a collection)
                if hide_viewport and target_collection_name:
                    # Access the layer collection to set the eye icon visibility
                    layer_collection = bpy.context.view_layer.layer_collection
                    target_layer_col = find_layer_collection(layer_collection, target_collection_name)
                    if target_layer_col:
                        target_layer_col.hide_viewport = True

                # Add linked objects directly to target collection
                for obj in linked_objects:
                    if obj.name not in target_collection.objects:
                        target_collection.objects.link(obj)

                        # Hide the object if requested and no collection name
                        if hide_viewport and not target_collection_name:
                            obj.hide_set(True)

                        result["linked_items"].append({
                            "name": obj.name,
                            "type": "object",
                            "status": "linked"
                        })

                # Add linked collections directly to target collection
                for col in linked_collections:
                    if col.name not in [c.name for c in target_collection.children]:
                        target_collection.children.link(col)

                        # Hide the collection if requested and no collection name
                        if hide_viewport and not target_collection_name:
                            # Find the layer collection and hide it (eye icon)
                            layer_collection = bpy.context.view_layer.layer_collection
                            col_layer = find_layer_collection(layer_collection, col.name)
                            if col_layer:
                                col_layer.hide_viewport = True

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
        parser.add_argument('--target-collection', default='', help='Target collection name (empty for scene collection)')
        parser.add_argument('--link-mode', default='instance', help='instance or individual')
        parser.add_argument('--dry-run', default='true', help='true or false')
        parser.add_argument('--hide-viewport', default='false', help='true or false')

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

        # Parse hide viewport flag
        hide_viewport = args.hide_viewport.lower() == 'true'

        # Execute link operation
        result = link_items(
            args.source_file,
            args.target_scene,
            item_names,
            item_types,
            args.target_collection,
            link_mode,
            dry_run,
            hide_viewport
        )

        # Output as JSON
        output_json(result)

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        error_result = create_error_result(
            str(e),
            linked_items=[]
        )
        output_json(error_result)
        sys.exit(1)
