"""Dialog for displaying linked files in a table format."""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class FileLinksDialog(QDialog):
    """Dialog to display linked files (libraries, textures, and materials) in a table."""

    def __init__(self, filename: str, linked_libraries: list, linked_textures: list, linked_materials: list = None, parent=None):
        """Initialize the dialog.

        Args:
            filename: Name of the .blend file
            linked_libraries: List of linked library dictionaries
            linked_textures: List of linked texture dictionaries
            linked_materials: List of linked material dictionaries
            parent: Parent widget
        """
        super().__init__(parent)
        self.filename = filename
        self.linked_libraries = linked_libraries
        self.linked_textures = linked_textures
        self.linked_materials = linked_materials or []

        self.setup_ui()

    def setup_ui(self):
        """Create the UI layout."""
        self.setWindowTitle(f"Linked Files - {self.filename}")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Header label
        header_label = QLabel(f"Files linked by '{self.filename}':")
        header_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(header_label)

        # Libraries section
        if self.linked_libraries:
            lib_label = QLabel(f"📦 Linked Libraries ({len(self.linked_libraries)}):")
            lib_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(lib_label)

            self.libraries_table = QTableWidget()
            self.libraries_table.setColumnCount(5)
            self.libraries_table.setHorizontalHeaderLabels([
                "Status", "Library Name", "Objects", "Collections", "Path"
            ])
            self.libraries_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.libraries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            self.libraries_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.libraries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            self._populate_libraries_table()
            layout.addWidget(self.libraries_table)

        # Textures section
        if self.linked_textures:
            tex_label = QLabel(f"🖼️  Linked Textures ({len(self.linked_textures)}):")
            tex_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(tex_label)

            self.textures_table = QTableWidget()
            self.textures_table.setColumnCount(3)
            self.textures_table.setHorizontalHeaderLabels([
                "Status", "Texture Name", "Path"
            ])
            self.textures_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.textures_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            self.textures_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.textures_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            self._populate_textures_table()
            layout.addWidget(self.textures_table)

        if self.linked_materials:
            mat_label = QLabel(f"🎨 Materials ({len(self.linked_materials)}):")
            mat_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(mat_label)

            self.materials_table = QTableWidget()
            self.materials_table.setColumnCount(3)
            self.materials_table.setHorizontalHeaderLabels([
                "Material Name", "Uses Nodes", "Users"
            ])
            self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            self.materials_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.materials_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.materials_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            self._populate_materials_table()
            layout.addWidget(self.materials_table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _populate_libraries_table(self):
        """Populate the libraries table with data."""
        self.libraries_table.setRowCount(len(self.linked_libraries))

        for row, lib in enumerate(self.linked_libraries):
            # Status
            exists = lib.get("exists", False)
            status_item = QTableWidgetItem("✓ OK" if exists else "✗ MISSING")
            if not exists:
                status_item.setForeground(QColor(200, 50, 50))  # Red for missing
            else:
                status_item.setForeground(QColor(50, 150, 50))  # Green for OK
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.libraries_table.setItem(row, 0, status_item)

            # Library name
            name_item = QTableWidgetItem(lib.get("name", "Unknown"))
            self.libraries_table.setItem(row, 1, name_item)

            # Objects count with preview
            objects_count = lib.get("objects_count", 0)
            linked_objects = lib.get("linked_objects", [])
            if objects_count > 0:
                obj_preview = ', '.join(linked_objects[:3])
                if len(linked_objects) > 3:
                    obj_preview += "..."
                objects_text = f"{objects_count} ({obj_preview})"
            else:
                objects_text = "0"
            objects_item = QTableWidgetItem(objects_text)
            self.libraries_table.setItem(row, 2, objects_item)

            # Collections count with preview
            collections_count = lib.get("collections_count", 0)
            linked_collections = lib.get("linked_collections", [])
            if collections_count > 0:
                col_preview = ', '.join(linked_collections[:3])
                if len(linked_collections) > 3:
                    col_preview += "..."
                collections_text = f"{collections_count} ({col_preview})"
            else:
                collections_text = "0"
            collections_item = QTableWidgetItem(collections_text)
            self.libraries_table.setItem(row, 3, collections_item)

            # Path
            path_item = QTableWidgetItem(lib.get("filepath", ""))
            path_item.setToolTip(lib.get("absolute_path", ""))
            self.libraries_table.setItem(row, 4, path_item)

    def _populate_textures_table(self):
        """Populate the textures table with data."""
        self.textures_table.setRowCount(len(self.linked_textures))

        for row, texture in enumerate(self.linked_textures):
            # Status
            exists = texture.get("exists", False)
            status_item = QTableWidgetItem("✓ OK" if exists else "✗ MISSING")
            if not exists:
                status_item.setForeground(QColor(200, 50, 50))  # Red for missing
            else:
                status_item.setForeground(QColor(50, 150, 50))  # Green for OK
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.textures_table.setItem(row, 0, status_item)

            # Texture name
            name_item = QTableWidgetItem(texture.get("name", "Unknown"))
            self.textures_table.setItem(row, 1, name_item)

            # Path
            path_item = QTableWidgetItem(texture.get("filepath", ""))
            path_item.setToolTip(texture.get("absolute_path", ""))
            self.textures_table.setItem(row, 2, path_item)

    def _populate_materials_table(self):
        """Populate the materials table with data."""
        self.materials_table.setRowCount(len(self.linked_materials))

        for row, material in enumerate(self.linked_materials):
            name_item = QTableWidgetItem(material.get("name", "Unknown"))
            self.materials_table.setItem(row, 0, name_item)

            use_nodes_item = QTableWidgetItem("Yes" if material.get("use_nodes", False) else "No")
            use_nodes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.materials_table.setItem(row, 1, use_nodes_item)

            users_item = QTableWidgetItem(str(material.get("users", 0)))
            users_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.materials_table.setItem(row, 2, users_item)
