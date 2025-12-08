"""Dialog for displaying file references in a table format."""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class FileReferencesDialog(QDialog):
    """Dialog to display files that reference a target file in a table."""

    def __init__(self, filename: str, file_type: str, referencing_files: list,
                 files_scanned: int, parent=None):
        """Initialize the dialog.

        Args:
            filename: Name of the target file
            file_type: Type of file ("blend" or "texture")
            referencing_files: List of files that reference the target
            files_scanned: Total number of files scanned
            parent: Parent widget
        """
        super().__init__(parent)
        self.filename = filename
        self.file_type = file_type
        self.referencing_files = referencing_files
        self.files_scanned = files_scanned

        self.setup_ui()

    def setup_ui(self):
        """Create the UI layout."""
        self.setWindowTitle(f"References to {self.filename}")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # Header label
        header_label = QLabel(
            f"Found {len(self.referencing_files)} file(s) referencing '{self.filename}'"
        )
        header_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(header_label)

        # Create table
        self.table = QTableWidget()

        if self.file_type == "texture":
            # For textures: show file name and usage count
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels([
                "File Name", "Times Used", "Used As"
            ])
        else:
            # For .blend files: show file name, objects, and collections
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels([
                "File Name", "Linked Objects", "Linked Collections", "Path"
            ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            self.table.columnCount() - 1,
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._populate_table()
        layout.addWidget(self.table)

        # Footer label
        footer_label = QLabel(f"Scanned {self.files_scanned} file(s)")
        footer_label.setStyleSheet("color: gray;")
        layout.addWidget(footer_label)

        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _populate_table(self):
        """Populate the table with referencing files."""
        self.table.setRowCount(len(self.referencing_files))

        for row, ref_file in enumerate(self.referencing_files):
            file_name = ref_file.get("file_name", "Unknown")

            if self.file_type == "texture":
                # Texture references
                # File name
                name_item = QTableWidgetItem(file_name)
                self.table.setItem(row, 0, name_item)

                # Times used
                images_count = ref_file.get("images_count", 0)
                count_item = QTableWidgetItem(str(images_count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, count_item)

                # Used as (image names)
                images = ref_file.get("images", [])
                if images:
                    image_names = [img.get("name", "") for img in images[:3]]
                    used_as = ', '.join(image_names)
                    if len(images) > 3:
                        used_as += f"... (+{len(images) - 3} more)"
                else:
                    used_as = ""
                used_item = QTableWidgetItem(used_as)
                self.table.setItem(row, 2, used_item)

            else:
                # .blend file references
                # File name
                name_item = QTableWidgetItem(file_name)
                self.table.setItem(row, 0, name_item)

                # Linked objects
                linked_objects = ref_file.get("linked_objects", [])
                objects_count = len(linked_objects)
                if objects_count > 0:
                    obj_preview = ', '.join(linked_objects[:3])
                    if len(linked_objects) > 3:
                        obj_preview += "..."
                    objects_text = f"{objects_count} ({obj_preview})"
                else:
                    objects_text = "0"
                objects_item = QTableWidgetItem(objects_text)
                self.table.setItem(row, 1, objects_item)

                # Linked collections
                linked_collections = ref_file.get("linked_collections", [])
                collections_count = len(linked_collections)
                if collections_count > 0:
                    col_preview = ', '.join(linked_collections[:3])
                    if len(linked_collections) > 3:
                        col_preview += "..."
                    collections_text = f"{collections_count} ({col_preview})"
                else:
                    collections_text = "0"
                collections_item = QTableWidgetItem(collections_text)
                self.table.setItem(row, 2, collections_item)

                # Path
                file_path = ref_file.get("file", "")
                path_item = QTableWidgetItem(file_path)
                self.table.setItem(row, 3, path_item)
