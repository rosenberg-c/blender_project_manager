"""Blender script to list objects and collections in a .blend file."""

import bpy
import sys
import argparse

# Import shared utilities
import os
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def list_objects_and_collections(scene_name=None):
    """List all objects, collections, and materials in the current blend file.

    Args:
        scene_name: Optional scene name to filter objects by. If None or "All", lists all objects.

    Returns:
        Dictionary with objects, collections, and materials
    """
    result = {
        "objects": [],
        "collections": [],
        "materials": []
    }

    # Get scene filter
    target_scene = None
    if scene_name and scene_name != "All":
        target_scene = bpy.data.scenes.get(scene_name)
        if not target_scene:
            # Scene not found, return empty
            return result

    # List objects
    if target_scene:
        # List only objects in the specified scene
        for obj in target_scene.objects:
            result["objects"].append({
                "name": obj.name,
                "type": obj.type,
                "collections": [col.name for col in obj.users_collection]
            })
    else:
        # List all objects
        for obj in bpy.data.objects:
            result["objects"].append({
                "name": obj.name,
                "type": obj.type,
                "collections": [col.name for col in obj.users_collection]
            })

    # List collections (always all collections, not scene-specific)
    for col in bpy.data.collections:
        result["collections"].append({
            "name": col.name,
            "objects_count": len(col.objects),
            "children_count": len(col.children)
        })

    # List materials (always all materials)
    for mat in bpy.data.materials:
        result["materials"].append({
            "name": mat.name,
            "use_nodes": mat.use_nodes,
            "users": mat.users
        })

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--blend-file', required=True, help='Path to .blend file')
        parser.add_argument('--scene', required=False, default=None, help='Scene name to filter by')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Load the blend file
        bpy.ops.wm.open_mainfile(filepath=args.blend_file)

        # Get objects and collections
        result = list_objects_and_collections(scene_name=args.scene)

        # Output as JSON
        output_json(create_success_result(**result))

        sys.exit(0)

    except Exception as e:
        output_json(create_error_result(str(e), objects=[], collections=[], materials=[]))
        sys.exit(1)
