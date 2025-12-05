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

        # Find all .blend files that might reference this file
        blend_files = self.filesystem.find_blend_files()

        for blend_file in blend_files:
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

            # Create target directory if needed
            report_progress(5, "Creating target directory...")
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            report_progress(10, f"Moving {old_path.name}...")
            shutil.move(str(old_path), str(new_path))

            # Update references in all blend files
            report_progress(20, "Finding .blend files...")
            blend_files = self.filesystem.find_blend_files()

            if not blend_files:
                report_progress(100, "Complete (no .blend files to update)")
                return OperationResult(
                    success=True,
                    message="File moved successfully",
                    changes_made=1
                )

            total = len(blend_files)
            changes_made = 1  # The file move itself

            for i, blend_file in enumerate(blend_files):
                progress = 20 + int(75 * i / total)
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
                message=f"Successfully moved {old_path.name} and updated {total} .blend file(s)",
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
