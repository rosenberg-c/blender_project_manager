"""Utilities tab for project cleanup operations."""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from gui.operations.base_tab import BaseOperationTab
from gui.ui_strings import (
    TITLE_NO_PROJECT, TITLE_NO_BACKUP_FILES, TITLE_CONFIRM_DELETION,
    TITLE_CLEANUP_COMPLETE, TITLE_ERROR,
    MSG_OPEN_PROJECT_FIRST, MSG_NO_BACKUP_FILES_FOUND,
    TMPL_CONFIRM_DELETE_BACKUPS, TMPL_FAILED_TO_CLEAN
)


class UtilitiesTab(BaseOperationTab):
    """Tab for project utility operations like cleanup."""

    def __init__(self, controller, parent=None):
        """Initialize utilities tab.

        Args:
            controller: File operations controller
            parent: Parent widget (operations panel)
        """
        super().__init__(controller, parent)
        self.setup_ui()

    def setup_ui(self):
        """Create the UI for the utilities tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

        info_label = QLabel("<b>Project Utilities:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Tools for managing and cleaning up your project.")
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(10)

        # Clean backup files section
        backup_label = QLabel("<b>Backup Files:</b>")
        tab_layout.addWidget(backup_label)

        backup_desc = QLabel("Remove Blender's automatic backup files (.blend1, .blend2) to free up disk space.")
        backup_desc.setWordWrap(True)
        tab_layout.addWidget(backup_desc)

        self.clean_blend1_btn = QPushButton("Clean Backup Files")
        self.clean_blend1_btn.clicked.connect(self._clean_blend1_files)
        self.clean_blend1_btn.setToolTip("Remove all .blend1 and .blend2 backup files from the project")
        tab_layout.addWidget(self.clean_blend1_btn)

        tab_layout.addSpacing(20)

        # Reload library links section
        library_label = QLabel("<b>Library Links:</b>")
        tab_layout.addWidget(library_label)

        library_desc = QLabel(
            "Reload all library links in .blend files. "
            "Useful after moving/renaming textures or linked files to ensure Blender displays updated paths."
        )
        library_desc.setWordWrap(True)
        tab_layout.addWidget(library_desc)

        self.reload_libraries_btn = QPushButton("Reload Library Links")
        self.reload_libraries_btn.clicked.connect(self._reload_libraries)
        self.reload_libraries_btn.setToolTip("Reload all library links in all .blend files in the project")
        tab_layout.addWidget(self.reload_libraries_btn)

        # Add stretch to push everything to top
        tab_layout.addStretch()

        # Set content widget in scroll area
        scroll.setWidget(content)

        # Set the main layout for this tab
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _clean_blend1_files(self):
        """Remove all .blend1 and .blend2 backup files from the project."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        try:
            # Find all .blend1 and .blend2 files
            project_root = self.get_project_root()
            blend1_files = list(project_root.rglob('*.blend1'))
            blend2_files = list(project_root.rglob('*.blend2'))
            backup_files = blend1_files + blend2_files

            if not backup_files:
                self.show_info(TITLE_NO_BACKUP_FILES, MSG_NO_BACKUP_FILES_FOUND)
                return

            # Calculate total size
            total_size = sum(f.stat().st_size for f in backup_files)
            size_mb = total_size / (1024 * 1024)

            # Confirm with user
            confirmed = self.confirm(
                TITLE_CONFIRM_DELETION,
                TMPL_CONFIRM_DELETE_BACKUPS.format(
                    count=len(backup_files),
                    blend1_count=len(blend1_files),
                    blend2_count=len(blend2_files),
                    size_mb=size_mb
                )
            )

            if not confirmed:
                return

            # Delete files with loading cursor
            deleted_count = 0
            failed = []

            def delete_backups():
                nonlocal deleted_count, failed
                for backup_file in backup_files:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        failed.append(f"{backup_file.name}: {str(e)}")

            self.with_loading_cursor(delete_backups)

            # Show results
            message_parts = []
            if deleted_count > 0:
                message_parts.append(f"<b>Successfully deleted {deleted_count} file(s)</b><br>")
                message_parts.append(f"Freed {size_mb:.2f} MB of disk space<br>")

            if failed:
                message_parts.append(f"<br><b>Failed to delete {len(failed)} file(s):</b><br>")
                for error in failed[:5]:
                    message_parts.append(f"  • {error}<br>")
                if len(failed) > 5:
                    message_parts.append(f"  ... and {len(failed) - 5} more<br>")

            self.show_info(TITLE_CLEANUP_COMPLETE, "".join(message_parts))

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_TO_CLEAN.format(error=str(e)))

    def _reload_libraries(self):
        """Reload all library links in .blend files in the project."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        # Confirm with user
        confirmed = self.confirm(
            "Reload Library Links",
            "This will reload all library links in all .blend files in your project.\n\n"
            "This is useful after moving or renaming textures/linked files.\n\n"
            "Continue?"
        )

        if not confirmed:
            return

        try:
            from pathlib import Path
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            # Run the reload script
            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "reload_libraries.py"
            project_root = self.get_project_root()

            # Show loading cursor
            def reload_operation():
                result = runner.run_script(
                    script_path,
                    {
                        "project-root": str(project_root),
                        "dry-run": "false"
                    },
                    timeout=TIMEOUT_VERY_LONG
                )
                return result

            result = self.with_loading_cursor(reload_operation)

            # Parse JSON output
            data = extract_json_from_output(result.stdout)

            if not data.get("success", False):
                errors = data.get("errors", [])
                raise Exception(errors[0] if errors else "Unknown error")

            # Show results
            files_processed = data.get("files_processed", 0)
            files_with_libraries = data.get("files_with_libraries", 0)
            total_libraries_reloaded = data.get("total_libraries_reloaded", 0)
            errors = data.get("errors", [])
            warnings = data.get("warnings", [])

            message_parts = []

            if files_processed == 0:
                message_parts.append("<b>No .blend files found in project.</b><br>")
            elif total_libraries_reloaded == 0:
                message_parts.append(f"<b>Processed {files_processed} .blend file(s)</b><br>")
                message_parts.append(f"<br><i>No library links found to reload.</i><br>")
            else:
                message_parts.append(f"<b>Successfully reloaded library links!</b><br>")
                message_parts.append(f"<br>Files processed: {files_processed}<br>")
                message_parts.append(f"Files with libraries: {files_with_libraries}<br>")
                message_parts.append(f"Library links reloaded: {total_libraries_reloaded}<br>")

            if warnings:
                message_parts.append(f"<br><b>Warnings:</b><br>")
                for warning in warnings[:5]:
                    message_parts.append(f"  • {warning}<br>")
                if len(warnings) > 5:
                    message_parts.append(f"  ... and {len(warnings) - 5} more<br>")

            if errors:
                message_parts.append(f"<br><b>Errors:</b><br>")
                for error in errors[:5]:
                    message_parts.append(f"  • {error}<br>")
                if len(errors) > 5:
                    message_parts.append(f"  ... and {len(errors) - 5} more<br>")

            self.show_info("Reload Complete", "".join(message_parts))

        except Exception as e:
            self.show_error(TITLE_ERROR, f"Failed to reload library links:\n\n{str(e)}")
