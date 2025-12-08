"""Dialog for displaying broken links results."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QColor


class BrokenLinksDialog(QDialog):
    """Dialog showing broken links found in .blend files."""

    def __init__(self, results: dict, parent=None):
        """Initialize broken links dialog.

        Args:
            results: Dictionary with broken links results from Blender script
            parent: Parent widget
        """
        super().__init__(parent)
        self.results = results

        self.setWindowTitle("Broken Links Results")
        self.resize(1000, 600)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        files_with_broken_links = self.results.get("files_with_broken_links", [])
        total_files_checked = self.results.get("total_files_checked", 0)
        total_broken_links = self.results.get("total_broken_links", 0)
        errors = self.results.get("errors", [])
        warnings = self.results.get("warnings", [])

        if total_broken_links == 0:
            header = QLabel("<h2>No Broken Links Found</h2>")
            layout.addWidget(header)

            summary = QLabel(f"<b>Checked {total_files_checked} .blend file(s)</b>")
            layout.addWidget(summary)

            desc = QLabel("<i>All library and texture references are valid.</i>")
            layout.addWidget(desc)

            layout.addStretch()

        else:
            header = QLabel("<h2>Broken Links Found</h2>")
            layout.addWidget(header)

            summary_text = f"<b>{total_broken_links} broken link(s)</b> found in <b>{len(files_with_broken_links)} file(s)</b>"
            summary_text += f" (checked {total_files_checked} files total)"

            if warnings:
                summary_text += f" <span style='color: orange;'>{len(warnings)} warnings</span>"

            if errors:
                summary_text += f" <span style='color: red;'>{len(errors)} errors</span>"

            summary = QLabel(summary_text)
            layout.addWidget(summary)

            if errors:
                errors_label = QLabel("<b>Errors:</b>")
                layout.addWidget(errors_label)

                for error in errors[:3]:
                    error_text = QLabel(f"❌ {error}")
                    error_text.setStyleSheet("color: red;")
                    layout.addWidget(error_text)

                if len(errors) > 3:
                    more_label = QLabel(f"<i>... and {len(errors) - 3} more errors</i>")
                    layout.addWidget(more_label)

            if warnings:
                warnings_label = QLabel("<b>Warnings:</b>")
                layout.addWidget(warnings_label)

                for warning in warnings[:3]:
                    warning_text = QLabel(f"⚠️ {warning}")
                    warning_text.setStyleSheet("color: orange;")
                    layout.addWidget(warning_text)

                if len(warnings) > 3:
                    more_label = QLabel(f"<i>... and {len(warnings) - 3} more warnings</i>")
                    layout.addWidget(more_label)

            table_label = QLabel("<b>Broken Links:</b>")
            layout.addWidget(table_label)

            self.table = QTableWidget()
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels([
                "File", "Link Type", "Name", "Missing Path", "Details"
            ])

            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

            rows_data = []
            for file_info in files_with_broken_links:
                file_name = file_info.get("file_name", "Unknown")
                broken_libraries = file_info.get("broken_libraries", [])
                broken_textures = file_info.get("broken_textures", [])

                for lib in broken_libraries:
                    lib_name = lib.get("library_name", "Unknown")
                    lib_path = lib.get("library_filepath", "Unknown")
                    resolved_path = lib.get("resolved_path", "")
                    objects_count = lib.get("objects_count", 0)
                    collections_count = lib.get("collections_count", 0)

                    details_parts = []
                    if objects_count > 0:
                        details_parts.append(f"{objects_count} object(s)")
                    if collections_count > 0:
                        details_parts.append(f"{collections_count} collection(s)")
                    details = ", ".join(details_parts) if details_parts else "No items"

                    rows_data.append({
                        "file": file_name,
                        "type": "Library",
                        "name": lib_name,
                        "path": resolved_path or lib_path,
                        "details": details,
                        "status": "error"
                    })

                for tex in broken_textures:
                    tex_name = tex.get("image_name", "Unknown")
                    tex_path = tex.get("image_filepath", "Unknown")
                    resolved_path = tex.get("resolved_path", "")
                    users_count = tex.get("users_count", 0)

                    details = f"{users_count} user(s)" if users_count > 0 else "No users"

                    rows_data.append({
                        "file": file_name,
                        "type": "Texture",
                        "name": tex_name,
                        "path": resolved_path or tex_path,
                        "details": details,
                        "status": "error"
                    })

            self.table.setRowCount(len(rows_data))

            for i, row_data in enumerate(rows_data):
                file_item = QTableWidgetItem(row_data["file"])
                self.table.setItem(i, 0, file_item)

                type_item = QTableWidgetItem(row_data["type"])
                self.table.setItem(i, 1, type_item)

                name_item = QTableWidgetItem(row_data["name"])
                self.table.setItem(i, 2, name_item)

                path_item = QTableWidgetItem(row_data["path"])
                self.table.setItem(i, 3, path_item)

                details_item = QTableWidgetItem(row_data["details"])
                self.table.setItem(i, 4, details_item)

                if row_data["status"] == "error":
                    for col in range(5):
                        self.table.item(i, col).setBackground(QColor(255, 230, 230))
                        self.table.item(i, col).setForeground(QColor(139, 0, 0))

            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

            layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setProperty("class", "primary")
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
