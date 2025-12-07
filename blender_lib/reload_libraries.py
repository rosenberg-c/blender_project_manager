"""Blender script to reload all library links in .blend files.

This is useful after moving/renaming textures or linked files, as Blender may
need to reload libraries to display updated paths correctly.
"""

import bpy
import sys
import argparse
import os
from pathlib import Path

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result

# Add parent directory to path to import core utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.file_scanner import find_blend_files


def reload_libraries_in_file(blend_file_path: str, dry_run: bool = True):
    """Reload all library links in a single .blend file.

    Args:
        blend_file_path: Path to .blend file
        dry_run: If True, only report what would be reloaded

    Returns:
        Dictionary with reload results for this file
    """
    result = {
        "file": blend_file_path,
        "libraries_found": 0,
        "libraries_reloaded": 0,
        "library_details": [],
        "errors": []
    }

    try:
        # Open the blend file
        bpy.ops.wm.open_mainfile(filepath=str(blend_file_path))

        # Get all libraries in this file
        libraries = list(bpy.data.libraries)
        result["libraries_found"] = len(libraries)

        if not libraries:
            return result

        # Reload each library
        for lib in libraries:
            lib_info = {
                "name": lib.name,
                "filepath": lib.filepath,
                "reloaded": False
            }

            try:
                if not dry_run:
                    # Reload the library
                    lib.reload()
                    lib_info["reloaded"] = True
                    result["libraries_reloaded"] += 1
                else:
                    # In dry run, just report what we would reload
                    lib_info["reloaded"] = False

                result["library_details"].append(lib_info)

            except Exception as e:
                lib_info["error"] = str(e)
                result["library_details"].append(lib_info)
                result["errors"].append(f"Failed to reload {lib.name}: {e}")

        # Save the file if we actually reloaded libraries
        if not dry_run and result["libraries_reloaded"] > 0:
            try:
                bpy.ops.wm.save_mainfile()
            except Exception as e:
                result["errors"].append(f"Failed to save file: {e}")

    except Exception as e:
        result["errors"].append(f"Failed to process file: {e}")

    return result


def reload_all_libraries(project_root: str, dry_run: bool = True):
    """Reload library links in all .blend files in the project.

    Args:
        project_root: Root directory of the project
        dry_run: If True, only preview what would be reloaded

    Returns:
        Dictionary with results for all files
    """
    result = {
        "files_processed": 0,
        "files_with_libraries": 0,
        "total_libraries_found": 0,
        "total_libraries_reloaded": 0,
        "file_results": [],
        "errors": [],
        "warnings": []
    }

    # Find all .blend files in the project
    try:
        blend_files = find_blend_files(Path(project_root))
    except Exception as e:
        result["errors"].append(f"Failed to find .blend files: {e}")
        return result

    # Process each .blend file
    for blend_file in blend_files:
        try:
            file_result = reload_libraries_in_file(str(blend_file), dry_run)

            result["files_processed"] += 1

            if file_result["libraries_found"] > 0:
                result["files_with_libraries"] += 1
                result["total_libraries_found"] += file_result["libraries_found"]
                result["total_libraries_reloaded"] += file_result["libraries_reloaded"]
                result["file_results"].append(file_result)

            # Collect any errors from this file
            if file_result["errors"]:
                result["errors"].extend(file_result["errors"])

        except Exception as e:
            result["warnings"].append(f"Could not process {blend_file}: {e}")

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--project-root', required=True, help='Project root directory')
        parser.add_argument('--dry-run', choices=['true', 'false'], default='true', help='Preview only')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        dry_run = args.dry_run == 'true'

        # Reload all libraries
        result = reload_all_libraries(args.project_root, dry_run)

        # Output as JSON
        output_json(create_success_result(**result))

        sys.exit(0)

    except Exception as e:
        import traceback
        error_result = create_error_result(
            str(e),
            traceback=traceback.format_exc(),
            files_processed=0,
            files_with_libraries=0,
            total_libraries_found=0,
            total_libraries_reloaded=0,
            file_results=[]
        )
        output_json(error_result)
        sys.exit(1)
