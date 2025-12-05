"""Dialog for previewing operation changes."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView
)
from PySide6.QtGui import QColor

from blender_lib.models import OperationPreview


class OperationPreviewDialog(QDialog):
    """Dialog showing preview of changes before execution."""

    def __init__(self, preview: OperationPreview, parent=None):
        """Initialize preview dialog.

        Args:
            preview: OperationPreview object with changes to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.preview = preview

        self.setWindowTitle("Preview Changes")
        self.resize(900, 600)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"<h2>{self.preview.operation_name}</h2>")
        layout.addWidget(header)

        # Summary
        summary_text = f"<b>{self.preview.total_changes} changes</b> will be made."

        if self.preview.warnings:
            summary_text += f" <span style='color: orange;'>{len(self.preview.warnings)} warnings</span>"

        if self.preview.errors:
            summary_text += f" <span style='color: red;'>{len(self.preview.errors)} errors</span>"

        summary = QLabel(summary_text)
        layout.addWidget(summary)

        # Errors (if any)
        if self.preview.errors:
            errors_label = QLabel("<b>Errors:</b>")
            layout.addWidget(errors_label)

            for error in self.preview.errors:
                error_text = QLabel(f"❌ {error}")
                error_text.setStyleSheet("color: red;")
                layout.addWidget(error_text)

        # Warnings (if any)
        if self.preview.warnings:
            warnings_label = QLabel("<b>Warnings:</b>")
            layout.addWidget(warnings_label)

            for warning in self.preview.warnings:
                warning_text = QLabel(f"⚠️ {warning}")
                warning_text.setStyleSheet("color: orange;")
                layout.addWidget(warning_text)

        # Changes table
        if self.preview.changes:
            changes_label = QLabel("<b>Changes:</b>")
            layout.addWidget(changes_label)

            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels([
                "File", "Type", "Item Name", "Old Path", "New Path"
            ])

            self.table.setRowCount(len(self.preview.changes))

            for i, change in enumerate(self.preview.changes):
                # File
                file_item = QTableWidgetItem(change.file_path.name)
                self.table.setItem(i, 0, file_item)

                # Type
                type_item = QTableWidgetItem(change.item_type)
                self.table.setItem(i, 1, type_item)

                # Item name
                name_item = QTableWidgetItem(change.item_name)
                self.table.setItem(i, 2, name_item)

                # Old path
                old_item = QTableWidgetItem(change.old_path)
                self.table.setItem(i, 3, old_item)

                # New path
                new_item = QTableWidgetItem(change.new_path)
                self.table.setItem(i, 4, new_item)

                # Color code by status
                if change.status == 'warning':
                    for col in range(5):
                        self.table.item(i, col).setBackground(QColor(255, 250, 205))  # Light yellow
                        self.table.item(i, col).setForeground(QColor(139, 69, 19))    # Dark brown text
                elif change.status == 'error':
                    for col in range(5):
                        self.table.item(i, col).setBackground(QColor(255, 230, 230))  # Light red
                        self.table.item(i, col).setForeground(QColor(139, 0, 0))      # Dark red text
                elif change.status == 'ok':
                    for col in range(5):
                        self.table.item(i, col).setBackground(QColor(230, 255, 230))  # Light green
                        self.table.item(i, col).setForeground(QColor(0, 100, 0))      # Dark green text

            # Resize columns to fit content
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setStretchLastSection(True)

            layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
