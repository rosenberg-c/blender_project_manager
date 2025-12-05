"""High-level Blender operations with preview support."""

import json
import shutil
from json import JSONDecoder
from pathlib import Path
from typing import Callable, List, Optional

from blender_lib.blender_runner import BlenderRunner
from blender_lib.models import OperationPreview, OperationResult, PathChange
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
