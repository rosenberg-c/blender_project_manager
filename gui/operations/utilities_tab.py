"""Utilities tab for project cleanup operations."""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QMessageBox, QTabWidget, QDialog, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from gui.operations.base_tab import BaseOperationTab
from gui.broken_links_dialog import BrokenLinksDialog
from gui.similar_files_dialog import SimilarFilesDialog
from gui.ui_strings import (
    TITLE_NO_PROJECT, TITLE_NO_BACKUP_FILES, TITLE_CONFIRM_DELETION,
    TITLE_CLEANUP_COMPLETE, TITLE_RELOAD_COMPLETE, TITLE_ERROR, TITLE_NO_FILE,
    TITLE_NO_EMPTY_DIRS, TITLE_REMOVE_EMPTY_DIRS, TITLE_RELOAD_LIBS,
    TITLE_UNSUPPORTED_FILE, TITLE_FIND_REFERENCES_RESULTS, TITLE_CHECKING_LINKS,
    TITLE_REMOVE_COMPLETE, TITLE_REMOVING_LINKS, TITLE_FINDING_FILES,
    TITLE_RELINK_COMPLETE, TITLE_NO_FILES_FOUND,
    MSG_OPEN_PROJECT_FIRST, MSG_NO_BACKUP_FILES_FOUND, MSG_SELECT_FILE,
    MSG_NO_EMPTY_DIRS_FOUND, MSG_UNSUPPORTED_FILE_TYPE, MSG_NO_FILES_FOUND,
    TMPL_CONFIRM_DELETE_BACKUPS, TMPL_FAILED_TO_CLEAN,
    TMPL_FAILED_REMOVE_DIRS, TMPL_FAILED_RELOAD_LIBS, TMPL_FAILED_FIND_REFS,
    TMPL_FAILED_CHECK_BROKEN_LINKS, TMPL_REMOVE_COMPLETE, TMPL_FAILED_REMOVE_LINKS,
    TMPL_FILES_FOUND, TMPL_EXACT_AND_SIMILAR_FOUND, TMPL_RELINK_COMPLETE,
    TMPL_FAILED_FIND_FILES, TMPL_FAILED_RELINK
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
        # Create main layout for this tab
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget for sub-tabs
        self.sub_tabs = QTabWidget()
        layout.addWidget(self.sub_tabs)

        # Create Clean tab
        clean_tab = self._create_clean_tab()
        self.sub_tabs.addTab(clean_tab, "Clean")

        # Create Library tab
        library_tab = self._create_library_tab()
        self.sub_tabs.addTab(library_tab, "Library")

        # Create Broken Links tab
        broken_links_tab = self._create_broken_links_tab()
        self.sub_tabs.addTab(broken_links_tab, "Broken Links")

    def set_file(self, file_path):
        """Set the currently selected file and update button states.

        Args:
            file_path: Path to the selected file
        """
        super().set_file(file_path)

        # Enable find references button for .blend files and texture files
        if file_path and (self.is_blend_file(file_path) or self.is_texture_file(file_path)):
            self.find_references_btn.setEnabled(True)
        else:
            self.find_references_btn.setEnabled(False)

    def _create_clean_tab(self):
        """Create the Clean sub-tab for cleanup operations."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

        info_label = QLabel("<b>Cleanup Operations:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Tools for cleaning up your project and freeing disk space.")
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

        # Remove empty directories section
        empty_dirs_label = QLabel("<b>Empty Directories:</b>")
        tab_layout.addWidget(empty_dirs_label)

        empty_dirs_desc = QLabel("Remove empty directories from the project to keep it organized.")
        empty_dirs_desc.setWordWrap(True)
        tab_layout.addWidget(empty_dirs_desc)

        self.remove_empty_dirs_btn = QPushButton("Remove Empty Directories")
        self.remove_empty_dirs_btn.clicked.connect(self._remove_empty_directories)
        self.remove_empty_dirs_btn.setToolTip("Remove all empty directories from the project")
        tab_layout.addWidget(self.remove_empty_dirs_btn)

        # Unused files section
        unused_files_label = QLabel("<b>Unused Files:</b>")
        tab_layout.addWidget(unused_files_label)

        unused_files_desc = QLabel(
            "Find files that are not referenced by any .blend file in your project. "
            "This includes unused textures, .blend files, and backup files. "
            "Useful for identifying files that can be safely removed to free up disk space."
        )
        unused_files_desc.setWordWrap(True)
        tab_layout.addWidget(unused_files_desc)

        self.find_unused_files_btn = QPushButton("Find Unused Files")
        self.find_unused_files_btn.clicked.connect(self._find_unused_files)
        self.find_unused_files_btn.setToolTip("Scan project for files not referenced by any .blend file")
        tab_layout.addWidget(self.find_unused_files_btn)

        # Add stretch to push everything to top
        tab_layout.addStretch()

        # Set content widget in scroll area
        scroll.setWidget(content)

        return scroll

    def _create_library_tab(self):
        """Create the Library sub-tab for library operations."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # Create content widget
        content = QWidget()
        tab_layout = QVBoxLayout(content)

        info_label = QLabel("<b>Library Operations:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel("Tools for managing library links in your .blend files.")
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(10)

        # Reload library links section
        library_label = QLabel("<b>Reload Library Links:</b>")
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

        tab_layout.addSpacing(20)

        # Find references section
        find_refs_label = QLabel("<b>Find References:</b>")
        tab_layout.addWidget(find_refs_label)

        find_refs_desc = QLabel(
            "Find all .blend files that reference the selected file. "
            "Works for .blend files (library links) and texture files (image usage). "
            "Useful for understanding file dependencies."
        )
        find_refs_desc.setWordWrap(True)
        tab_layout.addWidget(find_refs_desc)

        self.find_references_btn = QPushButton("Find References to Selected File")
        self.find_references_btn.clicked.connect(self._find_references)
        self.find_references_btn.setToolTip("Find all files that link to the selected .blend file")
        self.find_references_btn.setEnabled(False)  # Enabled when .blend file is selected
        tab_layout.addWidget(self.find_references_btn)

        # Add stretch to push everything to top
        tab_layout.addStretch()

        # Set content widget in scroll area
        scroll.setWidget(content)

        return scroll

    def _create_broken_links_tab(self):
        """Create the Broken Links sub-tab for checking broken dependencies."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        tab_layout = QVBoxLayout(content)

        info_label = QLabel("<b>Check Broken Links:</b>")
        tab_layout.addWidget(info_label)

        desc_label = QLabel(
            "Find all broken links in your .blend files, including:\n"
            "• Missing library files (linked objects/collections)\n"
            "• Missing texture files (images)\n"
            "\n"
            "This helps identify missing dependencies that need to be fixed."
        )
        desc_label.setWordWrap(True)
        tab_layout.addWidget(desc_label)

        tab_layout.addSpacing(10)

        self.check_broken_links_btn = QPushButton("Check All .blend Files for Broken Links")
        self.check_broken_links_btn.clicked.connect(self._check_broken_links)
        self.check_broken_links_btn.setToolTip("Scan all .blend files in the project for broken links")
        tab_layout.addWidget(self.check_broken_links_btn)

        tab_layout.addStretch()

        scroll.setWidget(content)

        return scroll

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

    def _remove_empty_directories(self):
        """Remove all empty directories from the project."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        try:
            # Find and count empty directories
            project_root = self.get_project_root()
            empty_dirs = []

            # Walk through all directories, depth-first (deepest first)
            for dirpath, dirnames, filenames in project_root.walk(top_down=False):
                # Skip if it's the project root itself
                if dirpath == project_root:
                    continue

                # Check if directory is empty (no files and no subdirectories)
                try:
                    if not any(dirpath.iterdir()):
                        empty_dirs.append(dirpath)
                except (OSError, PermissionError):
                    # Skip directories we can't read
                    continue

            if not empty_dirs:
                self.show_info(TITLE_NO_EMPTY_DIRS, MSG_NO_EMPTY_DIRS_FOUND)
                return

            # Confirm with user
            confirmed = self.confirm(
                TITLE_REMOVE_EMPTY_DIRS,
                f"Found {len(empty_dirs)} empty director{'y' if len(empty_dirs) == 1 else 'ies'}.\n\n"
                f"Remove {'it' if len(empty_dirs) == 1 else 'them'}?"
            )

            if not confirmed:
                return

            # Delete directories iteratively with loading cursor
            # Keep removing until no more empty directories (handles nested empties)
            removed_count = 0
            failed = []

            def remove_directories():
                nonlocal removed_count, failed
                while True:
                    found_empty = False
                    for dirpath, dirnames, filenames in project_root.walk(top_down=False):
                        if dirpath == project_root:
                            continue
                        try:
                            if not any(dirpath.iterdir()):
                                dirpath.rmdir()
                                removed_count += 1
                                found_empty = True
                        except Exception as e:
                            failed.append(f"{dirpath.name}: {str(e)}")

                    # If no empty directories found this pass, we're done
                    if not found_empty:
                        break

            self.with_loading_cursor(remove_directories)

            # Show results
            message_parts = []
            if removed_count > 0:
                message_parts.append(f"<b>Successfully removed {removed_count} empty director{'y' if removed_count == 1 else 'ies'}</b><br>")

            if failed:
                message_parts.append(f"<br><b>Failed to remove {len(failed)} director{'y' if len(failed) == 1 else 'ies'}:</b><br>")
                for error in failed[:5]:
                    message_parts.append(f"  • {error}<br>")
                if len(failed) > 5:
                    message_parts.append(f"  ... and {len(failed) - 5} more<br>")

            self.show_info(TITLE_CLEANUP_COMPLETE, "".join(message_parts))

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_REMOVE_DIRS.format(error=str(e)))

    def _find_unused_files(self):
        """Find files not referenced by any .blend file."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        try:
            from gui.progress_dialog import OperationProgressDialog

            project_root = self.get_project_root()

            # Create and show progress dialog
            progress_dialog = OperationProgressDialog("Finding Unused Files", self)
            progress_dialog.show()

            # Run scan
            result = None

            def progress_callback(percent, message):
                progress_dialog.update_progress(percent, message)
                progress_dialog.log_text.append(message)

            try:
                result = self.controller.project.blender_service.find_unused_files(
                    project_root,
                    include_backups=True,
                    progress_callback=progress_callback
                )

                if result and result.get("success", False):
                    progress_dialog.update_progress(100, "Scan complete!")
                    progress_dialog.exec()

                    # Show results dialog
                    from gui.unused_files_dialog import UnusedFilesDialog

                    dialog = UnusedFilesDialog(result, project_root, self)
                    dialog.exec()
                else:
                    errors = result.get("errors", ["Unknown error"]) if result else ["Unknown error"]
                    progress_dialog.mark_error("\n".join(errors[:3]))
                    progress_dialog.exec()

            except Exception as e:
                progress_dialog.mark_error(str(e))
                progress_dialog.exec()

        except Exception as e:
            self.show_error("Error", f"Failed to find unused files: {str(e)}")

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

            self.show_info(TITLE_RELOAD_COMPLETE, "".join(message_parts))

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_RELOAD_LIBS.format(error=str(e)))

    def _find_references(self):
        """Find all .blend files that reference the selected .blend file."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        if not self.current_file:
            self.show_warning(TITLE_NO_FILE, MSG_SELECT_FILE)
            return

        if not (self.is_blend_file(self.current_file) or self.is_texture_file(self.current_file)):
            self.show_warning(TITLE_UNSUPPORTED_FILE, MSG_UNSUPPORTED_FILE_TYPE)
            return

        try:
            from pathlib import Path
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            # Run the find references script
            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "find_references.py"
            project_root = self.get_project_root()

            # Show loading cursor
            def find_operation():
                result = runner.run_script(
                    script_path,
                    {
                        "target-file": str(self.current_file),
                        "project-root": str(project_root)
                    },
                    timeout=TIMEOUT_VERY_LONG
                )
                return result

            result = self.with_loading_cursor(find_operation)

            # Parse JSON output
            data = extract_json_from_output(result.stdout)

            if not data.get("success", False):
                errors = data.get("errors", [])
                raise Exception(errors[0] if errors else "Unknown error")

            # Show results
            target_name = data.get("target_name", self.current_file.name)
            file_type = data.get("file_type", "blend")
            referencing_files = data.get("referencing_files", [])
            files_scanned = data.get("files_scanned", 0)
            errors = data.get("errors", [])
            warnings = data.get("warnings", [])

            message_parts = []

            if not referencing_files:
                message_parts.append(f"<b>No references found to '{target_name}'</b><br>")
                message_parts.append(f"<br>Scanned {files_scanned} .blend file(s) in the project.<br>")
                if file_type == "texture":
                    message_parts.append(f"<br><i>This texture is not used by any .blend files.</i><br>")
                else:
                    message_parts.append(f"<br><i>This file is not linked by any other .blend files.</i><br>")
            else:
                message_parts.append(f"<b>Found {len(referencing_files)} file(s) referencing '{target_name}':</b><br><br>")

                for ref in referencing_files[:10]:  # Show first 10
                    file_name = ref.get("file_name", "Unknown")
                    message_parts.append(f"<b>• {file_name}</b><br>")

                    # Handle texture references
                    if file_type == "texture":
                        images_count = ref.get("images_count", 0)
                        images = ref.get("images", [])

                        if images_count > 0:
                            message_parts.append(f"  Uses texture {images_count} time(s)")
                            if images:
                                img_names = [img.get("name", "Unknown") for img in images[:3]]
                                message_parts.append(f" (as {', '.join(img_names)}")
                                if len(images) > 3:
                                    message_parts.append(f", +{len(images) - 3} more")
                                message_parts.append(")")
                            message_parts.append("<br>")

                    # Handle blend file references
                    else:
                        linked_objects = ref.get("linked_objects_count", 0)
                        linked_collections = ref.get("linked_collections_count", 0)

                        if linked_objects > 0:
                            message_parts.append(f"  Linked objects: {linked_objects}")
                            obj_names = ref.get("linked_objects", [])
                            if obj_names:
                                message_parts.append(f" ({', '.join(obj_names[:3])}")
                                if len(obj_names) > 3:
                                    message_parts.append(f", +{len(obj_names) - 3} more")
                                message_parts.append(")")
                            message_parts.append("<br>")

                        if linked_collections > 0:
                            message_parts.append(f"  Linked collections: {linked_collections}")
                            col_names = ref.get("linked_collections", [])
                            if col_names:
                                message_parts.append(f" ({', '.join(col_names[:3])}")
                                if len(col_names) > 3:
                                    message_parts.append(f", +{len(col_names) - 3} more")
                                message_parts.append(")")
                            message_parts.append("<br>")

                    message_parts.append("<br>")

                if len(referencing_files) > 10:
                    message_parts.append(f"<i>... and {len(referencing_files) - 10} more file(s)</i><br>")

                message_parts.append(f"<br>Total files scanned: {files_scanned}<br>")

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

            self.show_info(TITLE_FIND_REFERENCES_RESULTS, "".join(message_parts))

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_FIND_REFS.format(error=str(e)))

    def _check_broken_links(self):
        """Check all .blend files in the project for broken links."""
        if not self.controller.project.is_open:
            self.show_warning(TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        try:
            from pathlib import Path
            from PySide6.QtWidgets import QApplication
            from gui.progress_dialog import OperationProgressDialog
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "check_broken_links.py"
            project_root = self.get_project_root()

            self.check_broken_links_btn.setEnabled(False)
            QApplication.processEvents()

            progress_dialog = OperationProgressDialog(TITLE_CHECKING_LINKS, self)
            progress_dialog.show()
            QApplication.processEvents()

            def on_output_line(line: str):
                """Process each line of output from Blender script."""
                if line.startswith("LOG: "):
                    message = line[5:]
                    progress_dialog.log_text.append(message)
                    QApplication.processEvents()

            try:
                result = runner.run_script_with_progress(
                    script_path,
                    {
                        "project-root": str(project_root)
                    },
                    progress_callback=on_output_line,
                    timeout=TIMEOUT_VERY_LONG
                )

                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                progress_dialog.update_progress(100, "Check complete!")
                progress_dialog.exec()

                dialog = BrokenLinksDialog(data, self.controller, self)
                dialog.remove_requested.connect(lambda links: self._remove_broken_links(links, dialog))
                dialog.find_requested.connect(lambda links: self._find_and_relink(links, dialog))
                dialog.remap_requested.connect(lambda refs: self._remap_collection_names(refs, dialog))
                dialog.exec()

            except Exception as e:
                progress_dialog.mark_error(str(e))
                progress_dialog.exec()
                raise

            finally:
                self.check_broken_links_btn.setEnabled(True)

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_CHECK_BROKEN_LINKS.format(error=str(e)))

    def _remove_broken_links(self, links_to_remove: list, dialog=None):
        """Remove the selected broken links.

        Args:
            links_to_remove: List of broken link dictionaries to remove
            dialog: Optional BrokenLinksDialog to update after removal
        """
        try:
            import json
            from pathlib import Path
            from PySide6.QtWidgets import QApplication
            from gui.progress_dialog import OperationProgressDialog
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "fix_broken_links.py"

            progress_dialog = OperationProgressDialog(TITLE_REMOVING_LINKS, self)
            progress_dialog.show()
            QApplication.processEvents()

            def on_output_line(line: str):
                """Process each line of output from Blender script."""
                if line.startswith("LOG: "):
                    message = line[5:]
                    progress_dialog.log_text.append(message)
                    QApplication.processEvents()

            try:
                links_json = json.dumps(links_to_remove)

                result = runner.run_script_with_progress(
                    script_path,
                    {
                        "links-to-fix": links_json
                    },
                    progress_callback=on_output_line,
                    timeout=TIMEOUT_VERY_LONG
                )

                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                progress_dialog.update_progress(100, "Remove complete!")
                progress_dialog.exec()

                files_fixed = data.get("files_fixed", [])
                total_fixed = data.get("total_fixed", 0)
                errors = data.get("errors", [])

                message_parts = []

                if total_fixed > 0:
                    message_parts.append(f"<b>Successfully removed {total_fixed} broken link(s)!</b><br>")
                    message_parts.append(f"<br>Files modified: {len(files_fixed)}<br><br>")

                    for file_info in files_fixed[:5]:
                        file_name = file_info.get("file_name", "Unknown")
                        fixed_libraries = file_info.get("fixed_libraries", 0)
                        fixed_textures = file_info.get("fixed_textures", 0)

                        message_parts.append(f"<b>• {file_name}</b><br>")
                        if fixed_libraries > 0:
                            message_parts.append(f"  Removed {fixed_libraries} broken library link(s)<br>")
                        if fixed_textures > 0:
                            message_parts.append(f"  Removed {fixed_textures} broken texture(s)<br>")

                    if len(files_fixed) > 5:
                        message_parts.append(f"<br><i>... and {len(files_fixed) - 5} more file(s)</i><br>")
                else:
                    message_parts.append("<b>No broken links were removed.</b><br>")

                if errors:
                    message_parts.append(f"<br><b>Errors:</b><br>")
                    for error in errors[:5]:
                        message_parts.append(f"  • {error}<br>")
                    if len(errors) > 5:
                        message_parts.append(f"  ... and {len(errors) - 5} more<br>")

                self.show_info(TITLE_REMOVE_COMPLETE, "".join(message_parts))

            except Exception as e:
                progress_dialog.mark_error(str(e))
                progress_dialog.exec()
                raise

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_REMOVE_LINKS.format(error=str(e)))

    def _find_and_relink(self, broken_links: list, dialog=None):
        """Find missing files and relink them.

        Args:
            broken_links: List of broken link dictionaries to find and relink
            dialog: Optional BrokenLinksDialog to update after relinking
        """
        try:
            import json
            from pathlib import Path
            from PySide6.QtWidgets import QApplication, QMessageBox
            from gui.progress_dialog import OperationProgressDialog
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "find_and_relink.py"
            project_root = self.get_project_root()

            progress_dialog = OperationProgressDialog(TITLE_FINDING_FILES, self)
            progress_dialog.show()
            QApplication.processEvents()

            def on_output_line(line: str):
                """Process each line of output from Blender script."""
                if line.startswith("LOG: "):
                    message = line[5:]
                    progress_dialog.log_text.append(message)
                    QApplication.processEvents()

            try:
                links_json = json.dumps(broken_links)

                result = runner.run_script_with_progress(
                    script_path,
                    {
                        "broken-links": links_json,
                        "project-root": str(project_root),
                        "mode": "find"
                    },
                    progress_callback=on_output_line,
                    timeout=TIMEOUT_VERY_LONG
                )

                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                progress_dialog.update_progress(100, "Search complete!")
                progress_dialog.exec()

                found_files = data.get("found_files", [])
                similar_files = data.get("similar_files", [])
                not_found = data.get("not_found", [])

                if not found_files and not similar_files:
                    self.show_info(TITLE_NO_FILES_FOUND, MSG_NO_FILES_FOUND)
                    return

                relink_map = {}

                for found in found_files:
                    missing_path = found.get("missing_path", "")
                    found_paths = found.get("found_paths", [])

                    if found_paths:
                        new_path = found_paths[0]
                        relink_map[missing_path] = new_path

                if similar_files:
                    if found_files:
                        reply = QMessageBox.question(
                            self,
                            TITLE_FINDING_FILES,
                            TMPL_EXACT_AND_SIMILAR_FOUND.format(
                                exact_count=len(found_files),
                                similar_count=len(similar_files)
                            ),
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )

                        if reply != QMessageBox.Yes:
                            return

                    similar_dialog = SimilarFilesDialog(similar_files, project_root, self)
                    if similar_dialog.exec() == QDialog.Accepted:
                        similar_selections = similar_dialog.get_selected_matches()
                        relink_map.update(similar_selections)
                    else:
                        if not found_files:
                            return
                elif found_files:
                    details_parts = []
                    for found in found_files:
                        missing_filename = found.get("missing_filename", "")
                        found_paths = found.get("found_paths", [])
                        if found_paths:
                            new_path = found_paths[0]
                            details_parts.append(f"• {missing_filename} → {Path(new_path).relative_to(project_root)}")

                    details = "\n".join(details_parts[:10])
                    if len(details_parts) > 10:
                        details += f"\n... and {len(details_parts) - 10} more"

                    reply = QMessageBox.question(
                        self,
                        TITLE_FINDING_FILES,
                        TMPL_FILES_FOUND.format(
                            found_count=len(found_files),
                            details=details
                        ),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply != QMessageBox.Yes:
                        return

                if not relink_map:
                    return

                progress_dialog = OperationProgressDialog(TITLE_FINDING_FILES, self)
                progress_dialog.show()
                QApplication.processEvents()

                relink_map_json = json.dumps(relink_map)

                result = runner.run_script_with_progress(
                    script_path,
                    {
                        "broken-links": links_json,
                        "project-root": str(project_root),
                        "mode": "relink",
                        "relink-map": relink_map_json
                    },
                    progress_callback=on_output_line,
                    timeout=TIMEOUT_VERY_LONG
                )

                data = extract_json_from_output(result.stdout)

                if "error" in data and data["error"]:
                    raise Exception(data["error"])

                progress_dialog.update_progress(100, "Relink complete!")
                progress_dialog.exec()

                files_relinked = data.get("files_relinked", [])
                total_relinked = data.get("total_relinked", 0)
                errors = data.get("errors", [])

                message_parts = []

                if total_relinked > 0:
                    message_parts.append(f"<b>Successfully relinked {total_relinked} file(s)!</b><br>")
                    message_parts.append(f"<br>Files modified: {len(files_relinked)}<br><br>")

                    for file_info in files_relinked[:5]:
                        file_name = file_info.get("file_name", "Unknown")
                        relinked_libraries = file_info.get("relinked_libraries", 0)
                        relinked_textures = file_info.get("relinked_textures", 0)

                        message_parts.append(f"<b>• {file_name}</b><br>")
                        if relinked_libraries > 0:
                            message_parts.append(f"  Relinked {relinked_libraries} library link(s)<br>")
                        if relinked_textures > 0:
                            message_parts.append(f"  Relinked {relinked_textures} texture(s)<br>")

                    if len(files_relinked) > 5:
                        message_parts.append(f"<br><i>... and {len(files_relinked) - 5} more file(s)</i><br>")
                else:
                    message_parts.append("<b>No files were relinked.</b><br>")

                if errors:
                    message_parts.append(f"<br><b>Errors:</b><br>")
                    for error in errors[:5]:
                        message_parts.append(f"  • {error}<br>")
                    if len(errors) > 5:
                        message_parts.append(f"  ... and {len(errors) - 5} more<br>")

                self.show_info(TITLE_RELINK_COMPLETE, "".join(message_parts))

                if dialog and total_relinked > 0:
                    relinked_paths = set(relink_map.keys())
                    dialog.mark_as_relinked(relinked_paths)

            except Exception as e:
                progress_dialog.mark_error(str(e))
                progress_dialog.exec()
                raise

        except Exception as e:
            self.show_error(TITLE_ERROR, TMPL_FAILED_FIND_FILES.format(error=str(e)))

    def _remap_collection_names(self, collection_refs: list, dialog=None):
        """Remap broken collection name references.

        Args:
            collection_refs: List of broken collection reference dictionaries
            dialog: Optional BrokenLinksDialog to update after remapping
        """
        try:
            import json
            from pathlib import Path
            from PySide6.QtWidgets import QApplication, QDialog
            from gui.progress_dialog import OperationProgressDialog
            from gui.collection_remap_dialog import CollectionRemapDialog
            from blender_lib.constants import TIMEOUT_VERY_LONG
            from services.blender_service import extract_json_from_output

            # Show dialog for user to select new collection names
            remap_dialog = CollectionRemapDialog(collection_refs, self)
            if remap_dialog.exec() != QDialog.Accepted:
                return

            remappings = remap_dialog.get_remappings()
            if not remappings:
                self.show_warning("No Remappings", "No collection remappings were selected.")
                return

            # Group remappings by file
            remappings_by_file = {}
            for remap in remappings:
                file_path = remap["file"]
                if file_path not in remappings_by_file:
                    remappings_by_file[file_path] = []
                remappings_by_file[file_path].append(remap)

            runner = self.get_blender_runner()
            script_path = Path(__file__).parent.parent.parent / "blender_lib" / "fix_collection_names.py"

            progress_dialog = OperationProgressDialog("Remapping Collections", self)
            progress_dialog.show()
            QApplication.processEvents()

            def on_output_line(line: str):
                """Process each line of output from Blender script."""
                if line.startswith("LOG: "):
                    message = line[5:]
                    progress_dialog.log_text.append(message)
                    QApplication.processEvents()

            total_remapped = 0
            total_failed = 0
            files_modified = []

            try:
                # Process each file
                for file_path, file_remappings in remappings_by_file.items():
                    progress_dialog.log_text.append(f"\nProcessing {Path(file_path).name}...")
                    QApplication.processEvents()

                    remappings_json = json.dumps(file_remappings)

                    result = runner.run_script_with_progress(
                        script_path,
                        {
                            "blend-file": file_path,
                            "remappings": remappings_json
                        },
                        progress_callback=on_output_line,
                        timeout=TIMEOUT_VERY_LONG
                    )

                    data = extract_json_from_output(result.stdout)

                    if "error" in data and data["error"]:
                        raise Exception(data["error"])

                    total_remapped += data.get("total_remapped", 0)
                    total_failed += data.get("total_failed", 0)

                    if data.get("total_remapped", 0) > 0:
                        files_modified.append({
                            "file_name": data.get("file_name", Path(file_path).name),
                            "remapped_count": data.get("total_remapped", 0)
                        })

                progress_dialog.update_progress(100, "Remapping complete!")
                progress_dialog.exec()

                # Build result message
                message_parts = []

                if total_remapped > 0:
                    message_parts.append(f"<b>Successfully remapped {total_remapped} collection reference(s)!</b><br>")
                    message_parts.append(f"<br>Files modified: {len(files_modified)}<br><br>")

                    for file_info in files_modified[:5]:
                        file_name = file_info.get("file_name", "Unknown")
                        remapped_count = file_info.get("remapped_count", 0)
                        message_parts.append(f"<b>• {file_name}</b><br>")
                        message_parts.append(f"  Remapped {remapped_count} collection(s)<br>")

                    if len(files_modified) > 5:
                        message_parts.append(f"<br><i>... and {len(files_modified) - 5} more file(s)</i><br>")
                else:
                    message_parts.append("<b>No collections were remapped.</b><br>")

                if total_failed > 0:
                    message_parts.append(f"<br><span style='color: orange;'>{total_failed} remapping(s) failed</span><br>")

                self.show_info("Remap Complete", "".join(message_parts))

            except Exception as e:
                progress_dialog.mark_error(str(e))
                progress_dialog.exec()
                raise

        except Exception as e:
            self.show_error("Error", f"Failed to remap collections:\n\n{str(e)}")
