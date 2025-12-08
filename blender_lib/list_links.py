"""Blender script to list all linked files (libraries and textures) in a .blend file.

This is the opposite of find_references - it shows what this file is importing,
not what files are importing this file.
"""

import bpy
import sys
import argparse
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def list_linked_files():
    """List all linked libraries, textures, and materials in the current blend file.

    Returns:
        Dictionary with linked libraries, textures, and materials
    """
    result = {
        "linked_libraries": [],
        "linked_textures": [],
        "linked_materials": [],
        "total_libraries": 0,
        "total_textures": 0,
        "total_materials": 0
    }

    # Get all linked libraries
    for lib in bpy.data.libraries:
        lib_path = lib.filepath
        abs_path = bpy.path.abspath(lib.filepath)

        # Get objects and collections linked from this library
        linked_objects = [obj.name for obj in bpy.data.objects if obj.library == lib]
        linked_collections = [col.name for col in bpy.data.collections if col.library == lib]

        lib_info = {
            "name": lib.name,
            "filepath": lib_path,
            "absolute_path": abs_path,
            "exists": os.path.exists(abs_path) if abs_path else False,
            "linked_objects": linked_objects,
            "linked_collections": linked_collections,
            "objects_count": len(linked_objects),
            "collections_count": len(linked_collections)
        }

        result["linked_libraries"].append(lib_info)
        result["total_libraries"] += 1

    # Get all textures/images
    for img in bpy.data.images:
        # Skip images without filepath (generated, render results, etc.)
        if not img.filepath:
            continue

        # Skip packed images
        if img.packed_file:
            continue

        # Skip images from linked libraries (they belong to the library, not this file)
        if img.library is not None:
            continue

        img_path = img.filepath
        abs_path = bpy.path.abspath(img.filepath)

        img_info = {
            "name": img.name,
            "filepath": img_path,
            "absolute_path": abs_path,
            "exists": os.path.exists(abs_path) if abs_path else False,
            "size": [img.size[0], img.size[1]] if img.size[0] > 0 else None
        }

        result["linked_textures"].append(img_info)
        result["total_textures"] += 1

    for mat in bpy.data.materials:
        if mat.library is not None:
            continue

        mat_info = {
            "name": mat.name,
            "use_nodes": mat.use_nodes,
            "users": mat.users
        }

        result["linked_materials"].append(mat_info)
        result["total_materials"] += 1

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--blend-file', required=True, help='Path to .blend file')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Load the blend file
        bpy.ops.wm.open_mainfile(filepath=str(args.blend_file))

        # Get linked files
        result = list_linked_files()

        # Output as JSON
        output_json(create_success_result(**result))

        sys.exit(0)

    except Exception as e:
        import traceback
        output_json(create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            linked_libraries=[],
            linked_textures=[],
            linked_materials=[]
        ))
        sys.exit(1)
