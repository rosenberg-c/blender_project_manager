"""Dialog for tracking operation progress."""

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QProgressBar, QTextEdit, QPushButton
)


class OperationProgressDialog(QDialog):
    """Dialog showing progress of long-running operations."""

    def __init__(self, operation_name: str, parent=None):
        """Initialize progress dialog.

        Args:
            operation_name: Name of the operation being performed
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(operation_name)
        self.setModal(True)
        self.resize(600, 400)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel("Starting...")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Log text area
        log_label = QLabel("<b>Log:</b>")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Close button (initially disabled)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        layout.addWidget(self.close_button)

    def update_progress(self, percentage: int, message: str):
        """Update progress bar and log.

        Args:
            percentage: Progress percentage (0-100)
            message: Status message to display
        """
        self.progress_bar.setValue(percentage)
        self.status_label.setText(message)
        self.log_text.append(f"[{percentage}%] {message}")

        # Enable close button when complete
        if percentage >= 100:
            self.close_button.setEnabled(True)
            self.status_label.setText("✓ Complete!")

    def mark_error(self, error_message: str):
        """Mark operation as failed.

        Args:
            error_message: Error message to display
        """
        self.progress_bar.setValue(0)
        self.status_label.setText(f"❌ Error: {error_message}")
        self.log_text.append(f"\n❌ ERROR: {error_message}")
        self.close_button.setEnabled(True)
