"""Rename Objects/Collections tab for bulk renaming within .blend files."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QListWidget, QListWidgetItem, QComboBox
)

from gui.operations.base_tab import BaseOperationTab
from gui.ui_strings import (
    TITLE_NO_FILE, TITLE_NO_SELECTION, TITLE_MISSING_INPUT, TITLE_NO_ITEMS, TITLE_CONFIRM_RENAME,
    MSG_SELECT_BLEND_FILE, MSG_SELECT_ITEMS_TO_RENAME, MSG_ENTER_FIND_TEXT, MSG_NO_VALID_ITEMS,
    TMPL_CONFIRM_RENAME_OBJECTS, TMPL_FAILED_TO_LOAD,
    BTN_PROCESSING, BTN_EXECUTING
)
from blender_lib.constants import TIMEOUT_SHORT, TIMEOUT_MEDIUM
from services.blender_service import extract_json_from_output


class RenameObjectsTab(BaseOperationTab):
    """Tab for renaming objects and collections within a .blend file."""

    def __init__(self, controller, parent=None):
        """Initialize rename objects tab.

        Args:
            controller: File operations controller
            parent: Parent widget (operations panel)
        """
        super().__init__(controller, parent)
        self.obj_list_data = {"objects": [], "collections": []}
        self.setup_ui()

    def setup_ui(self):
        """Create the UI for the rename objects tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

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

        # Set content widget in scroll area
        scroll.setWidget(content)

        # Set the main layout for this tab
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def set_file(self, file_path: Path):
        """Set the currently selected file.

        Args:
            file_path: Path to the selected file or directory
        """
        super().set_file(file_path)

        # Update Rename Objects tab (only for .blend files)
        if self.is_blend_file(file_path):
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

    def _load_objects(self):
        """Load objects and collections from the selected .blend file."""
        if not self.current_file or self.current_file.suffix != '.blend':
            return

        try:
            with self.loading_state(self.obj_load_btn, "Loading..."):
                # Get the blender runner from controller
                runner = self.get_blender_runner()
                script_path = Path(__file__).parent.parent.parent / "blender_lib" / "list_objects.py"

                # Verify script exists
                if not script_path.exists():
                    raise Exception(f"Script not found: {script_path}")

                # Run the script with blend file as argument
                result = runner.run_script(
                    script_path,
                    {"blend-file": str(self.current_file)},
                    timeout=TIMEOUT_SHORT
                )

                # Parse JSON output
                data = extract_json_from_output(result.stdout)

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
            self.show_error("Load Error", TMPL_FAILED_TO_LOAD.format(error=str(e)))

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
        confirmed = self.confirm(TITLE_CONFIRM_RENAME, TMPL_CONFIRM_RENAME_OBJECTS)

        if not confirmed:
            return

        self._rename_objects_internal(dry_run=False)

    def _rename_objects_internal(self, dry_run=True):
        """Internal method to handle rename preview/execute.

        Args:
            dry_run: If True, only preview changes
        """
        if not self.current_file or self.current_file.suffix != '.blend':
            self.show_warning(TITLE_NO_FILE, MSG_SELECT_BLEND_FILE)
            return

        # Get selected items
        selected_items = self.obj_list.selectedItems()
        if not selected_items:
            self.show_warning(TITLE_NO_SELECTION, MSG_SELECT_ITEMS_TO_RENAME)
            return

        # Get find/replace text
        find_text = self.obj_find_input.text().strip()
        replace_text = self.obj_replace_input.text().strip()

        if not find_text:
            self.show_warning(TITLE_MISSING_INPUT, MSG_ENTER_FIND_TEXT)
            return

        # Extract item names
        item_names = []
        for item in selected_items:
            item_data = item.data(Qt.UserRole)
            if item_data and "data" in item_data:
                item_names.append(item_data["data"].get("name", ""))

        if not item_names:
            self.show_warning(TITLE_NO_ITEMS, MSG_NO_VALID_ITEMS)
            return

        # Execute with loading state
        btn = self.obj_preview_btn if dry_run else self.obj_execute_btn
        loading_text = BTN_PROCESSING if dry_run else BTN_EXECUTING

        try:
            with self.loading_state(btn, loading_text):
                runner = self.get_blender_runner()
                script_path = Path(__file__).parent.parent.parent / "blender_lib" / "rename_objects.py"

                # Get project root
                project_root = self.get_project_root()

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
                    timeout=TIMEOUT_MEDIUM
                )

                # Parse JSON output
                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                # Show results
                self._show_rename_results(data, dry_run)

        except Exception as e:
            self.show_error("Rename Error", f"Failed to rename items:\n\n{str(e)}")

    def _show_rename_results(self, data: dict, dry_run: bool):
        """Show results of rename operation.

        Args:
            data: Result data from Blender script
            dry_run: Whether this was a preview or execution
        """
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

        title = "Preview Results" if dry_run else "Rename Complete"
        self.show_info(title, "".join(message_parts))
