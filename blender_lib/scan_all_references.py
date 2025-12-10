"""Blender script to scan all .blend files and collect all referenced files."""

import bpy
import sys
import argparse
from pathlib import Path
import os

# Import shared utilities
sys.path.insert(0, os.path.dirname(__file__))
from script_utils import output_json, create_error_result, create_success_result


def scan_all_references(project_root):
    """Scan all .blend files in project and collect all referenced files.

    Args:
        project_root: Path to project root directory

    Returns:
        Dictionary with all referenced files and reference map
    """
    result = {
        "success": False,
        "all_referenced_files": [],
        "references_map": {},  # file_path -> [blend_files that use it]
        "blend_files_scanned": 0,
        "errors": [],
        "warnings": []
    }

    try:
        project_path = Path(project_root)
        if not project_path.exists():
            result["errors"].append(f"Project root does not exist: {project_root}")
            return result

        # Find all .blend files in project
        blend_files = []
        ignore_dirs = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache',
                      'node_modules', 'build', 'dist'}

        print(f"LOG: Scanning for .blend files in {project_root}...")
        for root, dirs, files in os.walk(project_root):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in ignore_dirs]

            for file in files:
                if file.endswith('.blend') and not file.startswith('.'):
                    blend_files.append(Path(root) / file)

        print(f"LOG: Found {len(blend_files)} .blend files")

        if len(blend_files) == 0:
            result["warnings"].append("No .blend files found in project")
            result["success"] = True
            return result

        # Scan each blend file for references
        referenced_files = set()
        references_map = {}

        for i, blend_file in enumerate(blend_files, 1):
            print(f"LOG: Scanning {blend_file.name} ({i}/{len(blend_files)})...")

            try:
                # Open the blend file
                bpy.ops.wm.open_mainfile(filepath=str(blend_file))

                # Scan for image references
                for img in bpy.data.images:
                    if img.filepath:
                        # Resolve relative paths
                        if img.filepath.startswith('//'):
                            img_path = bpy.path.abspath(img.filepath)
                        else:
                            img_path = img.filepath

                        img_path = str(Path(img_path).resolve())

                        # Only track files within project root
                        try:
                            rel_path = Path(img_path).relative_to(project_path)
                            referenced_files.add(img_path)

                            if img_path not in references_map:
                                references_map[img_path] = []
                            references_map[img_path].append(str(blend_file))
                        except ValueError:
                            # File is outside project root, skip
                            pass

                # Scan for library references
                for lib in bpy.data.libraries:
                    if lib.filepath:
                        # Resolve relative paths
                        if lib.filepath.startswith('//'):
                            lib_path = bpy.path.abspath(lib.filepath)
                        else:
                            lib_path = lib.filepath

                        lib_path = str(Path(lib_path).resolve())

                        # Only track files within project root
                        try:
                            rel_path = Path(lib_path).relative_to(project_path)
                            referenced_files.add(lib_path)

                            if lib_path not in references_map:
                                references_map[lib_path] = []
                            references_map[lib_path].append(str(blend_file))
                        except ValueError:
                            # File is outside project root, skip
                            pass

                result["blend_files_scanned"] += 1

            except Exception as e:
                result["warnings"].append(f"Error scanning {blend_file.name}: {str(e)}")
                continue

        result["all_referenced_files"] = sorted(list(referenced_files))
        result["references_map"] = references_map
        result["success"] = True

        print(f"LOG: Scan complete. Found {len(referenced_files)} referenced files.")

    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")
        result["success"] = False

    return result


if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('--project-root', required=True, help='Path to project root directory')

        # Get args after the '--' separator
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])

        # Execute scan
        result = scan_all_references(args.project_root)

        # Output as JSON
        output_json(result)

        sys.exit(0 if result["success"] else 1)

    except Exception as e:
        error_result = create_error_result(
            str(e),
            all_referenced_files=[],
            references_map={},
            blend_files_scanned=0
        )
        output_json(error_result)
        sys.exit(1)
