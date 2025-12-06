"""Blender script to list all scenes in a .blend file."""

import bpy
import json
import sys
import argparse


def list_scenes():
    """List all scenes in the current blend file.

    Returns:
        Dictionary with scenes list
    """
    result = {
        "scenes": []
    }

    # Get active scene if available
    active_scene = None
    if bpy.context.scene:
        active_scene = bpy.context.scene.name

    # List all scenes
    for scene in bpy.data.scenes:
        result["scenes"].append({
            "name": scene.name,
            "is_active": scene.name == active_scene
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

        # Get scenes
        result = list_scenes()

        # Output as JSON
        print("JSON_OUTPUT:" + json.dumps(result, indent=2))

        sys.exit(0)

    except Exception as e:
        error_result = {
            "error": str(e),
            "scenes": []
        }
        print("JSON_OUTPUT:" + json.dumps(error_result, indent=2))
        sys.exit(1)
