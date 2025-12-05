"""Blender script to list objects and collections in a .blend file."""

import bpy
import json
import sys
import argparse


def list_objects_and_collections():
    """List all objects and collections in the current blend file.

    Returns:
        Dictionary with objects and collections
    """
    result = {
        "objects": [],
        "collections": []
    }

    # List all objects
    for obj in bpy.data.objects:
        result["objects"].append({
            "name": obj.name,
            "type": obj.type,
            "collections": [col.name for col in obj.users_collection]
        })

    # List all collections
    for col in bpy.data.collections:
        result["collections"].append({
            "name": col.name,
            "objects_count": len(col.objects),
            "children_count": len(col.children)
        })

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--blend-file', required=True, help='Path to .blend file')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Load the blend file
        bpy.ops.wm.open_mainfile(filepath=args.blend_file)

        # Get objects and collections
        result = list_objects_and_collections()

        # Output as JSON
        print("JSON_OUTPUT:" + json.dumps(result, indent=2))

        sys.exit(0)

    except Exception as e:
        error_result = {
            "error": str(e),
            "objects": [],
            "collections": []
        }
        print("JSON_OUTPUT:" + json.dumps(error_result, indent=2))
        sys.exit(1)
