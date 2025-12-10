"""Link Objects/Collections tab for linking between .blend files."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QListWidget, QListWidgetItem, QComboBox,
    QCheckBox, QRadioButton, QButtonGroup
)

from gui.operations.base_tab import BaseOperationTab
from gui.preview_dialog import OperationPreviewDialog
from gui.theme import Theme
from gui.ui_strings import (
    TITLE_NO_FILE, TITLE_NO_SOURCE_FILE, TITLE_FILE_NOT_FOUND, TITLE_NO_SCENE,
    TITLE_NO_SOURCE, TITLE_NO_SELECTION, TITLE_NO_ITEMS, TITLE_NO_COLLECTION,
    TITLE_CONFIRM_LINK, TITLE_LOAD_ERROR, TITLE_LINK_ERRORS, TITLE_LINK_FAILED,
    TITLE_LINK_COMPLETE,
    MSG_SELECT_BLEND_FILE, MSG_SELECT_SOURCE_BLEND, MSG_SELECT_TARGET_SCENE,
    MSG_SELECT_VALID_SOURCE, MSG_SELECT_ITEMS_TO_LINK, MSG_ENTER_COLLECTION_NAME,
    MSG_NO_VALID_ITEMS,
    LABEL_NO_BLEND_SELECTED, LABEL_SELECT_BLEND_IN_BROWSER,
    TMPL_SOURCE_FILE_NOT_FOUND, TMPL_FAILED_TO_LOAD, TMPL_CONFIRM_LINK,
    TMPL_LINK_COMPLETE,
    BTN_PROCESSING, BTN_EXECUTING, BTN_LOAD_OBJECTS_COLLECTIONS
)
from blender_lib.constants import TIMEOUT_SHORT


class LinkObjectsTab(BaseOperationTab):
    """Tab for linking objects and collections between .blend files."""

    def __init__(self, controller, parent=None, config_file: Path = None):
        """Initialize link objects tab.

        Args:
            controller: File operations controller
            parent: Parent widget (operations panel)
            config_file: Path to config file for state persistence
        """
        super().__init__(controller, parent)
        self.config_file = config_file
        self.link_source_data = {"objects": [], "collections": []}
        self.link_scenes = []
        self.link_source_file: Optional[Path] = None
        self.link_locked_file: Optional[Path] = None
        self.pending_locked_file_restore = None
        self.setup_ui()
        self._restore_link_state()

    def setup_ui(self):
        """Create the UI for the link objects tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

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

        self.link_target_display = QLabel(LABEL_NO_BLEND_SELECTED)
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

        self.link_source_display = QLabel(LABEL_SELECT_BLEND_IN_BROWSER)
        self.link_source_display.setWordWrap(True)
        self.link_source_display.setStyleSheet(Theme.get_file_display_style())
        tab_layout.addWidget(self.link_source_display)

        # Source scene selector
        source_scene_layout = QHBoxLayout()
        source_scene_label = QLabel("Scene:")
        source_scene_layout.addWidget(source_scene_label)

        self.link_source_scene_combo = QComboBox()
        self.link_source_scene_combo.setEnabled(False)
        source_scene_layout.addWidget(self.link_source_scene_combo)

        source_scene_layout.addStretch()
        tab_layout.addLayout(source_scene_layout)

        # Type filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Show:")
        filter_layout.addWidget(filter_label)

        self.link_type_combo = QComboBox()
        self.link_type_combo.addItems(["All", "Objects", "Collections"])
        self.link_type_combo.currentTextChanged.connect(self._filter_link_items_list)
        filter_layout.addWidget(self.link_type_combo)

        # Load button
        self.link_load_btn = QPushButton(BTN_LOAD_OBJECTS_COLLECTIONS)
        self.link_load_btn.setEnabled(False)
        self.link_load_btn.clicked.connect(self._load_link_source)
        filter_layout.addWidget(self.link_load_btn)

        filter_layout.addStretch()
        tab_layout.addLayout(filter_layout)

        # Items list
        items_label = QLabel("Select items to link:")
        tab_layout.addWidget(items_label)

        self.link_items_list = QListWidget()
        self.link_items_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.link_items_list.itemSelectionChanged.connect(self._on_link_item_selection_changed)
        tab_layout.addWidget(self.link_items_list)

        tab_layout.addSpacing(5)

        # Link mode selection
        mode_label = QLabel("<b>Link Mode:</b>")
        tab_layout.addWidget(mode_label)

        self.link_mode_instance = QRadioButton("Link as instance (Blender default)")
        self.link_mode_instance.setToolTip("Creates an instance inside the target collection.\nSupports ONE collection or ONE object (mesh, camera, etc.)")
        self.link_mode_instance.setChecked(True)

        self.link_mode_individual = QRadioButton("Link individually into collection (Object/Mesh)")
        self.link_mode_individual.setToolTip("Links each object/collection separately into the target collection")

        self.link_mode_group = QButtonGroup()
        self.link_mode_group.addButton(self.link_mode_instance, 0)
        self.link_mode_group.addButton(self.link_mode_individual, 1)

        self.link_mode_instance.toggled.connect(self._on_link_mode_changed)

        tab_layout.addWidget(self.link_mode_instance)
        tab_layout.addWidget(self.link_mode_individual)

        tab_layout.addSpacing(5)

        # Add to collection checkbox
        self.link_add_to_collection_checkbox = QCheckBox("Add to collection")
        self.link_add_to_collection_checkbox.setToolTip("Place linked items inside a target collection")
        self.link_add_to_collection_checkbox.setChecked(True)
        self.link_add_to_collection_checkbox.stateChanged.connect(self._on_add_to_collection_changed)
        tab_layout.addWidget(self.link_add_to_collection_checkbox)

        # Target collection (for both modes)
        self.collection_label = QLabel("Target collection name:")
        tab_layout.addWidget(self.collection_label)

        collection_layout = QHBoxLayout()

        self.link_collection_input = QLineEdit()
        self.link_collection_input.setPlaceholderText("Collection to place linked items (created if needed)")
        collection_layout.addWidget(self.link_collection_input)

        # Copy button
        self.link_copy_name_btn = QPushButton("Copy Name")
        self.link_copy_name_btn.setEnabled(False)
        self.link_copy_name_btn.setToolTip("Copy selected item name to target collection field")
        self.link_copy_name_btn.clicked.connect(self._copy_item_name_to_collection)
        collection_layout.addWidget(self.link_copy_name_btn)

        tab_layout.addLayout(collection_layout)

        # Add .link suffix option
        self.link_add_suffix_checkbox = QCheckBox("Add '.link' suffix to collection name")
        self.link_add_suffix_checkbox.setToolTip("Appends '.link' to the target collection name (e.g., 'MyCollection.link')")
        self.link_add_suffix_checkbox.setChecked(False)
        self.link_add_suffix_checkbox.stateChanged.connect(self._save_link_state)
        tab_layout.addWidget(self.link_add_suffix_checkbox)

        # Link as hidden option
        self.link_as_hidden_checkbox = QCheckBox("Link as hidden")
        self.link_as_hidden_checkbox.setToolTip(
            "Hide in viewport (eye icon):\n"
            "• With collection: Hides the target collection\n"
            "• Without collection: Hides the linked objects"
        )
        self.link_as_hidden_checkbox.setChecked(False)
        self.link_as_hidden_checkbox.stateChanged.connect(self._save_link_state)
        tab_layout.addWidget(self.link_as_hidden_checkbox)

        # Hide instancer option
        self.link_hide_instancer_checkbox = QCheckBox("Hide instancer")
        self.link_hide_instancer_checkbox.setToolTip(
            "Hide the instancer visualization (axes and bounding box)\n"
            "for Empty objects with collection instances"
        )
        self.link_hide_instancer_checkbox.setChecked(False)
        self.link_hide_instancer_checkbox.stateChanged.connect(self._save_link_state)
        tab_layout.addWidget(self.link_hide_instancer_checkbox)

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

        # Update Link tab (only for .blend files)
        is_blend = self.is_blend_file(file_path)

        if self.link_scene_lock.isChecked():
            # Target is locked - selected file becomes SOURCE
            if is_blend:
                self.link_source_file = file_path
                self.link_source_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")
                self._load_scenes_for_link_source()
                self.link_load_btn.setEnabled(True)
                # Clear previous items when source changes
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}
            else:
                # Non-.blend file selected, clear source
                self.link_source_file = None
                self.link_source_display.setText(LABEL_SELECT_BLEND_IN_BROWSER)
                self.link_source_scene_combo.clear()
                self.link_source_scene_combo.setEnabled(False)
                self.link_load_btn.setEnabled(False)
                self.link_items_list.clear()
                self.link_source_data = {"objects": [], "collections": []}
        else:
            # Target is not locked - selected file becomes TARGET
            if is_blend:
                self.link_target_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")
                self._load_scenes_for_target()
            else:
                self.link_target_display.setText(LABEL_NO_BLEND_SELECTED)
                self.link_scene_combo.clear()
                self.link_scene_combo.setEnabled(False)

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
            self.show_warning("Load Scenes Error", f"Failed to load scenes:\n\n{str(e)}")

    def _on_scene_changed(self, scene_name: str):
        """Handle scene selection change."""
        # Save scene selection for this file
        self._save_link_state()

    def _on_link_mode_changed(self, checked: bool):
        """Handle link mode radio button change."""
        # Collection input is now required for both modes
        self.collection_label.setEnabled(True)
        self.link_collection_input.setEnabled(True)

        # Save the mode preference
        self._save_link_state()

    def _on_add_to_collection_changed(self, state: int):
        """Handle 'Add to collection' checkbox state change."""
        is_checked = self.link_add_to_collection_checkbox.isChecked()

        # Show/hide collection-related widgets
        self.collection_label.setVisible(is_checked)
        self.link_collection_input.setVisible(is_checked)
        self.link_copy_name_btn.setVisible(is_checked)
        self.link_add_suffix_checkbox.setVisible(is_checked)
        # Note: link_as_hidden_checkbox stays visible - it works for both modes

        # Save the preference
        self._save_link_state()

    def _update_scene_combo_state(self):
        """Update scene combo enabled state based on lock."""
        # Disable scene combo when lock is enabled
        is_locked = self.link_scene_lock.isChecked()
        self.link_scene_combo.setEnabled(not is_locked and len(self.link_scenes) > 0)

    def _on_scene_lock_changed(self, state: int):
        """Handle scene lock checkbox change."""
        if self.link_scene_lock.isChecked():
            # Lock is enabled - save current file and scene
            if self.current_file and self.current_file.suffix == '.blend':
                self.link_locked_file = self.current_file
            else:
                # Can't lock without a .blend file selected
                self.show_warning(
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

    def _load_scenes_for_link_source(self):
        """Load scenes from the source .blend file."""
        if not self.link_source_file or self.link_source_file.suffix != '.blend':
            return

        try:
            # Get scenes from Blender service
            blender_service = self.controller.project.blender_service
            scenes = blender_service.get_scenes(self.link_source_file)

            self.link_source_scene_combo.clear()
            self.link_source_scene_combo.addItem("All")  # Add "All" option first

            # Populate dropdown with scene names
            for scene in scenes:
                self.link_source_scene_combo.addItem(scene["name"])

            if scenes:
                self.link_source_scene_combo.setEnabled(True)

        except Exception as e:
            self.show_warning("Load Scenes Error", f"Failed to load scenes:\n\n{str(e)}")
            self.link_source_scene_combo.clear()
            self.link_source_scene_combo.setEnabled(False)

    def _load_link_source(self):
        """Load objects and collections from the source .blend file."""
        if not self.link_source_file:
            self.show_warning(TITLE_NO_SOURCE_FILE, MSG_SELECT_SOURCE_BLEND)
            return

        if not self.link_source_file.exists():
            self.show_warning(TITLE_FILE_NOT_FOUND, TMPL_SOURCE_FILE_NOT_FOUND.format(file_path=self.link_source_file))
            return

        try:
            with self.loading_state(self.link_load_btn, "Loading..."):
                # Use the same list_objects.py script
                runner = self.get_blender_runner()
                script_path = Path(__file__).parent.parent.parent / "blender_lib" / "list_objects.py"

                # Get selected scene
                scene_name = self.link_source_scene_combo.currentText()
                script_args = {"blend-file": str(self.link_source_file)}

                # Add scene parameter if not "All"
                if scene_name and scene_name != "All":
                    script_args["scene"] = scene_name

                result = runner.run_script(
                    script_path,
                    script_args,
                    timeout=TIMEOUT_SHORT
                )

                # Parse JSON output
                from services.blender_service import extract_json_from_output
                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                # Ensure we have the expected keys
                if "objects" not in data or "collections" not in data:
                    raise Exception(f"Invalid data structure: {list(data.keys())}")

                # Store the data
                self.link_source_data = data

                # Populate the list
                self._populate_link_items_list()

                # Enable preview and execute buttons
                self.link_preview_btn.setEnabled(True)
                self.link_execute_btn.setEnabled(True)

        except Exception as e:
            self.show_error(TITLE_LOAD_ERROR, TMPL_FAILED_TO_LOAD.format(error=str(e)))

    def _populate_link_items_list(self):
        """Populate the list widget with objects and collections based on filter."""
        self.link_items_list.clear()

        # Ensure link_source_data is a valid dict
        if not isinstance(self.link_source_data, dict):
            return

        filter_type = self.link_type_combo.currentText()

        # Add objects
        if filter_type in ["All", "Objects"]:
            objects = self.link_source_data.get("objects", [])
            if isinstance(objects, list):
                for obj in objects:
                    if isinstance(obj, dict):
                        item_text = f"🔷 {obj.get('name', 'Unknown')} ({obj.get('type', 'Unknown')})"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "object", "data": obj})
                        self.link_items_list.addItem(item)

        # Add collections
        if filter_type in ["All", "Collections"]:
            collections = self.link_source_data.get("collections", [])
            if isinstance(collections, list):
                for col in collections:
                    if isinstance(col, dict):
                        item_text = f"📁 {col.get('name', 'Unknown')} ({col.get('objects_count', 0)} objects)"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {"type": "collection", "data": col})
                        self.link_items_list.addItem(item)

    def _filter_link_items_list(self):
        """Filter the items list based on combo box selection."""
        if isinstance(self.link_source_data, dict) and (self.link_source_data.get("objects") or self.link_source_data.get("collections")):
            self._populate_link_items_list()

    def _preview_link(self):
        """Preview the link operation."""
        self._link_internal(dry_run=True)

    def _execute_link(self):
        """Execute the link operation."""
        # Confirm with user
        confirmed = self.confirm(TITLE_CONFIRM_LINK, TMPL_CONFIRM_LINK)

        if not confirmed:
            return

        self._link_internal(dry_run=False)

    def _link_internal(self, dry_run=True):
        """Internal method to handle link preview/execute."""
        # Use locked file if lock is enabled, otherwise use current file
        target_file = self.link_locked_file if self.link_scene_lock.isChecked() else self.current_file

        if not target_file or target_file.suffix != '.blend':
            self.show_warning(TITLE_NO_FILE, MSG_SELECT_BLEND_FILE)
            return

        # Get selected scene
        target_scene = self.link_scene_combo.currentText()
        if not target_scene:
            self.show_warning(TITLE_NO_SCENE, MSG_SELECT_TARGET_SCENE)
            return

        # Get source file
        if not self.link_source_file or not self.link_source_file.exists():
            self.show_warning(TITLE_NO_SOURCE, MSG_SELECT_VALID_SOURCE)
            return

        # Get selected items
        selected_items = self.link_items_list.selectedItems()
        if not selected_items:
            self.show_warning(TITLE_NO_SELECTION, MSG_SELECT_ITEMS_TO_LINK)
            return

        # Get link mode
        link_mode = 'instance' if self.link_mode_instance.isChecked() else 'individual'

        # Get target collection name (only if "Add to collection" is checked)
        target_collection = ""
        if self.link_add_to_collection_checkbox.isChecked():
            target_collection = self.link_collection_input.text().strip()
            if not target_collection:
                self.show_warning(TITLE_NO_COLLECTION, MSG_ENTER_COLLECTION_NAME)
                return

            # Add .link suffix if checkbox is checked
            if self.link_add_suffix_checkbox.isChecked():
                if not target_collection.endswith('.link'):
                    target_collection = target_collection + '.link'

        # Extract item names and types
        item_names = []
        item_types = []
        for item in selected_items:
            item_data = item.data(Qt.UserRole)
            if item_data and "data" in item_data:
                item_names.append(item_data["data"].get("name", ""))
                item_types.append(item_data["type"])  # 'object' or 'collection'

        if not item_names:
            self.show_warning(TITLE_NO_ITEMS, MSG_NO_VALID_ITEMS)
            return

        # Check if target collection name conflicts with any selected item names (only if collection is being created)
        if target_collection and target_collection in item_names:
            self.show_warning(
                "Name Conflict",
                f"The target collection name '{target_collection}' conflicts with one of the selected items.\n\n"
                f"Please choose a different collection name to avoid naming conflicts in Blender."
            )
            return

        # Validate selection for instance mode
        if link_mode == 'instance':
            # Count total items in selection
            total_items = len(item_names)

            if total_items != 1:
                self.show_warning(
                    "Invalid Selection",
                    "Instance mode requires exactly ONE item to be selected.\n\n"
                    "Please select a single collection or object, or switch to 'Individual' mode."
                )
                return

        # Execute with loading state
        btn = self.link_preview_btn if dry_run else self.link_execute_btn
        loading_text = BTN_PROCESSING if dry_run else BTN_EXECUTING

        try:
            with self.loading_state(btn, loading_text):
                from blender_lib.models import LinkOperationParams

                # Create operation parameters
                params = LinkOperationParams(
                    target_file=target_file,
                    target_scene=target_scene,
                    source_file=self.link_source_file,
                    item_names=item_names,
                    item_types=item_types,
                    target_collection=target_collection if target_collection else "",
                    link_mode=link_mode,
                    hide_viewport=self.link_as_hidden_checkbox.isChecked(),
                    hide_instancer=self.link_hide_instancer_checkbox.isChecked()
                )

                if dry_run:
                    # Preview mode
                    preview = self.controller.project.blender_service.preview_link_operation(params)

                    if preview.errors:
                        error_msg = "<b>Cannot link due to errors:</b><br>"
                        for error in preview.errors:
                            error_msg += f"  • {error}<br>"

                        self.show_error(TITLE_LINK_ERRORS, error_msg)
                    else:
                        # Show preview dialog
                        dialog = OperationPreviewDialog(preview, self)
                        dialog.exec()

                else:
                    # Execute mode
                    result = self.controller.project.blender_service.execute_link_operation(params)

                    if result.success:
                        self.show_success(
                            TITLE_LINK_COMPLETE,
                            TMPL_LINK_COMPLETE.format(
                                message=result.message,
                                changes=result.changes_made
                            )
                        )

                        # Clear selection
                        self.link_items_list.clearSelection()
                    else:
                        error_msg = f"<b>Link operation failed:</b><br>{result.message}<br>"
                        if result.errors:
                            error_msg += "<br><b>Errors:</b><br>"
                            for error in result.errors:
                                error_msg += f"  • {error}<br>"

                        self.show_error(TITLE_LINK_FAILED, error_msg)

        except Exception as e:
            self.show_error("Link Error", f"Failed to link items:\n\n{str(e)}")

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

            # Save add to collection checkbox state
            link_state['add_to_collection'] = self.link_add_to_collection_checkbox.isChecked()

            # Save add suffix checkbox state
            link_state['add_link_suffix'] = self.link_add_suffix_checkbox.isChecked()

            # Save link as hidden checkbox state
            link_state['link_as_hidden'] = self.link_as_hidden_checkbox.isChecked()

            # Save hide instancer checkbox state
            link_state['hide_instancer'] = self.link_hide_instancer_checkbox.isChecked()

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

            # Restore add to collection checkbox state
            add_to_collection = link_state.get('add_to_collection', True)
            self.link_add_to_collection_checkbox.setChecked(add_to_collection)
            # Trigger visibility update
            self._on_add_to_collection_changed(0)

            # Restore add suffix checkbox state
            add_suffix = link_state.get('add_link_suffix', False)
            self.link_add_suffix_checkbox.setChecked(add_suffix)

            # Restore link as hidden checkbox state
            link_as_hidden = link_state.get('link_as_hidden', False)
            self.link_as_hidden_checkbox.setChecked(link_as_hidden)

            # Restore hide instancer checkbox state
            hide_instancer = link_state.get('hide_instancer', False)
            self.link_hide_instancer_checkbox.setChecked(hide_instancer)

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
        """Apply locked file restoration when blender_service is available."""
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

    def _on_link_item_selection_changed(self):
        """Handle item selection change in link items list."""
        selected_items = self.link_items_list.selectedItems()
        # Enable copy button only if exactly one item is selected
        self.link_copy_name_btn.setEnabled(len(selected_items) == 1)

    def _copy_item_name_to_collection(self):
        """Copy the selected item name to the target collection field."""
        selected_items = self.link_items_list.selectedItems()
        if len(selected_items) == 1:
            item_data = selected_items[0].data(Qt.UserRole)
            if item_data and "data" in item_data:
                item_name = item_data["data"].get("name", "")
                if item_name:
                    self.link_collection_input.setText(item_name)
