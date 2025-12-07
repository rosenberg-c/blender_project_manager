"""Base class for operation tabs with shared functionality."""

from pathlib import Path
from contextlib import contextmanager
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QMessageBox, QApplication, QPushButton
from PySide6.QtGui import QCursor

from controllers.file_operations_controller import FileOperationsController


class BaseOperationTab(QWidget):
    """Base class for operation tabs providing common functionality."""

    def __init__(self, controller: FileOperationsController, parent=None):
        """Initialize base tab.

        Args:
            controller: File operations controller
            parent: Parent widget (operations panel)
        """
        super().__init__(parent)
        self.controller = controller
        self.operations_panel = parent  # Reference to parent OperationsPanelWidget
        self.current_file: Optional[Path] = None

    def set_file(self, file_path: Path):
        """Set the currently selected file.

        This method should be overridden by subclasses to handle file selection.

        Args:
            file_path: Path to the selected file or directory
        """
        self.current_file = file_path

    # Dialog Helper Methods

    def show_error(self, title: str, message: str):
        """Show error dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        QMessageBox.critical(self, title, message)

    def show_warning(self, title: str, message: str):
        """Show warning dialog.

        Args:
            title: Dialog title
            message: Warning message
        """
        QMessageBox.warning(self, title, message)

    def show_info(self, title: str, message: str):
        """Show information dialog.

        Args:
            title: Dialog title
            message: Information message
        """
        QMessageBox.information(self, title, message)

    def show_success(self, title: str, message: str):
        """Show success dialog.

        Args:
            title: Dialog title
            message: Success message
        """
        QMessageBox.information(self, title, message)

    def confirm(self, title: str, message: str) -> bool:
        """Show confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message

        Returns:
            True if user confirmed, False otherwise
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    # Loading State Management

    @contextmanager
    def loading_state(self, button: QPushButton, loading_text: str):
        """Context manager for managing loading state with cursor and button updates.

        Usage:
            with self.loading_state(self.execute_btn, "Executing..."):
                # Do work
                pass

        Args:
            button: Button to disable and update text
            loading_text: Text to show on button during loading

        Yields:
            None
        """
        # Save original state
        original_text = button.text()
        original_enabled = button.isEnabled()

        # Set loading state
        button.setText(loading_text)
        button.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()  # Force UI update

        try:
            yield
        finally:
            # Restore original state
            QApplication.restoreOverrideCursor()
            button.setText(original_text)
            button.setEnabled(original_enabled)

    def with_loading_cursor(self, operation: Callable):
        """Execute an operation with wait cursor.

        Args:
            operation: Function to execute with loading cursor

        Returns:
            Result of the operation
        """
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        try:
            return operation()
        finally:
            QApplication.restoreOverrideCursor()

    # File Type Helpers

    @staticmethod
    def is_blend_file(file_path: Path) -> bool:
        """Check if file is a .blend file.

        Args:
            file_path: Path to check

        Returns:
            True if file is a .blend file
        """
        return file_path.suffix == '.blend'

    @staticmethod
    def is_texture_file(file_path: Path) -> bool:
        """Check if file is a supported texture file.

        Args:
            file_path: Path to check

        Returns:
            True if file is a texture file
        """
        return file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']

    @staticmethod
    def is_directory(file_path: Path) -> bool:
        """Check if path is a directory.

        Args:
            file_path: Path to check

        Returns:
            True if path is a directory
        """
        return file_path.is_dir()

    # Utility Methods

    def get_project_root(self) -> Path:
        """Get project root directory.

        Returns:
            Project root path
        """
        return self.controller.project.project_root

    def get_blender_runner(self):
        """Get Blender script runner.

        Returns:
            Blender script runner
        """
        return self.controller.project.blender_service.runner
