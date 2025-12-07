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
