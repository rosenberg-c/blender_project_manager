"""Operations panel for file operations."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QApplication,
    QTabWidget, QListWidget, QListWidgetItem, QComboBox, QCheckBox
)
from PySide6.QtGui import QCursor

from controllers.file_operations_controller import FileOperationsController
from gui.preview_dialog import OperationPreviewDialog
from gui.progress_dialog import OperationProgressDialog
from gui.theme import Theme


class OperationsPanelWidget(QWidget):
    """Panel for configuring and executing file operations."""

    def __init__(self, controller: FileOperationsController, parent=None):
        """Initialize operations panel.

        Args:
            controller: File operations controller
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.current_file: Path | None = None
        self.obj_list_data = {"objects": [], "collections": []}

        self.setup_ui()

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
        btn_row.addWidget(self.tex_browse_btn)

        self.tex_preview_btn = QPushButton("Preview Changes")
        self.tex_preview_btn.setEnabled(False)
        self.tex_preview_btn.setProperty("class", "info")
        btn_row.addWidget(self.tex_preview_btn)

        tab_layout.addLayout(btn_row)

        self.tex_execute_btn = QPushButton("Execute Rename")
        self.tex_execute_btn.setEnabled(False)
        self.tex_execute_btn.setProperty("class", "primary")
        tab_layout.addWidget(self.tex_execute_btn)

        # Add stretch
        tab_layout.addStretch()

        # Add tab to tabs widget
        self.tabs.addTab(tab, "Rename Texture")

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
                        message_parts.append(f"<br><b>Will update linked references in {updated_files_count} other file(s)</b><br>")
                else:
                    message_parts.append("<b>No items will be renamed.</b><br>")
            else:
                # Execute mode
                if renamed:
                    message_parts.append(f"<b>Successfully renamed {len(renamed)} item(s)!</b><br>")

                    if updated_files_count > 0:
                        message_parts.append(f"<br><b>Updated {updated_files_count} file(s) with linked references</b><br>")

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
