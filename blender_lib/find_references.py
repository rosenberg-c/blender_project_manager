"""Blender script to find all files that reference a specific file.

Supports:
- .blend files: Find which files link to them as libraries
- Texture files: Find which .blend files use them as images

This is useful for understanding file dependencies in a project.
"""

import bpy
import sys
import argparse
import os
from pathlib import Path

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result
from constants import TEXTURE_EXTENSIONS

# Add parent directory to path to import core utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.file_scanner import find_blend_files


def is_texture_file(file_path: str) -> bool:
    """Check if file is a texture file.

    Args:
        file_path: Path to file

    Returns:
        True if file is a texture
    """
    return Path(file_path).suffix.lower() in TEXTURE_EXTENSIONS


def find_references_to_blend_file(target_file: str, project_root: str):
    """Find all .blend files that link to the target .blend file as a library.

    Args:
        target_file: Path to the .blend file to find references to
        project_root: Root directory of the project

    Returns:
        Dictionary with results
    """
    result = {
        "target_file": target_file,
        "target_name": Path(target_file).name,
        "referencing_files": [],
        "files_scanned": 0,
        "errors": [],
        "warnings": []
    }

    # Get the absolute path and name of the target file
    target_path = Path(target_file).resolve()
    target_name = target_path.name

    try:
        # Find all .blend files in the project
        blend_files = find_blend_files(Path(project_root))

        # Remove the target file from the list (can't reference itself)
        blend_files = [f for f in blend_files if f.resolve() != target_path]

        # Check each blend file for references to the target
        for blend_file in blend_files:
            try:
                result["files_scanned"] += 1

                # Open the blend file
                bpy.ops.wm.open_mainfile(filepath=str(blend_file))

                # Check if this file has any libraries
                if not bpy.data.libraries:
                    continue

                # Check each library to see if it references our target file
                for lib in bpy.data.libraries:
                    # Get the absolute path of the library
                    lib_path = Path(bpy.path.abspath(lib.filepath)).resolve()

                    # Check if this library references our target file
                    if lib_path == target_path or lib_path.name == target_name:
                        # Count linked objects and collections
                        linked_objects = [obj for obj in bpy.data.objects if obj.library == lib]
                        linked_collections = [col for col in bpy.data.collections if col.library == lib]

                        ref_info = {
                            "file": str(blend_file),
                            "file_name": blend_file.name,
                            "library_name": lib.name,
                            "library_filepath": lib.filepath,
                            "linked_objects_count": len(linked_objects),
                            "linked_collections_count": len(linked_collections),
                            "linked_objects": [obj.name for obj in linked_objects[:10]],  # First 10
                            "linked_collections": [col.name for col in linked_collections[:10]]  # First 10
                        }

                        result["referencing_files"].append(ref_info)
                        break  # Found the reference, no need to check other libraries

            except Exception as e:
                result["warnings"].append(f"Could not scan {blend_file.name}: {str(e)}")
                continue

    except Exception as e:
        result["errors"].append(f"Failed to scan project: {str(e)}")

    return result


def find_references_to_texture(target_file: str, project_root: str):
    """Find all .blend files that use the target texture file.

    Args:
        target_file: Path to the texture file to find references to
        project_root: Root directory of the project

    Returns:
        Dictionary with results
    """
    result = {
        "target_file": target_file,
        "target_name": Path(target_file).name,
        "file_type": "texture",
        "referencing_files": [],
        "files_scanned": 0,
        "errors": [],
        "warnings": []
    }

    # Get the absolute path and name of the target file
    target_path = Path(target_file).resolve()
    target_name = target_path.name

    try:
        # Find all .blend files in the project
        blend_files = find_blend_files(Path(project_root))

        # Check each blend file for references to the texture
        for blend_file in blend_files:
            try:
                result["files_scanned"] += 1

                # Open the blend file
                bpy.ops.wm.open_mainfile(filepath=str(blend_file))

                # Check all images in this file
                if not bpy.data.images:
                    continue

                using_images = []
                for img in bpy.data.images:
                    # Skip images without a filepath (generated/packed images)
                    if not img.filepath:
                        continue

                    # Get the absolute path of the image
                    img_path = Path(bpy.path.abspath(img.filepath)).resolve()

                    # Check if this image is our target texture
                    if img_path == target_path or img_path.name == target_name:
                        using_images.append({
                            "name": img.name,
                            "filepath": img.filepath,
                            "size": f"{img.size[0]}x{img.size[1]}" if img.size[0] > 0 else "unknown"
                        })

                if using_images:
                    ref_info = {
                        "file": str(blend_file),
                        "file_name": blend_file.name,
                        "images_count": len(using_images),
                        "images": using_images[:10]  # First 10
                    }
                    result["referencing_files"].append(ref_info)

            except Exception as e:
                result["warnings"].append(f"Could not scan {blend_file.name}: {str(e)}")
                continue

    except Exception as e:
        result["errors"].append(f"Failed to scan project: {str(e)}")

    return result


def find_references_to_file(target_file: str, project_root: str):
    """Find all files that reference the target file.

    Automatically detects file type and uses appropriate method.

    Args:
        target_file: Path to the file to find references to
        project_root: Root directory of the project

    Returns:
        Dictionary with results
    """
    if is_texture_file(target_file):
        return find_references_to_texture(target_file, project_root)
    else:
        # Assume it's a .blend file
        return find_references_to_blend_file(target_file, project_root)


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--target-file', required=True, help='Path to .blend file to find references to')
        parser.add_argument('--project-root', required=True, help='Project root directory')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Find references
        result = find_references_to_file(args.target_file, args.project_root)

        # Output as JSON
        output_json(create_success_result(**result))

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            target_file=args.target_file if 'args' in locals() else "",
            referencing_files=[],
            files_scanned=0
        )
        output_json(error_result)
        sys.exit(1)
