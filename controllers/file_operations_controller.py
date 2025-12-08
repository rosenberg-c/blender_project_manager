"""Controller for file operations."""

from pathlib import Path
from typing import Callable, Optional

from blender_lib.models import OperationPreview, OperationResult
from controllers.project_controller import ProjectController


class FileOperationsController:
    """Handles file operation requests from the GUI."""

    def __init__(self, project_controller: ProjectController):
        """Initialize file operations controller.

        Args:
            project_controller: The main project controller
        """
        self.project = project_controller

    def preview_move_file(self,
                         old_path: Path,
                         new_path: Path,
                         progress_callback: Optional[Callable[[int, str], None]] = None) -> OperationPreview:
        """Preview what will change when moving a file or directory.

        Args:
            old_path: Current path of the file or directory
            new_path: New path for the file or directory
            progress_callback: Optional callback for progress updates

        Returns:
            OperationPreview with list of changes
        """
        if not self.project.is_open or not self.project.blender_service:
            return OperationPreview(
                operation_name="Move File" if old_path.is_file() else "Move Directory",
                errors=["No project is open"]
            )

        # Auto-detect file vs directory
        if old_path.is_dir():
            return self.project.blender_service.preview_move_directory(
                old_path,
                new_path,
                progress_callback
            )
        else:
            return self.project.blender_service.preview_move_file(
                old_path,
                new_path,
                progress_callback
            )

    def execute_move_file(self,
                         old_path: Path,
                         new_path: Path,
                         progress_callback: Optional[Callable[[int, str], None]] = None) -> OperationResult:
        """Execute file or directory move operation.

        Args:
            old_path: Current path of the file or directory
            new_path: New path for the file or directory
            progress_callback: Optional callback for progress updates

        Returns:
            OperationResult with success status
        """
        if not self.project.is_open or not self.project.blender_service:
            return OperationResult(
                success=False,
                message="No project is open",
                errors=["No project is open"]
            )

        # Auto-detect file vs directory
        if old_path.is_dir():
            return self.project.blender_service.execute_move_directory(
                old_path,
                new_path,
                progress_callback
            )
        else:
            return self.project.blender_service.execute_move_file(
                old_path,
                new_path,
                progress_callback
            )

    def validate_move(self, old_path: Path, new_path: Path) -> tuple[bool, list[str]]:
        """Validate if a file move is possible.

        Args:
            old_path: Current path
            new_path: Target path

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if not old_path.exists():
            errors.append(f"Source file does not exist: {old_path}")

        if new_path.exists():
            errors.append(f"Target already exists: {new_path}")

        if old_path == new_path:
            errors.append("Source and target are the same")

        return (len(errors) == 0, errors)
