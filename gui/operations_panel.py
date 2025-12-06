"""Operations panel for file operations."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QApplication,
    QTabWidget, QListWidget, QListWidgetItem, QComboBox, QCheckBox, QRadioButton, QButtonGroup
)
from PySide6.QtGui import QCursor

from controllers.file_operations_controller import FileOperationsController
from gui.preview_dialog import OperationPreviewDialog
from gui.progress_dialog import OperationProgressDialog
from gui.theme import Theme


class OperationsPanelWidget(QWidget):
    """Panel for configuring and executing file operations."""

    def __init__(self, controller: FileOperationsController, config_file: Path = None, parent=None):
        """Initialize operations panel.

        Args:
            controller: File operations controller
            config_file: Path to config file for state persistence
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.config_file = config_file
        self.current_file: Path | None = None
        self.obj_list_data = {"objects": [], "collections": []}
        self.link_source_data = {"objects": [], "collections": []}
        self.link_scenes = []
        self.link_locked_file: Path | None = None  # Track locked target file
        self.pending_locked_file_restore = None  # Deferred restoration data

        self.setup_ui()
        self._restore_link_state()

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
        self.file_display.setStyleSheet(Theme.get_file_display_style())
        layout.addWidget(self.file_display)

        # Separator
        layout.addSpacing(10)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs
        self.create_move_tab()
        self.create_rename_objects_tab()
        self.create_rename_texture_tab()
        self.create_link_tab()

    def create_move_tab(self):
        """Create the Move/Rename file tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # Move/Rename section
        move_label = QLabel("<b>Move/Rename File:</b>")
        tab_layout.addWidget(move_label)

        # New path input
        new_path_label = QLabel("New path:")
        tab_layout.addWidget(new_path_label)

        self.new_path_input = QLineEdit()
        self.new_path_input.setPlaceholderText("Enter new path...")
        tab_layout.addWidget(self.new_path_input)

        # Browse and Preview buttons
        btn_row1 = QHBoxLayout()

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_new_path)
        self.browse_btn.setEnabled(False)
        btn_row1.addWidget(self.browse_btn)

        self.preview_btn = QPushButton("Preview Changes")
        self.preview_btn.clicked.connect(self._preview_operation)
        self.preview_btn.setEnabled(False)
        self.preview_btn.setProperty("class", "info")
        btn_row1.addWidget(self.preview_btn)

        tab_layout.addLayout(btn_row1)

        # Execute button
        self.execute_btn = QPushButton("Execute Move")
        self.execute_btn.clicked.connect(self._execute_operation)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setProperty("class", "primary")
        tab_layout.addWidget(self.execute_btn)

        # Add stretch to push everything to top
        tab_layout.addStretch()

        # Add tab to tabs widget
        self.tabs.addTab(tab, "Move/Rename File")

    def create_rename_objects_tab(self):
        """Create the Rename Objects/Collections tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        info_label = QLabel("<b>Rename Objects/Collections:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Select items from the .blend file to rename.")
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(5)

        # Type filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Show:")
        filter_layout.addWidget(filter_label)

        self.obj_type_combo = QComboBox()
        self.obj_type_combo.addItems(["All", "Objects", "Collections"])
        self.obj_type_combo.currentTextChanged.connect(self._filter_objects_list)
        filter_layout.addWidget(self.obj_type_combo)

        # Load button
        self.obj_load_btn = QPushButton("Load Items")
        self.obj_load_btn.setEnabled(False)
        self.obj_load_btn.clicked.connect(self._load_objects)
        filter_layout.addWidget(self.obj_load_btn)

        filter_layout.addStretch()
        tab_layout.addLayout(filter_layout)

        # List of objects/collections
        list_label = QLabel("Items in file:")
        tab_layout.addWidget(list_label)

        self.obj_list = QListWidget()
        self.obj_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.obj_list.itemSelectionChanged.connect(self._on_object_selection_changed)
        tab_layout.addWidget(self.obj_list)

        # Rename section
        rename_label = QLabel("Rename selected items:")
        tab_layout.addWidget(rename_label)

        rename_layout = QHBoxLayout()

        # Find pattern
        find_label = QLabel("Find:")
        rename_layout.addWidget(find_label)

        self.obj_find_input = QLineEdit()
        self.obj_find_input.setPlaceholderText("Text to find...")
        rename_layout.addWidget(self.obj_find_input)

        # Replace pattern
        replace_label = QLabel("Replace:")
        rename_layout.addWidget(replace_label)

        self.obj_replace_input = QLineEdit()
        self.obj_replace_input.setPlaceholderText("Replace with...")
        rename_layout.addWidget(self.obj_replace_input)

        tab_layout.addLayout(rename_layout)

        # Buttons
        btn_row = QHBoxLayout()

        self.obj_preview_btn = QPushButton("Preview Changes")
        self.obj_preview_btn.setEnabled(False)
        self.obj_preview_btn.setProperty("class", "info")
        self.obj_preview_btn.clicked.connect(self._preview_rename_objects)
        btn_row.addWidget(self.obj_preview_btn)

        tab_layout.addLayout(btn_row)

        self.obj_execute_btn = QPushButton("Execute Rename")
        self.obj_execute_btn.setEnabled(False)
        self.obj_execute_btn.setProperty("class", "primary")
        self.obj_execute_btn.clicked.connect(self._execute_rename_objects)
        tab_layout.addWidget(self.obj_execute_btn)

        # Add stretch
        tab_layout.addStretch()

        # Add tab to tabs widget
        self.tabs.addTab(tab, "Rename Objects")

    def create_rename_texture_tab(self):
        """Create the Rename Texture tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        info_label = QLabel("<b>Rename Texture:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Rename a texture file and update all references in .blend files.")
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(10)

        # Current texture path
        current_label = QLabel("Current texture path:")
        tab_layout.addWidget(current_label)

        self.tex_current_input = QLineEdit()
        self.tex_current_input.setPlaceholderText("Path to texture file...")
        self.tex_current_input.setReadOnly(True)
        tab_layout.addWidget(self.tex_current_input)

        # New texture path
        new_label = QLabel("New texture path:")
        tab_layout.addWidget(new_label)

        self.tex_new_input = QLineEdit()
        self.tex_new_input.setPlaceholderText("New path for texture...")
        tab_layout.addWidget(self.tex_new_input)

        # Buttons
        btn_row = QHBoxLayout()

        self.tex_browse_btn = QPushButton("Browse...")
        self.tex_browse_btn.setEnabled(False)
        self.tex_browse_btn.clicked.connect(self._browse_new_texture_path)
        btn_row.addWidget(self.tex_browse_btn)

        self.tex_preview_btn = QPushButton("Preview Changes")
        self.tex_preview_btn.setEnabled(False)
        self.tex_preview_btn.setProperty("class", "info")
        self.tex_preview_btn.clicked.connect(self._preview_rename_texture)
        btn_row.addWidget(self.tex_preview_btn)

        tab_layout.addLayout(btn_row)

        self.tex_execute_btn = QPushButton("Execute Rename")
        self.tex_execute_btn.setEnabled(False)
        self.tex_execute_btn.setProperty("class", "primary")
        self.tex_execute_btn.clicked.connect(self._execute_rename_texture)
        tab_layout.addWidget(self.tex_execute_btn)

        # Add stretch
        tab_layout.addStretch()

        # Add tab to tabs widget
        self.tabs.addTab(tab, "Rename Texture")

    def create_link_tab(self):
        """Create the Link Objects/Collections tab."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        info_label = QLabel("<b>Link Objects/Collections:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Link objects/collections from another .blend file into this file.")
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(10)

        # TARGET SECTION
        target_section_label = QLabel("<b>Target (Link into):</b>")
        tab_layout.addWidget(target_section_label)

        # Target file display
        target_file_label = QLabel("Target file:")
        tab_layout.addWidget(target_file_label)

        self.link_target_display = QLabel("<i>No .blend file selected</i>")
        self.link_target_display.setWordWrap(True)
        self.link_target_display.setStyleSheet(Theme.get_file_display_style())
        tab_layout.addWidget(self.link_target_display)

        # Scene selection with lock
        scene_layout = QHBoxLayout()
        scene_label = QLabel("Scene:")
        scene_layout.addWidget(scene_label)

        self.link_scene_combo = QComboBox()
        self.link_scene_combo.setEnabled(False)
        self.link_scene_combo.currentTextChanged.connect(self._on_scene_changed)
        scene_layout.addWidget(self.link_scene_combo, stretch=1)

        self.link_scene_lock = QCheckBox("🔒 Lock Target")
        self.link_scene_lock.setToolTip("Lock the target file and scene - you can only select a new target after unlocking")
        self.link_scene_lock.stateChanged.connect(self._on_scene_lock_changed)
        scene_layout.addWidget(self.link_scene_lock)

        tab_layout.addLayout(scene_layout)

        tab_layout.addSpacing(10)

        # SOURCE SECTION
        source_section_label = QLabel("<b>Source (Link from):</b>")
        tab_layout.addWidget(source_section_label)

        # Source file display (selected from file browser)
        source_file_label = QLabel("From file:")
        tab_layout.addWidget(source_file_label)

        self.link_source_display = QLabel("<i>Select a .blend file in the file browser</i>")
        self.link_source_display.setWordWrap(True)
        self.link_source_display.setStyleSheet(Theme.get_file_display_style())
        tab_layout.addWidget(self.link_source_display)

        self.link_source_file: Path | None = None  # Track source file

        # Load items button
        self.link_load_btn = QPushButton("Load Objects/Collections")
        self.link_load_btn.setEnabled(False)
        self.link_load_btn.clicked.connect(self._load_link_source)
        tab_layout.addWidget(self.link_load_btn)

        # Items list
        items_label = QLabel("Select items to link:")
        tab_layout.addWidget(items_label)

        self.link_items_list = QListWidget()
        self.link_items_list.setSelectionMode(QListWidget.ExtendedSelection)
        tab_layout.addWidget(self.link_items_list)

        tab_layout.addSpacing(5)

        # Link mode selection
        mode_label = QLabel("<b>Link Mode:</b>")
        tab_layout.addWidget(mode_label)

        self.link_mode_instance = QRadioButton("Link as collection instance (Blender default)")
        self.link_mode_instance.setToolTip("Creates a collection instance (orange) inside the target collection")
        self.link_mode_instance.setChecked(True)

        self.link_mode_individual = QRadioButton("Link individually into collection")
        self.link_mode_individual.setToolTip("Links each object/collection separately into the target collection")

        self.link_mode_group = QButtonGroup()
        self.link_mode_group.addButton(self.link_mode_instance, 0)
        self.link_mode_group.addButton(self.link_mode_individual, 1)

        self.link_mode_instance.toggled.connect(self._on_link_mode_changed)

        tab_layout.addWidget(self.link_mode_instance)
        tab_layout.addWidget(self.link_mode_individual)

        tab_layout.addSpacing(5)

        # Target collection (for both modes)
        collection_label = QLabel("Target collection name:")
        tab_layout.addWidget(collection_label)

        self.link_collection_input = QLineEdit()
        self.link_collection_input.setPlaceholderText("Collection to place linked items (created if needed)")
        tab_layout.addWidget(self.link_collection_input)

        self.collection_label = collection_label  # Store reference for enabling/disabling

        # Buttons
        btn_row = QHBoxLayout()

        self.link_preview_btn = QPushButton("Preview Link")
        self.link_preview_btn.setEnabled(False)
        self.link_preview_btn.setProperty("class", "info")
        self.link_preview_btn.clicked.connect(self._preview_link)
        btn_row.addWidget(self.link_preview_btn)

        tab_layout.addLayout(btn_row)

        self.link_execute_btn = QPushButton("Execute Link")
        self.link_execute_btn.setEnabled(False)
        self.link_execute_btn.setProperty("class", "primary")
        self.link_execute_btn.clicked.connect(self._execute_link)
        tab_layout.addWidget(self.link_execute_btn)

        # Add stretch
        tab_layout.addStretch()

        # Add tab to tabs widget
        self.tabs.addTab(tab, "Link Objects")

    def set_file(self, file_path: Path):
        """Set the currently selected file.

        Args:
            file_path: Path to the selected file
        """
        self.current_file = file_path
        self.file_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")

        # Determine file type
        is_blend = file_path.suffix == '.blend'
        is_texture = file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']

        # Update Move/Rename tab
        self.new_path_input.setText(str(file_path))
        self.browse_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)

        # Update Rename Objects tab (only for .blend files)
        if is_blend:
            self.obj_load_btn.setEnabled(True)
            self.obj_list.clear()
            # Clear the stored data
            self.obj_list_data = {"objects": [], "collections": []}
        else:
            self.obj_load_btn.setEnabled(False)
            self.obj_preview_btn.setEnabled(False)
            self.obj_execute_btn.setEnabled(False)
            self.obj_list.clear()
            self.obj_list_data = {"objects": [], "collections": []}

        # Update Rename Texture tab (for texture files)
        if is_texture:
            self.tex_current_input.setText(str(file_path))
            self.tex_new_input.setText(str(file_path))
            self.tex_browse_btn.setEnabled(True)
            self.tex_preview_btn.setEnabled(True)
            self.tex_execute_btn.setEnabled(True)
        else:
            self.tex_current_input.clear()
            self.tex_new_input.clear()
            self.tex_browse_btn.setEnabled(False)
            self.tex_preview_btn.setEnabled(False)
            self.tex_execute_btn.setEnabled(False)

        # Update Link tab (only for .blend files)
        if self.link_scene_lock.isChecked():
            # Target is locked - selected file becomes SOURCE
            if is_blend:
                self.link_source_file = file_path
                self.link_source_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")
                self.link_load_btn.setEnabled(True)
                # Clear previous items when source changes
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}
            else:
                # Non-.blend file selected, clear source
                self.link_source_file = None
                self.link_source_display.setText("<i>Select a .blend file in the file browser</i>")
                self.link_load_btn.setEnabled(False)
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}
        else:
            # Target is not locked - selected file becomes TARGET
            if is_blend:
                self.link_target_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")
                self._load_scenes_for_target()
                # Clear source since target changed
                self.link_source_file = None
                self.link_source_display.setText("<i>Select a .blend file in the file browser</i>")
                self.link_load_btn.setEnabled(False)
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}
            else:
                self.link_target_display.setText("<i>No .blend file selected</i>")
                self.link_scene_combo.clear()
                self.link_scene_combo.setEnabled(False)
                self.link_source_file = None
                self.link_source_display.setText("<i>Select a .blend file in the file browser</i>")
                self.link_load_btn.setEnabled(False)
                self.link_preview_btn.setEnabled(False)
                self.link_execute_btn.setEnabled(False)
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}

    def _load_objects(self):
        """Load objects and collections from the selected .blend file."""
        if not self.current_file or self.current_file.suffix != '.blend':
            return

        # Show loading state
        self.obj_load_btn.setText("Loading...")
        self.obj_load_btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            import traceback
            # Get the blender runner from controller
            from pathlib import Path as LibPath

            runner = self.controller.project.blender_service.runner
            script_path = LibPath(__file__).parent.parent / "blender_lib" / "list_objects.py"

            # Verify script exists
            if not script_path.exists():
                raise Exception(f"Script not found: {script_path}")

            # Run the script with blend file as argument
            result = runner.run_script(
                script_path,
                {"blend-file": str(self.current_file)},
                timeout=60
            )

            # Debug: print stdout
            print("=== Blender stdout ===")
            print(result.stdout)
            print("=== End stdout ===")

            # Parse JSON output
            from services.blender_service import extract_json_from_output
            data = extract_json_from_output(result.stdout)

            # Debug: print parsed data
            print(f"=== Parsed data type: {type(data)} ===")
            print(f"Data: {data}")

            # Validate data structure
            if not isinstance(data, dict):
                raise Exception(f"Expected dict from Blender script, got {type(data).__name__}: {data}")

            if "error" in data and data["error"]:
                raise Exception(data["error"])

            # Ensure we have the expected keys
            if "objects" not in data or "collections" not in data:
                raise Exception(f"Invalid data structure: {list(data.keys())}")

            # Store the data
            self.obj_list_data = data

            # Populate the list
            self._populate_objects_list()

            # Enable buttons
            self.obj_preview_btn.setEnabled(True)
            self.obj_execute_btn.setEnabled(True)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print("=== Full Error Traceback ===")
            print(error_details)
            print("=== End Traceback ===")

            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load objects/collections:\n\n{str(e)}\n\nFull error:\n{error_details}"
            )
        finally:
            # Restore state
            QApplication.restoreOverrideCursor()
            self.obj_load_btn.setText("Load Items")
            self.obj_load_btn.setEnabled(True)

    def _populate_objects_list(self):
        """Populate the list widget with objects and collections."""
        self.obj_list.clear()

        # Ensure obj_list_data is a valid dict
        if not isinstance(self.obj_list_data, dict):
            return

        filter_type = self.obj_type_combo.currentText()

        # Add objects
        if filter_type in ["All", "Objects"]:
            objects = self.obj_list_data.get("objects", [])
            if isinstance(objects, list):
                for obj in objects:
                    if isinstance(obj, dict):
                        item_text = f"🔷 {obj.get('name', 'Unknown')} ({obj.get('type', 'Unknown')})"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "object", "data": obj})
                        self.obj_list.addItem(item)

        # Add collections
        if filter_type in ["All", "Collections"]:
            collections = self.obj_list_data.get("collections", [])
            if isinstance(collections, list):
                for col in collections:
                    if isinstance(col, dict):
                        item_text = f"📁 {col.get('name', 'Unknown')} ({col.get('objects_count', 0)} objects)"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "collection", "data": col})
                        self.obj_list.addItem(item)

    def _filter_objects_list(self):
        """Filter the objects list based on combo box selection."""
        if isinstance(self.obj_list_data, dict) and (self.obj_list_data.get("objects") or self.obj_list_data.get("collections")):
            self._populate_objects_list()

    def _on_object_selection_changed(self):
        """Handle when objects/collections are selected in the list."""
        selected_items = self.obj_list.selectedItems()

        if not selected_items:
            # Clear if nothing selected
            self.obj_find_input.clear()
            return

        if len(selected_items) == 1:
            # Single selection - fill with exact name
            item_data = selected_items[0].data(Qt.UserRole)
            if item_data and "data" in item_data:
                name = item_data["data"].get("name", "")
                self.obj_find_input.setText(name)
        else:
            # Multiple selection - try to find common pattern
            names = []
            for item in selected_items:
                item_data = item.data(Qt.UserRole)
                if item_data and "data" in item_data:
                    names.append(item_data["data"].get("name", ""))

            # Find common prefix or suffix
            if names:
                # For now, just show the first name as a hint
                # User can modify to create a pattern
                self.obj_find_input.setText(names[0])

    def _preview_rename_objects(self):
        """Preview the rename operation for objects/collections."""
        self._rename_objects_internal(dry_run=True)

    def _execute_rename_objects(self):
        """Execute the rename operation for objects/collections."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            "This will rename the selected objects/collections in the .blend file.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self._rename_objects_internal(dry_run=False)

    def _rename_objects_internal(self, dry_run=True):
        """Internal method to handle rename preview/execute.

        Args:
            dry_run: If True, only preview changes
        """
        if not self.current_file or self.current_file.suffix != '.blend':
            QMessageBox.warning(self, "No File", "Please select a .blend file first.")
            return

        # Get selected items
        selected_items = self.obj_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select items to rename.")
            return

        # Get find/replace text
        find_text = self.obj_find_input.text().strip()
        replace_text = self.obj_replace_input.text().strip()

        if not find_text:
            QMessageBox.warning(self, "Missing Input", "Please enter text to find.")
            return

        # Extract item names
        item_names = []
        for item in selected_items:
            item_data = item.data(Qt.UserRole)
            if item_data and "data" in item_data:
                item_names.append(item_data["data"].get("name", ""))

        if not item_names:
            QMessageBox.warning(self, "No Items", "No valid items selected.")
            return

        # Show loading state
        btn = self.obj_preview_btn if dry_run else self.obj_execute_btn
        original_text = btn.text()
        btn.setText("Processing..." if dry_run else "Executing...")
        btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            from pathlib import Path as LibPath

            runner = self.controller.project.blender_service.runner
            script_path = LibPath(__file__).parent.parent / "blender_lib" / "rename_objects.py"

            # Get project root
            project_root = self.controller.project.project_root

            # Run the script
            result = runner.run_script(
                script_path,
                {
                    "blend-file": str(self.current_file),
                    "project-root": str(project_root),
                    "item-names": ",".join(item_names),
                    "find": find_text,
                    "replace": replace_text,
                    "dry-run": "true" if dry_run else "false"
                },
                timeout=120  # Longer timeout for processing multiple files
            )

            # Parse JSON output
            from services.blender_service import extract_json_from_output
            data = extract_json_from_output(result.stdout)

            if "error" in data and data["error"]:
                raise Exception(data["error"])

            # Show results
            renamed = data.get("renamed", [])
            warnings = data.get("warnings", [])
            errors = data.get("errors", [])
            updated_files_count = data.get("updated_files_count", 0)
            updated_files = data.get("updated_files", [])

            message_parts = []

            if dry_run:
                # Preview mode
                if renamed:
                    message_parts.append(f"<b>Will rename {len(renamed)} item(s) in this file:</b><br>")
                    for item in renamed[:10]:  # Show first 10
                        message_parts.append(
                            f"  • {item['old_name']} → {item['new_name']}<br>"
                        )
                    if len(renamed) > 10:
                        message_parts.append(f"  ... and {len(renamed) - 10} more<br>")

                    # Show files with linked references
                    if updated_files_count > 0:
                        message_parts.append(f"<br><b>Will update linked references in {updated_files_count} other file(s):</b><br>")
                        for file_path in updated_files[:10]:
                            from pathlib import Path
                            file_name = Path(file_path).name
                            message_parts.append(f"  • {file_name}<br>")
                        if len(updated_files) > 10:
                            message_parts.append(f"  ... and {len(updated_files) - 10} more<br>")
                else:
                    message_parts.append("<b>No items will be renamed.</b><br>")
            else:
                # Execute mode
                if renamed:
                    message_parts.append(f"<b>Successfully renamed {len(renamed)} item(s)!</b><br>")

                    if updated_files_count > 0:
                        message_parts.append(f"<br><b>Updated {updated_files_count} file(s) with linked references:</b><br>")
                        for file_path in updated_files[:10]:
                            from pathlib import Path
                            file_name = Path(file_path).name
                            message_parts.append(f"  • {file_name}<br>")
                        if len(updated_files) > 10:
                            message_parts.append(f"  ... and {len(updated_files) - 10} more<br>")

                    # Reload the list to show new names
                    self._load_objects()
                else:
                    message_parts.append("<b>No items were renamed.</b><br>")

            if warnings:
                message_parts.append(f"<br><b>Warnings:</b><br>")
                for warning in warnings[:5]:
                    message_parts.append(f"  • {warning}<br>")
                if len(warnings) > 5:
                    message_parts.append(f"  ... and {len(warnings) - 5} more<br>")

            if errors:
                message_parts.append(f"<br><b>Errors:</b><br>")
                for error in errors:
                    message_parts.append(f"  • {error}<br>")

            QMessageBox.information(
                self,
                "Preview Results" if dry_run else "Rename Complete",
                "".join(message_parts)
            )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print("=== Rename Error ===")
            print(error_details)

            QMessageBox.critical(
                self,
                "Rename Error",
                f"Failed to rename items:\n\n{str(e)}"
            )
        finally:
            # Restore state
            QApplication.restoreOverrideCursor()
            btn.setText(original_text)
            btn.setEnabled(True)

    def _browse_new_texture_path(self):
        """Open file dialog to select new texture path."""
        if not self.current_file:
            return

        # Show loading state
        self.tex_browse_btn.setText("Browsing...")
        self.tex_browse_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            new_path, _ = QFileDialog.getSaveFileName(
                self,
                "Select New Location for Texture",
                str(self.current_file),
                f"*{self.current_file.suffix}"
            )

            if new_path:
                self.tex_new_input.setText(new_path)

        finally:
            # Restore button state
            self.tex_browse_btn.setText("Browse...")
            self.tex_browse_btn.setEnabled(True)

    def _preview_rename_texture(self):
        """Preview the rename operation for texture file."""
        self._rename_texture_internal(dry_run=True)

    def _execute_rename_texture(self):
        """Execute the rename operation for texture file."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Rename",
            "This will rename/move the texture file and update all .blend file references.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self._rename_texture_internal(dry_run=False)

    def _rename_texture_internal(self, dry_run=True):
        """Internal method to handle texture rename preview/execute.

        Args:
            dry_run: If True, only preview changes
        """
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please select a texture file first.")
            return

        # Get old and new paths
        old_path = Path(self.tex_current_input.text().strip())
        new_path = Path(self.tex_new_input.text().strip())

        if not old_path or not new_path:
            QMessageBox.warning(self, "Missing Input", "Please specify both old and new paths.")
            return

        if old_path == new_path:
            QMessageBox.information(self, "No Change", "Old and new paths are the same.")
            return

        # Show loading state
        btn = self.tex_preview_btn if dry_run else self.tex_execute_btn
        original_text = btn.text()
        btn.setText("Processing..." if dry_run else "Executing...")
        btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            from pathlib import Path as LibPath

            runner = self.controller.project.blender_service.runner
            script_path = LibPath(__file__).parent.parent / "blender_lib" / "rename_texture.py"

            # Get project root
            project_root = self.controller.project.project_root

            # Run the script
            result = runner.run_script(
                script_path,
                {
                    "old-path": str(old_path),
                    "new-path": str(new_path),
                    "project-root": str(project_root),
                    "dry-run": "true" if dry_run else "false"
                },
                timeout=120
            )

            # Parse JSON output
            from services.blender_service import extract_json_from_output
            data = extract_json_from_output(result.stdout)

            if not data.get("success", False):
                errors = data.get("errors", [])
                raise Exception(errors[0] if errors else "Unknown error")

            # Show results
            updated_files = data.get("updated_files", [])
            updated_files_count = data.get("updated_files_count", 0)
            file_moved = data.get("file_moved", False)
            warnings = data.get("warnings", [])
            errors = data.get("errors", [])

            message_parts = []

            if dry_run:
                # Preview mode
                message_parts.append(f"<b>Will rename texture file:</b><br>")
                message_parts.append(f"  {old_path.name} → {new_path.name}<br>")

                if updated_files_count > 0:
                    message_parts.append(f"<br><b>Will update {updated_files_count} .blend file(s):</b><br>")
                    for file_info in updated_files[:5]:
                        file_name = Path(file_info["file"]).name
                        image_count = len(file_info["updated_images"])
                        message_parts.append(f"  • {file_name} ({image_count} image(s))<br>")
                    if len(updated_files) > 5:
                        message_parts.append(f"  ... and {len(updated_files) - 5} more<br>")
                else:
                    message_parts.append("<br><i>No .blend files reference this texture.</i><br>")
            else:
                # Execute mode
                if file_moved:
                    message_parts.append(f"<b>Successfully renamed texture file!</b><br>")
                else:
                    message_parts.append(f"<b>Texture file prepared for rename.</b><br>")

                if updated_files_count > 0:
                    message_parts.append(f"<br><b>Updated {updated_files_count} .blend file(s):</b><br>")
                    for file_info in updated_files[:5]:
                        file_name = Path(file_info["file"]).name
                        image_count = len(file_info["updated_images"])
                        message_parts.append(f"  • {file_name} ({image_count} image(s))<br>")
                    if len(updated_files) > 5:
                        message_parts.append(f"  ... and {len(updated_files) - 5} more<br>")

            if warnings:
                message_parts.append(f"<br><b>Warnings:</b><br>")
                for warning in warnings[:5]:
                    message_parts.append(f"  • {warning}<br>")
                if len(warnings) > 5:
                    message_parts.append(f"  ... and {len(warnings) - 5} more<br>")

            if errors:
                message_parts.append(f"<br><b>Errors:</b><br>")
                for error in errors:
                    message_parts.append(f"  • {error}<br>")

            QMessageBox.information(
                self,
                "Preview Results" if dry_run else "Rename Complete",
                "".join(message_parts)
            )

            # Clear inputs after successful execution
            if not dry_run and file_moved:
                self.tex_current_input.clear()
                self.tex_new_input.clear()
                self.tex_browse_btn.setEnabled(False)
                self.tex_preview_btn.setEnabled(False)
                self.tex_execute_btn.setEnabled(False)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print("=== Texture Rename Error ===")
            print(error_details)

            QMessageBox.critical(
                self,
                "Rename Error",
                f"Failed to rename texture:\n\n{str(e)}"
            )
        finally:
            # Restore state
            QApplication.restoreOverrideCursor()
            btn.setText(original_text)
            btn.setEnabled(True)

    def _browse_new_path(self):
        """Open file dialog to select new path."""
        if not self.current_file:
            return

        # Show loading state while dialog is open
        self.browse_btn.setText("Browsing...")
        self.browse_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            new_path, _ = QFileDialog.getSaveFileName(
                self,
                "Select New Location",
                str(self.current_file),
                f"*{self.current_file.suffix}"
            )

            if new_path:
                self.new_path_input.setText(new_path)

        finally:
            # Restore button state
            self.browse_btn.setText("Browse...")
            self.browse_btn.setEnabled(True)

    def _preview_operation(self):
        """Show preview dialog for the operation."""
        if not self.current_file:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return

        new_path = Path(self.new_path_input.text())

        if new_path == self.current_file:
            QMessageBox.information(self, "No Change", "Source and target are the same.")
            return

        # Show loading state
        self.preview_btn.setText("Loading Preview...")
        self.preview_btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()  # Force UI update

        try:
            # Get preview from controller
            preview = self.controller.preview_move_file(self.current_file, new_path)

            # Restore normal state
            QApplication.restoreOverrideCursor()
            self.preview_btn.setText("Preview Changes")
            self.preview_btn.setEnabled(True)

            # Show preview dialog
            dialog = OperationPreviewDialog(preview, self)
            dialog.exec()

        except Exception as e:
            # Restore normal state on error
            QApplication.restoreOverrideCursor()
            self.preview_btn.setText("Preview Changes")
            self.preview_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Preview Error",
                f"Failed to generate preview:\n\n{str(e)}"
            )

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

        # Show loading state immediately
        self.execute_btn.setText("Executing...")
        self.execute_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()  # Force UI update

        try:
            # Create and show progress dialog immediately
            progress_dialog = OperationProgressDialog(
                f"Moving {self.current_file.name}",
                self
            )
            progress_dialog.show()  # Show immediately, don't wait for exec()
            QApplication.processEvents()  # Force dialog to appear

            # Execute operation
            result = self.controller.execute_move_file(
                self.current_file,
                new_path,
                progress_dialog.update_progress
            )

            # Restore normal cursor
            QApplication.restoreOverrideCursor()

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
                self.execute_btn.setText("Execute Move")  # Restore text
                self.execute_btn.setEnabled(False)
            else:
                progress_dialog.mark_error(result.message)
                progress_dialog.exec()

                QMessageBox.critical(
                    self,
                    "Error",
                    f"Operation failed:\n\n{result.message}"
                )

                # Restore button state on error
                self.execute_btn.setText("Execute Move")
                self.execute_btn.setEnabled(True)
                self.preview_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)

        except Exception as e:
            # Restore state on exception
            QApplication.restoreOverrideCursor()
            self.execute_btn.setText("Execute Move")
            self.execute_btn.setEnabled(True)
            self.preview_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)

            QMessageBox.critical(
                self,
                "Error",
                f"Operation failed:\n\n{str(e)}"
            )

    def _load_scenes_for_target(self):
        """Load scenes from the target .blend file."""
        # Use locked file if lock is enabled, otherwise use current file
        target_file = self.link_locked_file if self.link_scene_lock.isChecked() else self.current_file

        if not target_file or target_file.suffix != '.blend':
            return

        try:
            # Get scenes from Blender service
            blender_service = self.controller.project.blender_service
            scenes = blender_service.get_scenes(target_file)

            self.link_scenes = scenes
            self.link_scene_combo.clear()

            # Populate dropdown
            for scene in scenes:
                self.link_scene_combo.addItem(scene["name"])

            # Update scene combo state (considers lock state)
            if scenes:
                self._update_scene_combo_state()
                # Restore scene selection
                self._restore_scene_selection()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Scenes Error",
                f"Failed to load scenes:\n\n{str(e)}"
            )

    def _on_scene_changed(self, scene_name: str):
        """Handle scene selection change.

        Args:
            scene_name: Name of selected scene
        """
        # Save scene selection for this file
        self._save_link_state()

    def _on_link_mode_changed(self, checked: bool):
        """Handle link mode radio button change.

        Args:
            checked: Whether instance mode is checked
        """
        # Collection input is now required for both modes
        self.collection_label.setEnabled(True)
        self.link_collection_input.setEnabled(True)

        # Save the mode preference
        self._save_link_state()

    def _update_scene_combo_state(self):
        """Update scene combo enabled state based on lock."""
        # Disable scene combo when lock is enabled
        is_locked = self.link_scene_lock.isChecked()
        self.link_scene_combo.setEnabled(not is_locked and len(self.link_scenes) > 0)

    def _on_scene_lock_changed(self, state: int):
        """Handle scene lock checkbox change.

        Args:
            state: Checkbox state
        """
        if self.link_scene_lock.isChecked():
            # Lock is enabled - save current file and scene
            if self.current_file and self.current_file.suffix == '.blend':
                self.link_locked_file = self.current_file
            else:
                # Can't lock without a .blend file selected
                QMessageBox.warning(
                    self,
                    "No Target File",
                    "Please select a .blend file as target before locking."
                )
                self.link_scene_lock.setChecked(False)
                return
        else:
            # Lock is disabled - clear locked file
            self.link_locked_file = None
            # Update target to current file
            if self.current_file and self.current_file.suffix == '.blend':
                self.link_target_display.setText(f"<b>{self.current_file.name}</b><br><small>{str(self.current_file)}</small>")
                self._load_scenes_for_target()

        # Update scene combo state based on lock
        self._update_scene_combo_state()

        # Save lock state
        self._save_link_state()

    def _load_link_source(self):
        """Load objects and collections from the source .blend file."""
        if not self.link_source_file:
            QMessageBox.warning(self, "No Source File", "Please select a source .blend file in the file browser.")
            return

        if not self.link_source_file.exists():
            QMessageBox.warning(self, "File Not Found", f"Source file not found: {self.link_source_file}")
            return

        # Show loading state
        self.link_load_btn.setText("Loading...")
        self.link_load_btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            # Use the same list_objects.py script
            runner = self.controller.project.blender_service.runner
            script_path = Path(__file__).parent.parent / "blender_lib" / "list_objects.py"

            result = runner.run_script(
                script_path,
                {"blend-file": str(self.link_source_file)},
                timeout=60
            )

            # Parse JSON output
            from services.blender_service import extract_json_from_output
            data = extract_json_from_output(result.stdout)

            if "error" in data and data["error"]:
                raise Exception(data["error"])

            # Store the data
            self.link_source_data = data

            # Populate the list
            self.link_items_list.clear()

            # Add objects
            for obj in data.get("objects", []):
                item_text = f"🔷 {obj.get('name', 'Unknown')} ({obj.get('type', 'Unknown')})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {"type": "object", "data": obj})
                self.link_items_list.addItem(item)

            # Add collections
            for col in data.get("collections", []):
                item_text = f"📁 {col.get('name', 'Unknown')} ({col.get('objects_count', 0)} objects)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {"type": "collection", "data": col})
                self.link_items_list.addItem(item)

            # Enable preview and execute buttons
            self.link_preview_btn.setEnabled(True)
            self.link_execute_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load objects/collections:\n\n{str(e)}"
            )
        finally:
            # Restore state
            QApplication.restoreOverrideCursor()
            self.link_load_btn.setText("Load Objects/Collections")
            self.link_load_btn.setEnabled(True)

    def _preview_link(self):
        """Preview the link operation."""
        self._link_internal(dry_run=True)

    def _execute_link(self):
        """Execute the link operation."""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Confirm Link",
            "This will link the selected objects/collections into the target .blend file.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self._link_internal(dry_run=False)

    def _link_internal(self, dry_run=True):
        """Internal method to handle link preview/execute.

        Args:
            dry_run: If True, only preview changes
        """
        # Use locked file if lock is enabled, otherwise use current file
        target_file = self.link_locked_file if self.link_scene_lock.isChecked() else self.current_file

        if not target_file or target_file.suffix != '.blend':
            QMessageBox.warning(self, "No File", "Please select a .blend file as target.")
            return

        # Get selected scene
        target_scene = self.link_scene_combo.currentText()
        if not target_scene:
            QMessageBox.warning(self, "No Scene", "Please select a target scene.")
            return

        # Get source file
        if not self.link_source_file or not self.link_source_file.exists():
            QMessageBox.warning(self, "No Source", "Please select a valid source .blend file in the file browser.")
            return

        # Get selected items
        selected_items = self.link_items_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select items to link.")
            return

        # Get link mode
        link_mode = 'instance' if self.link_mode_instance.isChecked() else 'individual'

        # Get target collection name (required for both modes)
        target_collection = self.link_collection_input.text().strip()
        if not target_collection:
            QMessageBox.warning(self, "No Collection", "Please enter a target collection name.")
            return

        # Extract item names and types
        item_names = []
        item_types = []
        for item in selected_items:
            item_data = item.data(Qt.UserRole)
            if item_data and "data" in item_data:
                item_names.append(item_data["data"].get("name", ""))
                item_types.append(item_data["type"])  # 'object' or 'collection'

        if not item_names:
            QMessageBox.warning(self, "No Items", "No valid items selected.")
            return

        # Validate selection for instance mode
        if link_mode == 'instance':
            # Count collections in selection
            num_collections = sum(1 for t in item_types if t == 'collection')
            num_objects = sum(1 for t in item_types if t == 'object')

            if num_collections != 1 or num_objects > 0:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Instance mode requires exactly ONE collection to be selected.\n\n"
                    "Please select a single collection, or switch to 'Individual' mode."
                )
                return

        # Show loading state
        btn = self.link_preview_btn if dry_run else self.link_execute_btn
        original_text = btn.text()
        btn.setText("Processing..." if dry_run else "Executing...")
        btn.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()

        try:
            from blender_lib.models import LinkOperationParams

            # Create operation parameters
            params = LinkOperationParams(
                target_file=target_file,
                target_scene=target_scene,
                source_file=self.link_source_file,
                item_names=item_names,
                item_types=item_types,
                target_collection=target_collection if target_collection else "",
                link_mode=link_mode
            )

            if dry_run:
                # Preview mode
                preview = self.controller.project.blender_service.preview_link_operation(params)

                QApplication.restoreOverrideCursor()

                if preview.errors:
                    error_msg = "<b>Cannot link due to errors:</b><br>"
                    for error in preview.errors:
                        error_msg += f"  • {error}<br>"

                    QMessageBox.critical(self, "Link Errors", error_msg)
                else:
                    # Show preview dialog
                    dialog = OperationPreviewDialog(preview, self)
                    dialog.exec()

            else:
                # Execute mode
                result = self.controller.project.blender_service.execute_link_operation(params)

                QApplication.restoreOverrideCursor()

                if result.success:
                    QMessageBox.information(
                        self,
                        "Link Complete",
                        f"{result.message}\n\n{result.changes_made} item(s) linked."
                    )

                    # Clear selection
                    self.link_items_list.clearSelection()
                else:
                    error_msg = f"<b>Link operation failed:</b><br>{result.message}<br>"
                    if result.errors:
                        error_msg += "<br><b>Errors:</b><br>"
                        for error in result.errors:
                            error_msg += f"  • {error}<br>"

                    QMessageBox.critical(self, "Link Failed", error_msg)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print("=== Link Error ===")
            print(error_details)

            QApplication.restoreOverrideCursor()

            QMessageBox.critical(
                self,
                "Link Error",
                f"Failed to link items:\n\n{str(e)}"
            )
        finally:
            # Restore state
            btn.setText(original_text)
            btn.setEnabled(True)

    def _save_link_state(self):
        """Save link operation state to config file."""
        if not self.config_file:
            return

        try:
            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Get current state
            link_state = config_data.get('link_operation', {})

            # Save link mode
            link_state['link_mode'] = 'instance' if self.link_mode_instance.isChecked() else 'individual'

            # Save lock state
            link_state['scene_lock_enabled'] = self.link_scene_lock.isChecked()

            # If lock is enabled, save the locked file and scene
            if self.link_scene_lock.isChecked():
                if self.link_locked_file:
                    link_state['locked_file'] = str(self.link_locked_file)
                link_state['locked_scene'] = self.link_scene_combo.currentText()

            # Save per-file scene selection
            # Use locked file if lock is enabled, otherwise use current file
            target_file = self.link_locked_file if self.link_scene_lock.isChecked() else self.current_file
            if target_file and self.link_scene_combo.currentText():
                per_file_scenes = link_state.get('per_file_scenes', {})
                per_file_scenes[str(target_file)] = self.link_scene_combo.currentText()
                link_state['per_file_scenes'] = per_file_scenes

            # Save target collection
            if self.link_collection_input.text():
                link_state['last_target_collection'] = self.link_collection_input.text()

            config_data['link_operation'] = link_state

            # Write back to file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save link operation state: {e}")

    def _restore_link_state(self):
        """Restore link operation state from config file."""
        if not self.config_file or not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            link_state = config_data.get('link_operation', {})

            # Restore link mode
            link_mode = link_state.get('link_mode', 'instance')
            if link_mode == 'instance':
                self.link_mode_instance.setChecked(True)
            else:
                self.link_mode_individual.setChecked(True)

            # Restore lock state
            scene_lock_enabled = link_state.get('scene_lock_enabled', False)

            # If lock was enabled, restore the locked file and scene
            if scene_lock_enabled:
                locked_file = link_state.get('locked_file')
                locked_scene = link_state.get('locked_scene')
                if locked_file and Path(locked_file).exists():
                    # Check if project is open (blender_service available)
                    if self.controller.project.is_open and self.controller.project.blender_service:
                        # Project is open, restore immediately
                        self._apply_locked_file_restoration(Path(locked_file), locked_scene)
                    else:
                        # Project not open yet, defer restoration
                        self.pending_locked_file_restore = {
                            'locked_file': Path(locked_file),
                            'locked_scene': locked_scene
                        }
                else:
                    # Locked file doesn't exist anymore, don't enable lock
                    scene_lock_enabled = False

            if not scene_lock_enabled:
                # Block signals to avoid validation during initialization
                self.link_scene_lock.blockSignals(True)
                self.link_scene_lock.setChecked(False)
                self.link_scene_lock.blockSignals(False)

            # Restore last target collection
            last_collection = link_state.get('last_target_collection', '')
            self.link_collection_input.setText(last_collection)

        except Exception as e:
            print(f"Warning: Could not restore link operation state: {e}")

    def _restore_scene_selection(self):
        """Restore scene selection based on lock state and per-file settings."""
        # Use locked file if lock is enabled, otherwise use current file
        target_file = self.link_locked_file if self.link_scene_lock.isChecked() else self.current_file

        if not self.config_file or not self.config_file.exists() or not target_file:
            return

        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            link_state = config_data.get('link_operation', {})

            # Check if lock is enabled
            if link_state.get('scene_lock_enabled', False):
                # Use locked scene
                locked_scene = link_state.get('locked_scene')
                if locked_scene:
                    index = self.link_scene_combo.findText(locked_scene)
                    if index >= 0:
                        self.link_scene_combo.setCurrentIndex(index)
                        return

            # Otherwise, check for per-file scene
            per_file_scenes = link_state.get('per_file_scenes', {})
            file_scene = per_file_scenes.get(str(target_file))
            if file_scene:
                index = self.link_scene_combo.findText(file_scene)
                if index >= 0:
                    self.link_scene_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Warning: Could not restore scene selection: {e}")

    def _apply_locked_file_restoration(self, locked_file: Path, locked_scene: str):
        """Apply locked file restoration when blender_service is available.

        Args:
            locked_file: Path to locked .blend file
            locked_scene: Name of locked scene
        """
        try:
            self.link_locked_file = locked_file
            # Update the display to show the locked file
            self.link_target_display.setText(f"<b>{locked_file.name}</b><br><small>{str(locked_file)}</small>")

            # Load scenes for the locked file
            blender_service = self.controller.project.blender_service
            scenes = blender_service.get_scenes(locked_file)
            self.link_scenes = scenes

            # Block signals during restoration to avoid saving state while loading
            self.link_scene_combo.blockSignals(True)
            self.link_scene_combo.clear()
            for scene in scenes:
                self.link_scene_combo.addItem(scene["name"])
            if scenes:
                # Restore locked scene
                if locked_scene:
                    index = self.link_scene_combo.findText(locked_scene)
                    if index >= 0:
                        self.link_scene_combo.setCurrentIndex(index)
            self.link_scene_combo.blockSignals(False)

            # Block signals while setting checkbox to avoid validation during initialization
            self.link_scene_lock.blockSignals(True)
            self.link_scene_lock.setChecked(True)
            self.link_scene_lock.blockSignals(False)

            # Update scene combo state (will be disabled because lock is checked)
            self._update_scene_combo_state()

            # Clear pending restoration
            self.pending_locked_file_restore = None

        except Exception as e:
            self.link_scene_combo.blockSignals(False)
            print(f"Warning: Could not apply locked file restoration: {e}")

    def apply_pending_restorations(self):
        """Apply any pending restorations after project is opened."""
        if self.pending_locked_file_restore:
            locked_file = self.pending_locked_file_restore['locked_file']
            locked_scene = self.pending_locked_file_restore['locked_scene']
            self._apply_locked_file_restoration(locked_file, locked_scene)
