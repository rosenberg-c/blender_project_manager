"""File browser widget with tree view."""

import json
import subprocess
import platform
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QModelIndex, QRect, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeView, QFileSystemModel, QMessageBox, QStyledItemDelegate, QStyle, QStyleOptionViewItem
)

from controllers.project_controller import ProjectController
from services.blender_service import BlenderService
from gui.progress_dialog import OperationProgressDialog
from blender_lib.constants import TEXTURE_EXTENSIONS
from gui.ui_strings import (
    TITLE_BLENDER_NOT_FOUND, TITLE_ERROR_OPENING_FILE,
    TITLE_CONFIRM_DELETION, TITLE_SUCCESS, TITLE_ERROR,
    TITLE_NO_PROJECT, TITLE_FINDING_REFERENCES,
    MSG_BLENDER_NOT_CONFIGURED, MSG_OPEN_PROJECT_FIRST,
    TMPL_FAILED_TO_OPEN_BLENDER,
    TMPL_CONFIRM_DELETE_FILE, TMPL_CONFIRM_DELETE_DIR,
    TMPL_DELETE_SUCCESS, TMPL_DELETE_FAILED,
    TMPL_SCANNING_REFS, TMPL_ANALYZING_BLEND, TMPL_REFS_COMPLETE,
    TMPL_NO_REFS_FOUND, TMPL_REFS_FOUND_HEADER, TMPL_REFS_SCANNED_FOOTER,
    TMPL_FAILED_FIND_REFS
)


class FileItemDelegate(QStyledItemDelegate):
    """Custom delegate to draw action icons on selected rows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_size = 16
        self.icon_margin = 4
        self.icon_spacing = 2

    def paint(self, painter, option, index):
        """Paint the item with action icons if selected."""
        # Draw the default item
        super().paint(painter, option, index)

        # Draw action icons if this row is selected
        if option.state & QStyle.StateFlag.State_Selected:
            style = option.widget.style()

            # Get the file path from the model
            model = index.model()
            file_path = Path(model.filePath(index))

            x_offset = option.rect.right() - self.icon_margin
            y_pos = option.rect.top() + (option.rect.height() - self.icon_size) // 2

            # Draw trash icon (always shown)
            trash_icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
            trash_rect = QRect(
                x_offset - self.icon_size,
                y_pos,
                self.icon_size,
                self.icon_size
            )
            trash_icon.paint(painter, trash_rect)
            x_offset -= (self.icon_size + self.icon_spacing)

            # Draw find references icon (only for .blend and texture files)
            if file_path.is_file() and self._is_supported_file(file_path):
                find_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)
                find_rect = QRect(
                    x_offset - self.icon_size,
                    y_pos,
                    self.icon_size,
                    self.icon_size
                )
                find_icon.paint(painter, find_rect)

    def _is_supported_file(self, file_path):
        """Check if file is a .blend or texture file."""
        suffix = file_path.suffix.lower()
        return suffix == '.blend' or suffix in TEXTURE_EXTENSIONS

    def get_trash_icon_rect(self, option):
        """Get the rectangle where the trash icon is drawn."""
        return QRect(
            option.rect.right() - self.icon_size - self.icon_margin,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )

    def get_find_icon_rect(self, option):
        """Get the rectangle where the find references icon is drawn."""
        x_offset = option.rect.right() - self.icon_margin - self.icon_size - self.icon_spacing
        return QRect(
            x_offset - self.icon_size,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )


class FileBrowserWidget(QWidget):
    """File browser with tree view and search."""

    file_selected = Signal(Path)

    def __init__(self, project_controller: ProjectController, config_file: Path = None, parent=None):
        """Initialize file browser.

        Args:
            project_controller: The project controller
            config_file: Path to config file for state persistence
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project_controller
        self.config_file = config_file
        self.pending_restore_state = False

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box and buttons
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files...")
        search_layout.addWidget(self.search_box)

        # Collapse/Expand buttons
        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(self.collapse_all)
        search_layout.addWidget(self.collapse_all_btn)

        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(self.expand_all)
        search_layout.addWidget(self.expand_all_btn)

        layout.addLayout(search_layout)

        # Tree view with file system model
        self.tree = QTreeView()
        self.model = QFileSystemModel()

        # Set file filters
        self.model.setNameFilters(['*.blend', '*.png', '*.jpg', '*.jpeg', '*.hdr', '*.exr'])
        self.model.setNameFilterDisables(False)  # Hide non-matching files

        # Connect to directoryLoaded signal for state restoration
        self.model.directoryLoaded.connect(self._on_directory_loaded)

        self.tree.setModel(self.model)
        self.tree.setSelectionMode(QTreeView.SingleSelection)

        # Set custom delegate to draw trash icon on selected rows
        self.delegate = FileItemDelegate(self.tree)
        self.tree.setItemDelegate(self.delegate)

        # Hide size, type, and date columns for simpler view
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)

        # Enable sorting
        self.tree.setSortingEnabled(True)

        # Connect selection signal
        self.tree.clicked.connect(self._on_item_clicked)

        # Connect double-click signal to open in Blender
        self.tree.doubleClicked.connect(self._on_item_double_clicked)

        # Install event filter to handle clicks on trash icon
        self.tree.viewport().installEventFilter(self)

        layout.addWidget(self.tree)

        # State restoration data
        self.restore_data = None

    def set_root(self, path: Path):
        """Set the root directory for the file browser.

        Args:
            path: Root directory path
        """
        root_index = self.model.setRootPath(str(path))
        self.tree.setRootIndex(root_index)
        self.tree.expandToDepth(1)  # Expand first level

    def collapse_all(self):
        """Collapse all directories in the tree."""
        self.tree.collapseAll()

    def expand_all(self):
        """Expand all directories in the tree."""
        self.tree.expandAll()

    def _on_item_clicked(self, index):
        """Handle file or directory selection.

        Args:
            index: QModelIndex of selected item
        """
        file_path = Path(self.model.filePath(index))

        # Emit signal for both files and directories
        if file_path.is_file() or file_path.is_dir():
            self.file_selected.emit(file_path)

    def _on_item_double_clicked(self, index):
        """Handle double-click to open .blend file in Blender.

        Args:
            index: QModelIndex of double-clicked item
        """
        file_path = Path(self.model.filePath(index))

        # Only open .blend files
        if not file_path.is_file() or file_path.suffix != '.blend':
            return

        try:
            system = platform.system()

            if system == 'Darwin':  # macOS
                # Use 'open -a Blender -n' to open in new instance
                subprocess.Popen(['open', '-a', 'Blender', '-n', str(file_path)])
            elif system == 'Windows':
                # Use blender executable from project controller
                if self.project.is_open and self.project.blender_path:
                    subprocess.Popen([str(self.project.blender_path), str(file_path)])
                else:
                    QMessageBox.warning(
                        self,
                        TITLE_BLENDER_NOT_FOUND,
                        MSG_BLENDER_NOT_CONFIGURED
                    )
            else:  # Linux and others
                # Use blender executable from project controller
                if self.project.is_open and self.project.blender_path:
                    subprocess.Popen([str(self.project.blender_path), str(file_path)])
                else:
                    QMessageBox.warning(
                        self,
                        TITLE_BLENDER_NOT_FOUND,
                        MSG_BLENDER_NOT_CONFIGURED
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                TITLE_ERROR_OPENING_FILE,
                TMPL_FAILED_TO_OPEN_BLENDER.format(
                    file_name=file_path.name,
                    error=str(e)
                )
            )

    def eventFilter(self, obj, event):
        """Filter events to handle clicks on action icons."""
        if obj == self.tree.viewport() and event.type() == event.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                # Get the index at the click position
                pos = event.pos()
                index = self.tree.indexAt(pos)

                if index.isValid():
                    # Check if this index is selected
                    if self.tree.selectionModel().isSelected(index):
                        # Get the visual rect for this index
                        visual_rect = self.tree.visualRect(index)

                        # Create option for delegate
                        option = QStyleOptionViewItem()
                        option.rect = visual_rect

                        # Check for trash icon click
                        trash_rect = self.delegate.get_trash_icon_rect(option)
                        if trash_rect.contains(pos):
                            self._delete_selected()
                            return True  # Event handled

                        # Check for find references icon click
                        find_rect = self.delegate.get_find_icon_rect(option)
                        if find_rect.contains(pos):
                            self._find_references()
                            return True  # Event handled

        return super().eventFilter(obj, event)

    def _delete_selected(self):
        """Delete the currently selected file or directory."""
        selected_path = self.get_selected_path()
        if not selected_path:
            return

        # Show confirmation dialog
        if selected_path.is_dir():
            message = TMPL_CONFIRM_DELETE_DIR.format(dir_path=str(selected_path))
        else:
            message = TMPL_CONFIRM_DELETE_FILE.format(file_path=str(selected_path))

        reply = QMessageBox.question(
            self,
            TITLE_CONFIRM_DELETION,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Perform deletion
        try:
            if selected_path.is_dir():
                shutil.rmtree(selected_path)
            else:
                selected_path.unlink()

            QMessageBox.information(
                self,
                TITLE_SUCCESS,
                TMPL_DELETE_SUCCESS.format(path=str(selected_path))
            )

            # Clear selection
            self.tree.clearSelection()

        except Exception as e:
            QMessageBox.critical(
                self,
                TITLE_ERROR,
                TMPL_DELETE_FAILED.format(path=str(selected_path), error=str(e))
            )

    def _find_references(self):
        """Find references to the selected file."""
        selected_path = self.get_selected_path()
        if not selected_path or not selected_path.is_file():
            return

        # Check if file type is supported
        suffix = selected_path.suffix.lower()
        is_blend = suffix == '.blend'
        is_texture = suffix in TEXTURE_EXTENSIONS

        if not (is_blend or is_texture):
            return

        if not self.project.is_open:
            QMessageBox.warning(self, TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        # Show progress dialog
        progress_dialog = OperationProgressDialog(TITLE_FINDING_REFERENCES, self)
        progress_dialog.update_progress(0, TMPL_SCANNING_REFS.format(filename=selected_path.name))
        progress_dialog.show()

        try:
            # Run find references script
            blender_service = BlenderService(
                blender_path=self.project.blender_path,
                project_root=self.project.project_root
            )

            progress_dialog.update_progress(50, TMPL_ANALYZING_BLEND)
            result = blender_service.find_references(target_file=str(selected_path))
            progress_dialog.update_progress(100, TMPL_REFS_COMPLETE)
            progress_dialog.close()

            if not result.get("success"):
                QMessageBox.critical(
                    self,
                    TITLE_ERROR,
                    TMPL_FAILED_FIND_REFS.format(error=result.get('error', 'Unknown error'))
                )
                return

            # Format results
            file_type = result.get("file_type", "blend")
            referencing_files = result.get("referencing_files", [])
            files_scanned = result.get("files_scanned", 0)

            if not referencing_files:
                message = TMPL_NO_REFS_FOUND.format(count=files_scanned)
                QMessageBox.information(self, TITLE_FINDING_REFERENCES, message)
                return

            # Build detailed message
            message_lines = [
                TMPL_REFS_FOUND_HEADER.format(count=len(referencing_files), filename=selected_path.name),
                ""
            ]

            for ref_file in referencing_files:
                file_name = ref_file.get("file_name", "Unknown")
                message_lines.append(f"• {file_name}")

                if file_type == "texture":
                    # Texture references
                    images_count = ref_file.get("images_count", 0)
                    images = ref_file.get("images", [])
                    if images:
                        image_names = [img.get("name", "") for img in images[:3]]
                        message_lines.append(f"  Uses texture {images_count} time(s) (as {', '.join(image_names)}{'...' if images_count > 3 else ''})")
                else:
                    # .blend file references
                    linked_objects = ref_file.get("linked_objects", [])
                    linked_collections = ref_file.get("linked_collections", [])

                    if linked_objects:
                        obj_preview = ', '.join(linked_objects[:3])
                        if len(linked_objects) > 3:
                            obj_preview += "..."
                        message_lines.append(f"  Linked objects: {len(linked_objects)} ({obj_preview})")

                    if linked_collections:
                        col_preview = ', '.join(linked_collections[:3])
                        if len(linked_collections) > 3:
                            col_preview += "..."
                        message_lines.append(f"  Linked collections: {len(linked_collections)} ({col_preview})")

                message_lines.append("")

            message_lines.append(TMPL_REFS_SCANNED_FOOTER.format(count=files_scanned))

            QMessageBox.information(self, TITLE_FINDING_REFERENCES, "\n".join(message_lines))

        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                TITLE_ERROR,
                TMPL_FAILED_FIND_REFS.format(error=str(e))
            )

    def get_selected_path(self) -> Path | None:
        """Get the currently selected file or directory path.

        Returns:
            Path object or None if nothing selected
        """
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return None

        file_path = Path(self.model.filePath(indexes[0]))
        return file_path if (file_path.is_file() or file_path.is_dir()) else None

    def save_state(self):
        """Save file browser state (expanded paths and selected file)."""
        if not self.config_file or not self.project.is_open:
            return

        try:
            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Get expanded paths
            expanded_paths = []
            root_path = self.project.project_root
            if root_path:
                self._collect_expanded_paths(self.tree.rootIndex(), root_path, expanded_paths)

            # Get selected file or directory
            selected_item = None
            selected_path = self.get_selected_path()
            if selected_path and root_path:
                try:
                    # Store as relative path to project root
                    selected_item = str(selected_path.relative_to(root_path))
                except ValueError:
                    pass  # Selected item is outside project root

            # Save to config
            file_browser_state = {
                'expanded_paths': expanded_paths,
                'selected_file': selected_item  # Name kept for backward compatibility
            }
            config_data['file_browser'] = file_browser_state

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save file browser state: {e}")

    def _collect_expanded_paths(self, index: QModelIndex, root_path: Path, expanded_paths: list):
        """Recursively collect expanded paths in the tree.

        Args:
            index: Current index to check
            root_path: Project root path
            expanded_paths: List to append expanded paths to
        """
        # Check children first
        for row in range(self.model.rowCount(index)):
            child_index = self.model.index(row, 0, index)
            if child_index.isValid():
                # Check if this child is expanded
                if self.tree.isExpanded(child_index):
                    file_path = Path(self.model.filePath(child_index))
                    if file_path.is_dir():
                        try:
                            # Store as relative path to project root
                            rel_path = str(file_path.relative_to(root_path))
                            expanded_paths.append(rel_path)
                        except ValueError:
                            pass  # Path is outside project root

                # Recursively check this child's children
                self._collect_expanded_paths(child_index, root_path, expanded_paths)

    def restore_state(self):
        """Restore file browser state (expanded paths and selected file)."""
        if not self.config_file or not self.config_file.exists() or not self.project.is_open:
            return

        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            file_browser_state = config_data.get('file_browser', {})
            root_path = self.project.project_root
            if not root_path:
                return

            # Store restoration data to be applied when directories are loaded
            self.restore_data = {
                'root_path': root_path,
                'expanded_paths': file_browser_state.get('expanded_paths', []),
                'selected_file': file_browser_state.get('selected_file'),
                'pending_expansions': set(file_browser_state.get('expanded_paths', []))
            }
            self.pending_restore_state = True

            # Try to expand paths that are already loaded
            self._apply_pending_expansions()

        except Exception as e:
            print(f"Warning: Could not restore file browser state: {e}")

    def _on_directory_loaded(self, path: str):
        """Handle directory loaded event from the file system model.

        Args:
            path: Path of the directory that was loaded
        """
        if self.pending_restore_state and self.restore_data:
            self._apply_pending_expansions()

    def _apply_pending_expansions(self):
        """Apply pending path expansions as directories become available."""
        if not self.restore_data:
            return

        root_path = self.restore_data['root_path']
        pending = self.restore_data['pending_expansions']

        # Sort paths by depth (shallowest first) to ensure parent dirs are expanded before children
        sorted_paths = sorted(pending, key=lambda p: p.count('/'))

        # Try to expand all pending paths
        expanded_any = False
        for rel_path in sorted_paths:
            full_path = root_path / rel_path
            if full_path.exists() and full_path.is_dir():
                index = self.model.index(str(full_path))
                if index.isValid():
                    self.tree.expand(index)
                    pending.discard(rel_path)
                    expanded_any = True

        # If no more pending expansions, restore selected file or directory
        if not pending and self.restore_data.get('selected_file'):
            selected_item = self.restore_data['selected_file']
            full_path = root_path / selected_item
            if full_path.exists() and (full_path.is_file() or full_path.is_dir()):
                index = self.model.index(str(full_path))
                if index.isValid():
                    self.tree.setCurrentIndex(index)
                    self.tree.scrollTo(index)
                    # Emit signal to update operations panel
                    self.file_selected.emit(full_path)

            # Clear restoration data
            self.restore_data = None
            self.pending_restore_state = False
