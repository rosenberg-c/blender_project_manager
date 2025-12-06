"""High-level Blender operations with preview support."""

import json
import shutil
from json import JSONDecoder
from pathlib import Path
from typing import Callable, List, Optional

from blender_lib.blender_runner import BlenderRunner
from blender_lib.models import OperationPreview, OperationResult, PathChange, LinkOperationParams
from services.filesystem_service import FilesystemService


def extract_json_from_output(output: str, marker: str = "JSON_OUTPUT:") -> dict:
    """Extract JSON data from Blender output.

    Blender output often contains additional text after JSON like "Blender quit".
    This function extracts only the valid JSON portion.

    Args:
        output: The stdout from Blender
        marker: The marker string before the JSON

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If JSON cannot be found or parsed
    """
    json_start = output.find(marker)
    if json_start == -1:
        raise ValueError(f"No {marker} found in output")

    # Start after the marker
    json_text = output[json_start + len(marker):].lstrip()

    # Use JSONDecoder to parse and find where JSON ends
    decoder = JSONDecoder()
    try:
        obj, end_idx = decoder.raw_decode(json_text)
        return obj
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")


class BlenderService:
    """Coordinates Blender operations with preview and execution modes."""

    def __init__(self, blender_path: Path, project_root: Path):
        """Initialize Blender service.

        Args:
            blender_path: Path to Blender executable
            project_root: Root directory of the project
        """
        self.runner = BlenderRunner(blender_path)
        self.filesystem = FilesystemService(project_root)
        self.project_root = project_root

        # Path to lib_scripts directory
        self.lib_scripts_dir = Path(__file__).parent.parent / "lib_scripts"

    def preview_move_file(self,
                         old_path: Path,
                         new_path: Path) -> OperationPreview:
        """Preview what will change when moving a file.

        Args:
            old_path: Current path of the file
            new_path: New path for the file

        Returns:
            OperationPreview with list of changes
        """
        changes = []
        warnings = []
        errors = []

        # Validation
        if not old_path.exists():
            errors.append(f"Source file does not exist: {old_path}")
            return OperationPreview(
                operation_name=f"Move {old_path.name}",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        if new_path.exists():
            errors.append(f"Target already exists: {new_path}")

        if not self.filesystem.is_project_path(old_path):
            warnings.append(f"Source is outside project directory")

        if not self.filesystem.is_project_path(new_path):
            warnings.append(f"Target is outside project directory")

        # Add the file move itself
        changes.append(PathChange(
            file_path=old_path,
            item_type='file_move',
            item_name=old_path.name,
            old_path=str(old_path),
            new_path=str(new_path),
            status='ok' if not errors else 'error'
        ))

        # Check if this is a .blend file - handle specially
        is_blend_file = old_path.suffix.lower() == '.blend'

        if is_blend_file:
            # Preview internal path rebasing
            try:
                script_path = Path(__file__).parent.parent / "blender_lib" / "move_scene.py"
                result = self.runner.run_script(
                    script_path,
                    {
                        "old-scene": str(old_path),
                        "new-scene": str(new_path),
                        "delete-old": "false",
                        "dry-run": "true"
                    },
                    timeout=120
                )

                move_result = extract_json_from_output(result.stdout)

                # Add rebased images
                for img in move_result.get("rebased_images", []):
                    changes.append(PathChange(
                        file_path=old_path,
                        item_type='image_rebase',
                        item_name=img["name"],
                        old_path=img["old_path"],
                        new_path=img["new_path"],
                        status='ok'
                    ))

                # Add rebased libraries
                for lib in move_result.get("rebased_libraries", []):
                    changes.append(PathChange(
                        file_path=old_path,
                        item_type='library_rebase',
                        item_name=lib["name"],
                        old_path=lib["old_path"],
                        new_path=lib["new_path"],
                        status='ok'
                    ))

                # Add warnings
                for warn in move_result.get("warnings", []):
                    warnings.append(warn)

            except Exception as e:
                warnings.append(f"Could not preview internal path rebasing: {str(e)}")

        # Find all .blend files that might reference this file
        blend_files = self.filesystem.find_blend_files()

        for blend_file in blend_files:
            # Skip the file being moved itself
            if blend_file == old_path:
                continue

            # Scan each blend for references to the file being moved
            blend_changes = self._scan_blend_for_references(
                blend_file,
                old_path,
                new_path
            )
            changes.extend(blend_changes)

        return OperationPreview(
            operation_name=f"Move {old_path.name} → {new_path.name}",
            changes=changes,
            warnings=warnings,
            errors=errors
        )

    def execute_move_file(self,
                         old_path: Path,
                         new_path: Path,
                         progress_callback: Optional[Callable[[int, str], None]] = None) -> OperationResult:
        """Execute file move with reference updates.

        Args:
            old_path: Current path of the file
            new_path: New path for the file
            progress_callback: Optional callback(percentage, message)

        Returns:
            OperationResult with success status
        """
        def report_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            report_progress(0, "Starting operation...")

            # Validate
            if not old_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Source file does not exist: {old_path}",
                    errors=[f"File not found: {old_path}"]
                )

            if new_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Target already exists: {new_path}",
                    errors=[f"File exists: {new_path}"]
                )

            # Check if this is a .blend file - handle specially
            is_blend_file = old_path.suffix.lower() == '.blend'

            if is_blend_file:
                # Use move_scene script to rebase internal paths
                return self._execute_move_blend_file(old_path, new_path, progress_callback)

            # Create target directory if needed
            report_progress(5, "Creating target directory...")
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            report_progress(10, f"Moving {old_path.name}...")
            shutil.move(str(old_path), str(new_path))

            # First, scan to find which files actually reference the moved file
            report_progress(20, "Scanning .blend files for references...")
            blend_files = self.filesystem.find_blend_files()

            if not blend_files:
                report_progress(100, "Complete (no .blend files to update)")
                return OperationResult(
                    success=True,
                    message="File moved successfully",
                    changes_made=1
                )

            # Scan all files to find which ones reference the moved file
            files_to_update = []
            for i, blend_file in enumerate(blend_files):
                progress = 20 + int(40 * i / len(blend_files))
                report_progress(progress, f"Scanning {blend_file.name}...")

                changes = self._scan_blend_for_references(blend_file, old_path, new_path)
                # Only include files that have actual references (not just errors)
                has_references = any(c.status != 'error' for c in changes)
                if has_references:
                    files_to_update.append(blend_file)

            if not files_to_update:
                report_progress(100, "Complete (no references found)")
                return OperationResult(
                    success=True,
                    message=f"File moved successfully (no .blend files referenced it)",
                    changes_made=1
                )

            # Now update only the files that need it
            report_progress(60, f"Updating {len(files_to_update)} .blend file(s)...")
            changes_made = 1  # The file move itself

            for i, blend_file in enumerate(files_to_update):
                progress = 60 + int(35 * i / len(files_to_update))
                report_progress(progress, f"Updating {blend_file.name}...")

                # Update paths in this blend file
                result = self._update_blend_paths(
                    blend_file,
                    old_path,
                    new_path
                )

                if result:
                    changes_made += result

            report_progress(100, "Complete!")

            return OperationResult(
                success=True,
                message=f"Successfully moved {old_path.name} and updated {len(files_to_update)} .blend file(s)",
                changes_made=changes_made
            )

        except Exception as e:
            # Try to rollback the file move
            if new_path.exists() and not old_path.exists():
                try:
                    shutil.move(str(new_path), str(old_path))
                    report_progress(0, "Operation failed, rolled back")
                except Exception:
                    pass

            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                errors=[str(e)]
            )

    def preview_move_directory(self,
                              old_path: Path,
                              new_path: Path) -> OperationPreview:
        """Preview what will change when moving a directory.

        Args:
            old_path: Current path of the directory
            new_path: New path for the directory

        Returns:
            OperationPreview with list of changes for all files in directory
        """
        changes = []
        warnings = []
        errors = []

        # Validation
        if not old_path.exists():
            errors.append(f"Source directory does not exist: {old_path}")
            return OperationPreview(
                operation_name=f"Move {old_path.name}/",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        if not old_path.is_dir():
            errors.append(f"Source is not a directory: {old_path}")
            return OperationPreview(
                operation_name=f"Move {old_path.name}",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        if new_path.exists():
            errors.append(f"Target directory already exists: {new_path}")
            return OperationPreview(
                operation_name=f"Move {old_path.name}/",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        # Find all .blend and texture files in the directory recursively
        blend_extensions = ['.blend']
        texture_extensions = ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']
        all_extensions = blend_extensions + texture_extensions

        files_to_move = []
        for ext in all_extensions:
            files_to_move.extend(old_path.rglob(f'*{ext}'))

        if not files_to_move:
            warnings.append("No .blend or texture files found in directory")
            return OperationPreview(
                operation_name=f"Move {old_path.name}/",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        # For each file, calculate its new path and check for references
        from blender_lib.models import PathChange

        for file in files_to_move:
            # Calculate new path for this file (maintaining directory structure)
            rel_path = file.relative_to(old_path)
            file_new_path = new_path / rel_path

            # Add a change for the file move itself
            item_type = 'directory_move'
            if file.suffix == '.blend':
                item_type = 'directory_move_blend'  # Will also rebase internal paths

            changes.append(PathChange(
                file_path=file,
                item_type=item_type,
                item_name=str(rel_path),
                old_path=str(file),
                new_path=str(file_new_path),
                status='ok'
            ))

        # Now scan all .blend files in the project for references to files being moved
        all_blend_files = self.filesystem.find_blend_files()

        for blend_file in all_blend_files:
            # Skip blend files that are inside the directory being moved
            try:
                blend_file.relative_to(old_path)
                continue  # This file is being moved, skip it
            except ValueError:
                pass  # Not inside old_path, check for references

            # Check if this blend file references any of the files being moved
            for file in files_to_move:
                rel_path = file.relative_to(old_path)
                file_new_path = new_path / rel_path

                blend_changes = self._scan_blend_for_references(
                    blend_file,
                    file,
                    file_new_path
                )
                changes.extend(blend_changes)

        return OperationPreview(
            operation_name=f"Move {old_path.name}/ → {new_path.name}/",
            changes=changes,
            warnings=warnings,
            errors=errors
        )

    def execute_move_directory(self,
                              old_path: Path,
                              new_path: Path,
                              progress_callback: Optional[Callable[[int, str], None]] = None) -> OperationResult:
        """Execute directory move with reference updates.

        Args:
            old_path: Current path of the directory
            new_path: New path for the directory
            progress_callback: Optional callback(percentage, message)

        Returns:
            OperationResult with success status
        """
        def report_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            report_progress(0, "Starting directory move...")

            # Validation
            if not old_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Source directory does not exist: {old_path}",
                    errors=[f"Directory not found: {old_path}"]
                )

            if not old_path.is_dir():
                return OperationResult(
                    success=False,
                    message=f"Source is not a directory: {old_path}",
                    errors=[f"Not a directory: {old_path}"]
                )

            if new_path.exists():
                return OperationResult(
                    success=False,
                    message=f"Target directory already exists: {new_path}",
                    errors=[f"Directory exists: {new_path}"]
                )

            # Find all .blend and texture files in the directory
            blend_extensions = ['.blend']
            texture_extensions = ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']
            all_extensions = blend_extensions + texture_extensions

            files_to_move = []
            for ext in all_extensions:
                files_to_move.extend(old_path.rglob(f'*{ext}'))

            report_progress(5, f"Found {len(files_to_move)} files to move...")

            # Build mapping of old paths to new paths
            file_mappings = []
            for file in files_to_move:
                rel_path = file.relative_to(old_path)
                file_new_path = new_path / rel_path
                file_mappings.append((file, file_new_path))

            # Find all .blend files in project that might reference files being moved
            report_progress(10, "Scanning for references...")
            all_blend_files = self.filesystem.find_blend_files()

            files_to_update = {}  # blend_file -> list of (old, new) tuples

            for blend_file in all_blend_files:
                # Skip blend files inside the directory being moved
                try:
                    blend_file.relative_to(old_path)
                    continue
                except ValueError:
                    pass

                # Check if this blend file references any files being moved
                for old_file, new_file in file_mappings:
                    changes = self._scan_blend_for_references(blend_file, old_file, new_file)
                    has_references = any(c.status != 'error' for c in changes)
                    if has_references:
                        if blend_file not in files_to_update:
                            files_to_update[blend_file] = []
                        files_to_update[blend_file].append((old_file, new_file))

            # Move the directory
            report_progress(20, f"Moving directory {old_path.name}/...")
            shutil.move(str(old_path), str(new_path))

            # Rebase internal paths in all moved .blend files
            moved_blend_files = [f for f in files_to_move if f.suffix == '.blend']
            if moved_blend_files:
                report_progress(30, "Rebasing internal paths in moved .blend files...")
                script_path = Path(__file__).parent.parent / "blender_lib" / "rebase_blend_paths.py"

                # Create comma-separated list of OLD absolute paths of all moved files
                # This helps the rebase script know which references should NOT be rebased
                moved_files_old_paths = ','.join(str(f) for f in files_to_move)

                for i, old_blend_path in enumerate(moved_blend_files):
                    # Calculate new path for this blend file
                    rel_path = old_blend_path.relative_to(old_path)
                    new_blend_path = new_path / rel_path

                    progress = 30 + int(20 * i / len(moved_blend_files))
                    report_progress(progress, f"Rebasing {rel_path}...")

                    # Run rebase script
                    result = self.runner.run_script(
                        script_path,
                        {
                            "blend-file": str(new_blend_path),  # File at its new location
                            "old-dir": str(old_blend_path.parent),  # Where it was
                            "new-dir": str(new_blend_path.parent),  # Where it is now
                            "moved-files": moved_files_old_paths,  # List of all moved files
                            "dry-run": "false"
                        },
                        timeout=120
                    )

                    # Check for errors
                    rebase_result = extract_json_from_output(result.stdout)
                    if not rebase_result.get("success"):
                        # Log warning but continue
                        print(f"Warning: Failed to rebase {new_blend_path}: {rebase_result.get('errors')}")

            # Update all .blend files that reference moved files
            if files_to_update:
                total_files = len(files_to_update)
                for i, (blend_file, file_pairs) in enumerate(files_to_update.items()):
                    progress = 50 + int(45 * i / total_files)
                    report_progress(progress, f"Updating {blend_file.name}...")

                    # Update all references in this blend file
                    for old_file, new_file in file_pairs:
                        self._update_blend_paths(blend_file, old_file, new_file)

            report_progress(100, "Directory move complete!")

            total_changes = len(files_to_move) + sum(len(pairs) for pairs in files_to_update.values())

            # Build success message
            message = f"Directory moved successfully ({len(files_to_move)} files)"
            if moved_blend_files:
                message += f", rebased internal paths in {len(moved_blend_files)} .blend file(s)"
            if files_to_update:
                message += f", updated {len(files_to_update)} external file(s)"

            return OperationResult(
                success=True,
                message=message,
                changes_made=total_changes
            )

        except Exception as e:
            import traceback
            traceback.print_exc()

            # Try to rollback the directory move
            if new_path.exists() and not old_path.exists():
                try:
                    shutil.move(str(new_path), str(old_path))
                    report_progress(0, "Operation failed, rolled back")
                except Exception:
                    pass

            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                errors=[str(e)]
            )

    def _execute_move_blend_file(self,
                                 old_path: Path,
                                 new_path: Path,
                                 progress_callback: Optional[Callable[[int, str], None]] = None) -> OperationResult:
        """Execute move of a .blend file with internal path rebasing.

        This handles the special case of moving .blend files where internal
        relative paths need to be rebased to still point to the same files.

        Args:
            old_path: Current path to .blend file
            new_path: New path for .blend file
            progress_callback: Optional callback(percentage, message)

        Returns:
            OperationResult with success status
        """
        def report_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            report_progress(10, f"Moving .blend file and rebasing paths...")

            # Use move_scene.py script to move and rebase
            script_path = Path(__file__).parent.parent / "blender_lib" / "move_scene.py"

            result = self.runner.run_script(
                script_path,
                {
                    "old-scene": str(old_path),
                    "new-scene": str(new_path),
                    "delete-old": "true",  # Delete old file after successful move
                    "dry-run": "false"
                },
                timeout=120
            )

            # Parse result
            move_result = extract_json_from_output(result.stdout)

            if not move_result.get("success"):
                errors = move_result.get("errors", ["Unknown error"])
                return OperationResult(
                    success=False,
                    message=f"Failed to move .blend file: {errors[0]}",
                    errors=errors
                )

            report_progress(50, "Scanning for files that link to this .blend...")

            # Now update references in OTHER .blend files that link to this one
            blend_files = self.filesystem.find_blend_files()
            files_to_update = []

            for blend_file in blend_files:
                # Skip the file we just moved
                if blend_file == new_path:
                    continue

                # Check if this file references the moved .blend
                changes = self._scan_blend_for_references(blend_file, old_path, new_path)
                has_references = any(c.status != 'error' for c in changes)
                if has_references:
                    files_to_update.append(blend_file)

            if not files_to_update:
                report_progress(100, "Complete!")

                # Build success message
                rebased_count = len(move_result.get("rebased_images", [])) + len(move_result.get("rebased_libraries", []))
                message = f"Successfully moved {old_path.name}"
                if rebased_count > 0:
                    message += f" and rebased {rebased_count} internal path(s)"

                return OperationResult(
                    success=True,
                    message=message,
                    changes_made=1
                )

            # Update files that link to this .blend
            report_progress(70, f"Updating {len(files_to_update)} file(s) that link to this .blend...")
            changes_made = 1  # The move itself

            for i, blend_file in enumerate(files_to_update):
                progress = 70 + int(25 * i / len(files_to_update))
                report_progress(progress, f"Updating {blend_file.name}...")

                result = self._update_blend_paths(blend_file, old_path, new_path)
                if result:
                    changes_made += result

            report_progress(100, "Complete!")

            # Build success message
            rebased_count = len(move_result.get("rebased_images", [])) + len(move_result.get("rebased_libraries", []))
            message = f"Successfully moved {old_path.name}"
            if rebased_count > 0:
                message += f", rebased {rebased_count} internal path(s)"
            if len(files_to_update) > 0:
                message += f", and updated {len(files_to_update)} linked file(s)"

            return OperationResult(
                success=True,
                message=message,
                changes_made=changes_made
            )

        except Exception as e:
            # Try to rollback if file was moved but something failed
            if new_path.exists() and not old_path.exists():
                try:
                    shutil.move(str(new_path), str(old_path))
                    report_progress(0, "Operation failed, rolled back")
                except Exception:
                    pass

            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                errors=[str(e)]
            )

    def _scan_blend_for_references(self,
                                   blend_path: Path,
                                   target_file: Path,
                                   new_location: Path) -> List[PathChange]:
        """Scan a blend file for references to a specific file.

        This is for preview mode - it checks if the blend references the file.

        Args:
            blend_path: The .blend file to scan
            target_file: The file we're looking for references to
            new_location: Where the file will be moved to

        Returns:
            List of PathChange objects
        """
        changes = []

        try:
            script_path = self.lib_scripts_dir / "scan_blend_references.py"

            result = self.runner.run_script(
                script_path,
                {"blend-file": str(blend_path)},
                timeout=60
            )

            # Parse JSON output using helper function
            refs = extract_json_from_output(result.stdout)

            target_str = str(target_file.resolve())

            # Check image references
            for img in refs.get("images", []):
                resolved = Path(img["resolved"]).resolve() if img["resolved"] else None
                if resolved and str(resolved) == target_str:
                    changes.append(PathChange(
                        file_path=blend_path,
                        item_type='image',
                        item_name=img["name"],
                        old_path=img["filepath"],
                        new_path=str(new_location),
                        status='ok'
                    ))

            # Check library references
            for lib in refs.get("libraries", []):
                resolved = Path(lib["resolved"]).resolve() if lib["resolved"] else None
                if resolved and str(resolved) == target_str:
                    changes.append(PathChange(
                        file_path=blend_path,
                        item_type='library',
                        item_name=lib["name"],
                        old_path=lib["filepath"],
                        new_path=str(new_location),
                        status='ok'
                    ))

        except Exception as e:
            # If scanning fails, add a warning but don't fail the whole operation
            # Log error to console for debugging
            print(f"Warning: Error scanning {blend_path}: {str(e)}")

            changes.append(PathChange(
                file_path=blend_path,
                item_type='error',
                item_name=f'Scan Error: {str(e)}',
                old_path='',
                new_path='',
                status='error'
            ))

        return changes

    def _update_blend_paths(self,
                           blend_path: Path,
                           old_location: Path,
                           new_location: Path) -> int:
        """Update paths in a blend file after a file move.

        Args:
            blend_path: The .blend file to update
            old_location: Old path of the moved file
            new_location: New path of the moved file

        Returns:
            Number of changes made
        """
        try:
            script_path = self.lib_scripts_dir / "update_blend_paths.py"

            result = self.runner.run_script(
                script_path,
                {
                    "blend-file": str(blend_path),
                    "old-path": str(old_location.resolve()),
                    "new-path": str(new_location.resolve())
                },
                timeout=120
            )

            # Parse JSON output using helper function
            update_result = extract_json_from_output(result.stdout)

            return update_result.get("changes_count", 0)

        except Exception as e:
            print(f"Warning: Failed to update {blend_path}: {e}")
            return 0

    def get_scenes(self, blend_file: Path) -> List[dict]:
        """Get list of scenes in a .blend file.

        Args:
            blend_file: Path to .blend file

        Returns:
            List of scene dictionaries with 'name' and 'is_active' keys

        Raises:
            Exception: If scenes cannot be loaded
        """
        try:
            script_path = Path(__file__).parent.parent / "blender_lib" / "list_scenes.py"

            result = self.runner.run_script(
                script_path,
                {"blend-file": str(blend_file)},
                timeout=60
            )

            data = extract_json_from_output(result.stdout)

            if "error" in data and data["error"]:
                raise Exception(data["error"])

            return data.get("scenes", [])

        except Exception as e:
            raise Exception(f"Failed to get scenes from {blend_file.name}: {str(e)}")

    def preview_link_operation(self, params: LinkOperationParams) -> OperationPreview:
        """Preview what will happen when linking objects/collections.

        Args:
            params: Link operation parameters

        Returns:
            OperationPreview with list of changes
        """
        changes = []
        warnings = []
        errors = []

        # Validation
        if not params.target_file.exists():
            errors.append(f"Target file does not exist: {params.target_file}")

        if not params.source_file.exists():
            errors.append(f"Source file does not exist: {params.source_file}")

        if not params.item_names:
            errors.append("No items selected to link")

        if len(params.item_names) != len(params.item_types):
            errors.append("Item names and types count mismatch")

        if not params.target_collection:
            errors.append("Target collection name is required")

        if errors:
            return OperationPreview(
                operation_name="Link Objects/Collections",
                changes=changes,
                warnings=warnings,
                errors=errors
            )

        # Run dry-run link operation
        try:
            script_path = Path(__file__).parent.parent / "blender_lib" / "link_objects.py"

            result = self.runner.run_script(
                script_path,
                {
                    "target-file": str(params.target_file),
                    "target-scene": params.target_scene,
                    "source-file": str(params.source_file),
                    "item-names": ",".join(params.item_names),
                    "item-types": ",".join(params.item_types),
                    "target-collection": params.target_collection,
                    "link-mode": params.link_mode,
                    "dry-run": "true"
                },
                timeout=120
            )

            link_result = extract_json_from_output(result.stdout)

            # Convert to PathChange objects for preview dialog
            for item in link_result.get("linked_items", []):
                changes.append(PathChange(
                    file_path=params.target_file,
                    item_type=f"link_{item['type']}",
                    item_name=item["name"],
                    old_path=str(params.source_file),
                    new_path=f"{params.target_scene} → {params.target_collection}",
                    status='ok'
                ))

            # Add warnings and errors from Blender script
            warnings.extend(link_result.get("warnings", []))
            errors.extend(link_result.get("errors", []))

            # Add info about target collection
            collection_status = link_result.get("target_collection_status", "")
            if collection_status == "will_create":
                warnings.append(f"Collection '{params.target_collection}' will be created")

        except Exception as e:
            errors.append(f"Preview failed: {str(e)}")

        return OperationPreview(
            operation_name=f"Link to {params.target_file.name}",
            changes=changes,
            warnings=warnings,
            errors=errors
        )

    def execute_link_operation(
        self,
        params: LinkOperationParams,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> OperationResult:
        """Execute linking objects/collections from source to target file.

        Args:
            params: Link operation parameters
            progress_callback: Optional callback(percentage, message)

        Returns:
            OperationResult with success status
        """
        def report_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            report_progress(0, "Starting link operation...")

            # Validation
            if not params.target_file.exists():
                return OperationResult(
                    success=False,
                    message=f"Target file does not exist: {params.target_file}",
                    errors=["Target file not found"]
                )

            if not params.source_file.exists():
                return OperationResult(
                    success=False,
                    message=f"Source file does not exist: {params.source_file}",
                    errors=["Source file not found"]
                )

            if not params.item_names:
                return OperationResult(
                    success=False,
                    message="No items selected to link",
                    errors=["No items selected"]
                )

            report_progress(20, f"Linking {len(params.item_names)} item(s)...")

            # Execute link operation
            script_path = Path(__file__).parent.parent / "blender_lib" / "link_objects.py"

            result = self.runner.run_script(
                script_path,
                {
                    "target-file": str(params.target_file),
                    "target-scene": params.target_scene,
                    "source-file": str(params.source_file),
                    "item-names": ",".join(params.item_names),
                    "item-types": ",".join(params.item_types),
                    "target-collection": params.target_collection,
                    "link-mode": params.link_mode,
                    "dry-run": "false"
                },
                timeout=180
            )

            link_result = extract_json_from_output(result.stdout)

            report_progress(100, "Complete!")

            if not link_result.get("success", False):
                errors = link_result.get("errors", ["Unknown error"])
                return OperationResult(
                    success=False,
                    message=f"Link operation failed: {errors[0]}",
                    errors=errors
                )

            # Build success message
            linked_items = link_result.get("linked_items", [])
            warnings = link_result.get("warnings", [])

            message = f"Successfully linked {len(linked_items)} item(s) to {params.target_file.name}"
            if warnings:
                message += f" (with {len(warnings)} warning(s))"

            return OperationResult(
                success=True,
                message=message,
                changes_made=len(linked_items),
                errors=link_result.get("errors", [])
            )

        except Exception as e:
            report_progress(0, "Operation failed")
            return OperationResult(
                success=False,
                message=f"Operation failed: {str(e)}",
                errors=[str(e)]
            )
