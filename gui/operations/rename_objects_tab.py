"""Rename Objects/Collections tab for bulk renaming within .blend files."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QListWidget, QListWidgetItem, QComboBox
)

from gui.operations.base_tab import BaseOperationTab
from gui.progress_dialog import OperationProgressDialog
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
        self.obj_list_data = {"objects": [], "collections": [], "materials": []}
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

        # Scene selector
        scene_layout = QHBoxLayout()
        scene_label = QLabel("Scene:")
        scene_layout.addWidget(scene_label)

        self.obj_scene_combo = QComboBox()
        self.obj_scene_combo.setEnabled(False)
        scene_layout.addWidget(self.obj_scene_combo, stretch=1)

        self.obj_load_scenes_btn = QPushButton("Load Scenes")
        self.obj_load_scenes_btn.setEnabled(False)
        self.obj_load_scenes_btn.clicked.connect(self._load_scenes_for_rename)
        scene_layout.addWidget(self.obj_load_scenes_btn)

        tab_layout.addLayout(scene_layout)

        # Type filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Show:")
        filter_layout.addWidget(filter_label)

        self.obj_type_combo = QComboBox()
        self.obj_type_combo.addItems(["All", "Objects", "Collections", "Materials"])
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

        # Filter input for searching items
        self.obj_filter_input = QLineEdit()
        self.obj_filter_input.setPlaceholderText("Filter items by name...")
        self.obj_filter_input.textChanged.connect(self._filter_items_by_name)
        self.obj_filter_input.setClearButtonEnabled(True)
        tab_layout.addWidget(self.obj_filter_input)

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

        # Copy button
        self.obj_copy_btn = QPushButton("→")
        self.obj_copy_btn.setMaximumWidth(40)
        self.obj_copy_btn.setToolTip("Copy 'Find' text to 'Replace' field")
        self.obj_copy_btn.clicked.connect(self._copy_find_to_replace)
        rename_layout.addWidget(self.obj_copy_btn)

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
            self.obj_load_scenes_btn.setEnabled(True)
            self.obj_load_btn.setEnabled(True)
            self.obj_list.clear()
            self.obj_filter_input.clear()
            self.obj_list_data = {"objects": [], "collections": [], "materials": []}
        else:
            self.obj_scene_combo.clear()
            self.obj_scene_combo.setEnabled(False)
            self.obj_load_scenes_btn.setEnabled(False)
            self.obj_load_btn.setEnabled(False)
            self.obj_preview_btn.setEnabled(False)
            self.obj_execute_btn.setEnabled(False)
            self.obj_list.clear()
            self.obj_filter_input.clear()
            self.obj_list_data = {"objects": [], "collections": [], "materials": []}

    def _load_scenes_for_rename(self):
        """Load scenes from the .blend file."""
        if not self.current_file or self.current_file.suffix != '.blend':
            return

        try:
            with self.loading_state(self.obj_load_scenes_btn, "Loading..."):
                # Get scenes from Blender service
                blender_service = self.controller.project.blender_service
                scenes = blender_service.get_scenes(self.current_file)

                self.obj_scene_combo.clear()
                self.obj_scene_combo.addItem("All")  # Add "All" option first

                # Populate dropdown with scene names
                for scene in scenes:
                    self.obj_scene_combo.addItem(scene["name"])

                if scenes:
                    self.obj_scene_combo.setEnabled(True)

        except Exception as e:
            self.show_warning("Load Scenes Error", f"Failed to load scenes:\n\n{str(e)}")
            self.obj_scene_combo.clear()
            self.obj_scene_combo.setEnabled(False)

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

                # Get selected scene
                scene_name = self.obj_scene_combo.currentText()
                script_args = {"blend-file": str(self.current_file)}

                # Add scene parameter if not "All"
                if scene_name and scene_name != "All":
                    script_args["scene"] = scene_name

                # Run the script with blend file as argument
                result = runner.run_script(
                    script_path,
                    script_args,
                    timeout=TIMEOUT_SHORT
                )

                # Parse JSON output
                data = extract_json_from_output(result.stdout)

                # Validate data structure
                if not isinstance(data, dict):
                    raise Exception(f"Expected dict from Blender script, got {type(data).__name__}: {data}")

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                if "objects" not in data or "collections" not in data or "materials" not in data:
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

        if filter_type in ["All", "Objects"]:
            objects = self.obj_list_data.get("objects", [])
            if isinstance(objects, list):
                for obj in objects:
                    if isinstance(obj, dict):
                        item_text = f"🔷 {obj.get('name', 'Unknown')} ({obj.get('type', 'Unknown')})"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "object", "data": obj})
                        self.obj_list.addItem(item)

        if filter_type in ["All", "Collections"]:
            collections = self.obj_list_data.get("collections", [])
            if isinstance(collections, list):
                for col in collections:
                    if isinstance(col, dict):
                        item_text = f"📁 {col.get('name', 'Unknown')} ({col.get('objects_count', 0)} objects)"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "collection", "data": col})
                        self.obj_list.addItem(item)

        if filter_type in ["All", "Materials"]:
            materials = self.obj_list_data.get("materials", [])
            if isinstance(materials, list):
                for mat in materials:
                    if isinstance(mat, dict):
                        nodes_text = "nodes" if mat.get("use_nodes", False) else "no nodes"
                        item_text = f"🎨 {mat.get('name', 'Unknown')} ({nodes_text}, {mat.get('users', 0)} users)"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "material", "data": mat})
                        self.obj_list.addItem(item)

        # Apply name filter if there is one
        self._filter_items_by_name()

    def _filter_objects_list(self):
        """Filter the objects list based on combo box selection."""
        if isinstance(self.obj_list_data, dict) and (self.obj_list_data.get("objects") or self.obj_list_data.get("collections") or self.obj_list_data.get("materials")):
            self._populate_objects_list()

    def _filter_items_by_name(self):
        """Filter list items based on name filter input."""
        filter_text = self.obj_filter_input.text().strip().lower()

        # Show/hide items based on filter text
        for i in range(self.obj_list.count()):
            item = self.obj_list.item(i)
            if not filter_text:
                # No filter - show all items
                item.setHidden(False)
            else:
                # Get item data to check the actual name
                item_data = item.data(Qt.UserRole)
                if item_data and "data" in item_data:
                    item_name = item_data["data"].get("name", "").lower()
                    # Show item if name contains filter text
                    item.setHidden(filter_text not in item_name)
                else:
                    # If no data, hide the item
                    item.setHidden(True)

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

    def _copy_find_to_replace(self):
        """Copy the 'Find' text to the 'Replace' field."""
        find_text = self.obj_find_input.text()
        self.obj_replace_input.setText(find_text)

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

        # For preview, use loading state; for execute, use progress dialog
        if dry_run:
            self._run_rename_with_loading_state(item_names, find_text, replace_text, dry_run)
        else:
            self._run_rename_with_progress_dialog(item_names, find_text, replace_text)

    def _run_rename_with_loading_state(self, item_names, find_text, replace_text, dry_run):
        """Run rename operation with simple loading state (for preview)."""
        try:
            with self.loading_state(self.obj_preview_btn, BTN_PROCESSING):
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
                        "dry-run": "true"
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

    def _run_rename_with_progress_dialog(self, item_names, find_text, replace_text):
        """Run rename operation with progress dialog (for execution)."""
        from PySide6.QtWidgets import QApplication

        # Disable buttons
        self.obj_execute_btn.setText(BTN_EXECUTING)
        self.obj_execute_btn.setEnabled(False)
        self.obj_preview_btn.setEnabled(False)
        self.obj_load_btn.setEnabled(False)
        QApplication.processEvents()

        # Create and show progress dialog
        progress_dialog = OperationProgressDialog(f"Renaming Objects/Collections", self)
        progress_dialog.show()
        QApplication.processEvents()

        try:
            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "rename_objects.py"

            # Get project root
            project_root = self.get_project_root()

            # Define progress callback
            def on_output_line(line: str):
                """Process each line of output from Blender script."""
                # Look for LOG: prefix
                if line.startswith("LOG: "):
                    message = line[5:]  # Remove "LOG: " prefix
                    progress_dialog.log_text.append(message)
                    QApplication.processEvents()

            # Run the script with progress
            result = runner.run_script_with_progress(
                script_path,
                {
                    "blend-file": str(self.current_file),
                    "project-root": str(project_root),
                    "item-names": ",".join(item_names),
                    "find": find_text,
                    "replace": replace_text,
                    "dry-run": "false"
                },
                progress_callback=on_output_line,
                timeout=TIMEOUT_MEDIUM
            )

            # Parse JSON output
            data = extract_json_from_output(result.stdout)

            if "error" in data and data["error"]:
                raise Exception(data["error"])

            # Mark complete
            progress_dialog.update_progress(100, "Rename complete!")
            progress_dialog.exec()

            # Show results
            self._show_rename_results(data, dry_run=False)

        except Exception as e:
            progress_dialog.mark_error(str(e))
            progress_dialog.exec()
            self.show_error("Rename Error", f"Failed to rename items:\n\n{str(e)}")
        finally:
            # Restore buttons
            self.obj_execute_btn.setText("Execute Rename")
            self.obj_execute_btn.setEnabled(True)
            self.obj_preview_btn.setEnabled(True)
            self.obj_load_btn.setEnabled(True)

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
