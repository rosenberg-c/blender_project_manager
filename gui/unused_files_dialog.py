"""Dialog for displaying and managing unused files in the project."""

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QMessageBox,
    QCheckBox, QWidget
)
from PySide6.QtGui import QColor

from send2trash import send2trash


class UnusedFilesDialog(QDialog):
    """Dialog showing unused files found in the project."""

    files_deleted = Signal(list)

    def __init__(self, results: dict, project_root: Path, parent=None):
        """Initialize unused files dialog.

        Args:
            results: Dictionary with unused files results
            project_root: Path to project root directory
            parent: Parent widget
        """
        super().__init__(parent)
        self.results = results
        self.project_root = project_root
        self.unused_files = results.get("unused_files", [])

        self.setWindowTitle("Unused Files")
        self.resize(1100, 700)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        total_unused = len(self.unused_files)
        total_size = self.results.get("total_unused_size", 0)
        unused_by_type = self.results.get("unused_by_type", {})
        errors = self.results.get("errors", [])
        warnings = self.results.get("warnings", [])

        if total_unused == 0:
            header = QLabel("<h2>No Unused Files Found</h2>")
            layout.addWidget(header)

            desc = QLabel("<i>All files in your project are referenced by at least one .blend file.</i>")
            layout.addWidget(desc)

            layout.addStretch()

        else:
            header = QLabel("<h2>Unused Files Found</h2>")
            layout.addWidget(header)

            # Summary stats
            size_mb = total_size / (1024 * 1024)
            summary_text = f"<b>{total_unused} unused file(s)</b> totaling <b>{size_mb:.2f} MB</b>"

            textures = unused_by_type.get('texture', 0)
            blends = unused_by_type.get('blend', 0)
            backups = unused_by_type.get('backup', 0)

            if textures > 0:
                summary_text += f"<br>• {textures} texture file(s)"
            if blends > 0:
                summary_text += f"<br>• {blends} .blend file(s)"
            if backups > 0:
                summary_text += f"<br>• {backups} backup file(s)"

            self.summary_label = QLabel(summary_text)
            layout.addWidget(self.summary_label)

            if warnings:
                for warning in warnings[:2]:
                    warning_text = QLabel(f"⚠️ {warning}")
                    warning_text.setStyleSheet("color: orange;")
                    layout.addWidget(warning_text)

            if errors:
                for error in errors[:2]:
                    error_text = QLabel(f"❌ {error}")
                    error_text.setStyleSheet("color: red;")
                    layout.addWidget(error_text)

            # Description
            desc = QLabel(
                "<i>These files are not referenced by any .blend file in your project. "
                "Select files to delete them.</i>"
            )
            desc.setWordWrap(True)
            layout.addWidget(desc)

            # Selection controls
            controls_layout = QHBoxLayout()

            self.select_all_btn = QPushButton("Select All")
            self.select_all_btn.clicked.connect(self._select_all)
            controls_layout.addWidget(self.select_all_btn)

            self.select_none_btn = QPushButton("Select None")
            self.select_none_btn.clicked.connect(self._select_none)
            controls_layout.addWidget(self.select_none_btn)

            controls_layout.addStretch()

            # Filter buttons
            self.show_textures_check = QCheckBox("Textures")
            self.show_textures_check.setChecked(True)
            self.show_textures_check.stateChanged.connect(self._apply_filters)
            controls_layout.addWidget(self.show_textures_check)

            self.show_blends_check = QCheckBox(".blend files")
            self.show_blends_check.setChecked(True)
            self.show_blends_check.stateChanged.connect(self._apply_filters)
            controls_layout.addWidget(self.show_blends_check)

            self.show_backups_check = QCheckBox("Backups")
            self.show_backups_check.setChecked(True)
            self.show_backups_check.stateChanged.connect(self._apply_filters)
            controls_layout.addWidget(self.show_backups_check)

            layout.addLayout(controls_layout)

            # Table with unused files
            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["", "File Name", "Type", "Size", "Location"])
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setAlternatingRowColors(True)

            # Populate table
            self._populate_table()

            layout.addWidget(self.table)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if total_unused > 0:
            self.delete_btn = QPushButton("Delete Selected")
            self.delete_btn.clicked.connect(self._delete_selected)
            self.delete_btn.setStyleSheet("background-color: #d32f2f; color: white;")
            button_layout.addWidget(self.delete_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _populate_table(self):
        """Populate table with unused files."""
        self.table.setRowCount(len(self.unused_files))

        for row, file_info in enumerate(self.unused_files):
            # Checkbox
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, checkbox_widget)

            # File name
            name_item = QTableWidgetItem(file_info["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, file_info)  # Store full file info
            self.table.setItem(row, 1, name_item)

            # Type
            file_type = file_info["type"].capitalize()
            type_item = QTableWidgetItem(file_type)

            # Color code by type
            if file_info["type"] == "texture":
                type_item.setForeground(QColor("#2196F3"))  # Blue
            elif file_info["type"] == "blend":
                type_item.setForeground(QColor("#FF9800"))  # Orange
            elif file_info["type"] == "backup":
                type_item.setForeground(QColor("#9E9E9E"))  # Gray

            self.table.setItem(row, 2, type_item)

            # Size
            size_bytes = file_info["size"]
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, size_item)

            # Location
            location_item = QTableWidgetItem(file_info["relative_path"])
            self.table.setItem(row, 4, location_item)

    def _apply_filters(self):
        """Apply type filters to table rows."""
        show_textures = self.show_textures_check.isChecked()
        show_blends = self.show_blends_check.isChecked()
        show_backups = self.show_backups_check.isChecked()

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            if name_item:
                file_info = name_item.data(Qt.ItemDataRole.UserRole)
                file_type = file_info["type"]

                should_show = (
                    (file_type == "texture" and show_textures) or
                    (file_type == "blend" and show_blends) or
                    (file_type == "backup" and show_backups)
                )

                self.table.setRowHidden(row, not should_show)

    def _select_all(self):
        """Select all visible checkboxes."""
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(True)

    def _select_none(self):
        """Deselect all checkboxes."""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)

    def _get_selected_files(self):
        """Get list of selected file paths."""
        selected = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox_widget = self.table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        name_item = self.table.item(row, 1)
                        if name_item:
                            file_info = name_item.data(Qt.ItemDataRole.UserRole)
                            selected.append(file_info)
        return selected

    def _delete_selected(self):
        """Delete selected files after confirmation."""
        selected_files = self._get_selected_files()

        if not selected_files:
            QMessageBox.warning(
                self,
                "No Files Selected",
                "Please select files to delete."
            )
            return

        # Count by type
        textures = sum(1 for f in selected_files if f["type"] == "texture")
        blends = sum(1 for f in selected_files if f["type"] == "blend")
        backups = sum(1 for f in selected_files if f["type"] == "backup")

        # Build warning message
        msg_parts = [f"You are about to delete {len(selected_files)} file(s):"]
        if textures > 0:
            msg_parts.append(f"• {textures} texture file(s)")
        if blends > 0:
            msg_parts.append(f"• {blends} .blend file(s)")
        if backups > 0:
            msg_parts.append(f"• {backups} backup file(s)")

        msg_parts.append("\nFiles will be moved to the trash/recycle bin.")

        if blends > 0:
            msg_parts.append("\n⚠️ WARNING: You are deleting .blend files! Make sure these are truly unused.")

        msg_parts.append("\nContinue with deletion?")

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "\n".join(msg_parts),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete files
        deleted_files = []
        errors = []

        for file_info in selected_files:
            file_path = Path(file_info["path"])
            try:
                if file_path.exists():
                    send2trash(str(file_path))
                    deleted_files.append(file_info["path"])
                else:
                    errors.append(f"File not found: {file_info['name']}")
            except Exception as e:
                errors.append(f"Failed to delete {file_info['name']}: {str(e)}")

        # Show result
        if deleted_files:
            msg = f"Successfully moved {len(deleted_files)} file(s) to trash."
            if errors:
                msg += f"\n\n{len(errors)} error(s) occurred."

            QMessageBox.information(self, "Deletion Complete", msg)

            # Emit signal and close
            self.files_deleted.emit(deleted_files)
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Deletion Failed",
                f"Failed to delete files:\n" + "\n".join(errors[:5])
            )
