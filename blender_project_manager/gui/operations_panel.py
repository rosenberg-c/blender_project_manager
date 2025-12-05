"""Operations panel for file operations."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox
)

from controllers.file_operations_controller import FileOperationsController
from gui.preview_dialog import OperationPreviewDialog
from gui.progress_dialog import OperationProgressDialog


class OperationsPanelWidget(QWidget):
    """Panel for configuring and executing file operations."""

    def __init__(self, controller: FileOperationsController, parent=None):
        """Initialize operations panel.

        Args:
            controller: File operations controller
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.current_file: Path | None = None

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>File Operations</h2>")
        layout.addWidget(title)

        # Current file display
        file_label = QLabel("<b>Selected File:</b>")
        layout.addWidget(file_label)

        self.file_display = QLabel("<i>No file selected</i>")
        self.file_display.setWordWrap(True)
        self.file_display.setStyleSheet(
            "padding: 10px; "
            "background-color: #f0f0f0; "
            "color: #333333; "
            "border-radius: 5px; "
            "border: 1px solid #cccccc;"
        )
        layout.addWidget(self.file_display)

        # Separator
        layout.addSpacing(20)

        # Move/Rename section
        move_label = QLabel("<b>Move/Rename File:</b>")
        layout.addWidget(move_label)

        # New path input
        new_path_label = QLabel("New path:")
        layout.addWidget(new_path_label)

        self.new_path_input = QLineEdit()
        self.new_path_input.setPlaceholderText("Enter new path...")
        layout.addWidget(self.new_path_input)

        # Browse and Preview buttons
        btn_row1 = QHBoxLayout()

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_new_path)
        self.browse_btn.setEnabled(False)
        btn_row1.addWidget(self.browse_btn)

        self.preview_btn = QPushButton("Preview Changes")
        self.preview_btn.clicked.connect(self._preview_operation)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        btn_row1.addWidget(self.preview_btn)

        layout.addLayout(btn_row1)

        # Execute button
        self.execute_btn = QPushButton("Execute Move")
        self.execute_btn.clicked.connect(self._execute_operation)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(self.execute_btn)

        # Add stretch to push everything to top
        layout.addStretch()

    def set_file(self, file_path: Path):
        """Set the currently selected file.

        Args:
            file_path: Path to the selected file
        """
        self.current_file = file_path
        self.file_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")
        self.new_path_input.setText(str(file_path))

        # Enable buttons
        self.browse_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)

    def _browse_new_path(self):
        """Open file dialog to select new path."""
        if not self.current_file:
            return

        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select New Location",
            str(self.current_file),
            f"*{self.current_file.suffix}"
        )

        if new_path:
            self.new_path_input.setText(new_path)

    def _preview_operation(self):
        """Show preview dialog for the operation."""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return

        new_path = Path(self.new_path_input.text())

        if new_path == self.current_file:
            QMessageBox.information(self, "No Change", "Source and target are the same.")
            return

        # Get preview from controller
        preview = self.controller.preview_move_file(self.current_file, new_path)

        # Show preview dialog
        dialog = OperationPreviewDialog(preview, self)
        dialog.exec()

    def _execute_operation(self):
        """Execute the move operation."""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return

        new_path = Path(self.new_path_input.text())

        if new_path == self.current_file:
            QMessageBox.information(self, "No Change", "Source and target are the same.")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Operation",
            f"Move/rename file?\n\nFrom: {self.current_file}\nTo: {new_path}\n\n"
            "All .blend files referencing this file will be updated.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Create progress dialog
        progress_dialog = OperationProgressDialog(
            f"Moving {self.current_file.name}",
            self
        )

        # Execute operation
        result = self.controller.execute_move_file(
            self.current_file,
            new_path,
            progress_dialog.update_progress
        )

        # Show result
        if result.success:
            progress_dialog.update_progress(100, result.message)
            progress_dialog.exec()

            QMessageBox.information(
                self,
                "Success",
                f"{result.message}\n\n{result.changes_made} changes made."
            )

            # Clear selection
            self.current_file = None
            self.file_display.setText("<i>No file selected</i>")
            self.new_path_input.clear()
            self.browse_btn.setEnabled(False)
            self.preview_btn.setEnabled(False)
            self.execute_btn.setEnabled(False)
        else:
            progress_dialog.mark_error(result.message)
            progress_dialog.exec()

            QMessageBox.critical(
                self,
                "Error",
                f"Operation failed:\n\n{result.message}"
            )
