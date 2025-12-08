"""Move/Rename tab for file and directory operations."""

from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QWidget, QFileDialog, QApplication
)

from gui.operations.base_tab import BaseOperationTab
from gui.preview_dialog import OperationPreviewDialog
from gui.progress_dialog import OperationProgressDialog
from gui.ui_strings import (
    TITLE_NO_FILE, TITLE_NO_CHANGE, TITLE_CONFIRM_OPERATION, TITLE_SUCCESS, TITLE_ERROR,
    MSG_SELECT_FILE, MSG_SOURCE_TARGET_SAME,
    BTN_EXECUTE_MOVE, BTN_EXECUTING,
    LABEL_NO_FILE_SELECTED, LABEL_MOVE_PERFORMANCE_INFO,
    TMPL_CONFIRM_MOVE, TMPL_SUCCESS_WITH_CHANGES, TMPL_OPERATION_FAILED
)
from blender_lib.constants import TIMEOUT_MEDIUM
from services.blender_service import extract_json_from_output


class MoveRenameTab(BaseOperationTab):
    """Tab for moving and renaming files and directories."""

    def __init__(self, controller, parent=None):
        """Initialize move/rename tab.

        Args:
            controller: File operations controller
            parent: Parent widget (operations panel)
        """
        super().__init__(controller, parent)
        self.setup_ui()

    def setup_ui(self):
        """Create the UI for the move/rename tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

        # Move/Rename section
        move_label = QLabel("<b>Move/Rename File or Directory:</b>")
        tab_layout.addWidget(move_label)

        # Performance info
        perf_info_label = QLabel(LABEL_MOVE_PERFORMANCE_INFO)
        perf_info_label.setWordWrap(True)
        perf_info_label.setStyleSheet("color: #666; padding: 5px 0px;")
        tab_layout.addWidget(perf_info_label)

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
        self.execute_btn = QPushButton(BTN_EXECUTE_MOVE)
        self.execute_btn.clicked.connect(self._execute_operation)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setProperty("class", "primary")
        tab_layout.addWidget(self.execute_btn)

        # Add stretch to push everything to top
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

        # Update UI for move/rename tab
        self.new_path_input.setText(str(file_path))
        self.browse_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.execute_btn.setEnabled(True)

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
            self.show_warning(TITLE_NO_FILE, MSG_SELECT_FILE)
            return

        new_path = Path(self.new_path_input.text())

        if new_path == self.current_file:
            self.show_info(TITLE_NO_CHANGE, MSG_SOURCE_TARGET_SAME)
            return

        # Check file/directory type
        is_directory = self.is_directory(self.current_file)
        is_blend = self.is_blend_file(self.current_file)
        is_texture = self.is_texture_file(self.current_file)

        try:
            with self.loading_state(self.preview_btn, "Loading Preview..."):
                if is_directory or is_blend:
                    # Handle directories and .blend files using controller
                    preview = self.controller.preview_move_file(self.current_file, new_path)

                    # Show preview dialog
                    dialog = OperationPreviewDialog(preview, self)
                    dialog.exec()

                elif is_texture:
                    # Handle texture files using Blender script
                    runner = self.get_blender_runner()
                    script_path = Path(__file__).parent.parent.parent / "blender_lib" / "rename_texture.py"
                    project_root = self.get_project_root()

                    # Run preview
                    result = runner.run_script(
                        script_path,
                        {
                            "old-path": str(self.current_file),
                            "new-path": str(new_path),
                            "project-root": str(project_root),
                            "dry-run": "true"
                        },
                        timeout=TIMEOUT_MEDIUM
                    )

                    # Parse JSON output
                    data = extract_json_from_output(result.stdout)

                    if not data.get("success", False):
                        errors = data.get("errors", [])
                        raise Exception(errors[0] if errors else "Unknown error")

                    # Show results
                    self._show_texture_preview_results(data, new_path)

                else:
                    # Unsupported file type
                    self.show_warning(
                        "Unsupported File Type",
                        f"Cannot preview move operation for {self.current_file.suffix} files.\n\n"
                        "Supported: directories, .blend files, and texture files (.png, .jpg, .jpeg, .exr, .hdr, .tif, .tiff)"
                    )

        except Exception as e:
            self.show_error("Preview Error", f"Failed to generate preview:\n\n{str(e)}")

    def _show_texture_preview_results(self, data: dict, new_path: Path):
        """Show preview results for texture file rename.

        Args:
            data: Result data from Blender script
            new_path: New path for texture file
        """
        updated_files = data.get("updated_files", [])
        updated_files_count = data.get("updated_files_count", 0)
        warnings = data.get("warnings", [])

        message_parts = []
        message_parts.append(f"<b>Will rename texture file:</b><br>")
        message_parts.append(f"  {self.current_file.name} → {new_path.name}<br>")

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

        if warnings:
            message_parts.append(f"<br><b>Warnings:</b><br>")
            for warning in warnings[:5]:
                message_parts.append(f"  • {warning}<br>")
            if len(warnings) > 5:
                message_parts.append(f"  ... and {len(warnings) - 5} more<br>")

        self.show_info("Preview Results", "".join(message_parts))

    def _execute_operation(self):
        """Execute the move operation."""
        if not self.current_file:
            self.show_warning(TITLE_NO_FILE, MSG_SELECT_FILE)
            return

        new_path = Path(self.new_path_input.text())

        if new_path == self.current_file:
            self.show_info(TITLE_NO_CHANGE, MSG_SOURCE_TARGET_SAME)
            return

        # Check file/directory type
        is_directory = self.is_directory(self.current_file)
        is_blend = self.is_blend_file(self.current_file)
        is_texture = self.is_texture_file(self.current_file)

        # Confirm with user
        item_type = "directory" if is_directory else "file"
        confirmed = self.confirm(
            TITLE_CONFIRM_OPERATION,
            TMPL_CONFIRM_MOVE.format(
                item_type=item_type,
                old_path=self.current_file,
                new_path=new_path
            )
        )

        if not confirmed:
            return

        try:
            if is_directory or is_blend:
                self._execute_move_directory_or_blend(is_directory, new_path)
            elif is_texture:
                self._execute_move_texture(new_path)
            else:
                # Unsupported file type
                self.show_warning(
                    "Unsupported File Type",
                    f"Cannot execute move operation for {self.current_file.suffix} files.\n\n"
                    "Supported: directories, .blend files, and texture files (.png, .jpg, .jpeg, .exr, .hdr, .tif, .tiff)"
                )

        except Exception as e:
            self.show_error("Error", f"Operation failed:\n\n{str(e)}")

    def _execute_move_directory_or_blend(self, is_directory: bool, new_path: Path):
        """Execute move operation for directory or .blend file.

        Args:
            is_directory: Whether the current file is a directory
            new_path: New path for the file/directory
        """
        # Show loading state immediately
        self.execute_btn.setText(BTN_EXECUTING)
        self.execute_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            # Create and show progress dialog
            item_name = f"{self.current_file.name}/" if is_directory else self.current_file.name
            progress_dialog = OperationProgressDialog(f"Moving {item_name}", self)
            progress_dialog.show()
            QApplication.processEvents()

            # Execute operation
            result = self.controller.execute_move_file(
                self.current_file,
                new_path,
                progress_dialog.update_progress
            )

            # Show result
            if result.success:
                progress_dialog.update_progress(100, result.message)
                progress_dialog.exec()

                self.show_success(
                    TITLE_SUCCESS,
                    TMPL_SUCCESS_WITH_CHANGES.format(
                        message=result.message,
                        changes=result.changes_made
                    )
                )

                # Clear selection
                self._clear_selection()
            else:
                progress_dialog.mark_error(result.message)
                progress_dialog.exec()

                self.show_error(TITLE_ERROR, TMPL_OPERATION_FAILED.format(message=result.message))

                # Restore button state on error
                self._restore_button_state()

        except Exception as e:
            self._restore_button_state()
            raise

    def _execute_move_texture(self, new_path: Path):
        """Execute move operation for texture file.

        Args:
            new_path: New path for the texture file
        """
        with self.loading_state(self.execute_btn, BTN_EXECUTING):
            # Also disable other buttons
            self.preview_btn.setEnabled(False)
            self.browse_btn.setEnabled(False)

            try:
                # Handle texture files using Blender script
                runner = self.get_blender_runner()
                script_path = Path(__file__).parent.parent.parent / "blender_lib" / "rename_texture.py"
                project_root = self.get_project_root()

                # Run execute
                result = runner.run_script(
                    script_path,
                    {
                        "old-path": str(self.current_file),
                        "new-path": str(new_path),
                        "project-root": str(project_root),
                        "dry-run": "false"
                    },
                    timeout=TIMEOUT_MEDIUM
                )

                # Parse JSON output
                data = extract_json_from_output(result.stdout)

                if not data.get("success", False):
                    errors = data.get("errors", [])
                    raise Exception(errors[0] if errors else "Unknown error")

                # Show results
                self._show_texture_execute_results(data, new_path)

            finally:
                # Restore other buttons
                self.preview_btn.setEnabled(True)
                self.browse_btn.setEnabled(True)

    def _show_texture_execute_results(self, data: dict, new_path: Path):
        """Show execution results for texture file rename.

        Args:
            data: Result data from Blender script
            new_path: New path for texture file
        """
        updated_files = data.get("updated_files", [])
        updated_files_count = data.get("updated_files_count", 0)
        file_moved = data.get("file_moved", False)
        warnings = data.get("warnings", [])
        errors = data.get("errors", [])

        message_parts = []

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

        self.show_info("Rename Complete", "".join(message_parts))

        # Clear inputs after successful execution
        if file_moved:
            self._clear_selection()
        else:
            self._restore_button_state()

    def _clear_selection(self):
        """Clear the current file selection and reset UI."""
        self.current_file = None
        if self.operations_panel:
            self.operations_panel.file_display.setText(LABEL_NO_FILE_SELECTED)
        self.new_path_input.clear()
        self.browse_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.execute_btn.setText(BTN_EXECUTE_MOVE)
        self.execute_btn.setEnabled(False)

    def _restore_button_state(self):
        """Restore button state after operation."""
        self.execute_btn.setText(BTN_EXECUTE_MOVE)
        self.execute_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
