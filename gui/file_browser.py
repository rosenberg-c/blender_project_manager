"""File browser widget with tree view."""

import json
import subprocess
import platform
import shutil
import re
from pathlib import Path
from send2trash import send2trash

from PySide6.QtCore import Qt, Signal, QModelIndex, QRect, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QToolTip
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeView, QFileSystemModel, QMessageBox, QStyledItemDelegate, QStyle, QStyleOptionViewItem
)
from PySide6.QtCore import QSortFilterProxyModel

from controllers.project_controller import ProjectController
from services.blender_service import BlenderService
from gui.progress_dialog import OperationProgressDialog
from gui.file_links_dialog import FileLinksDialog
from gui.file_references_dialog import FileReferencesDialog
from blender_lib.constants import TEXTURE_EXTENSIONS
from gui.ui_strings import (
    TITLE_BLENDER_NOT_FOUND, TITLE_ERROR_OPENING_FILE,
    TITLE_CONFIRM_DELETION, TITLE_SUCCESS, TITLE_ERROR,
    TITLE_NO_PROJECT, TITLE_FINDING_REFERENCES, TITLE_LINKED_FILES, TITLE_LOADING_LINKS,
    MSG_BLENDER_NOT_CONFIGURED, MSG_OPEN_PROJECT_FIRST,
    TMPL_FAILED_TO_OPEN_BLENDER,
    TMPL_CONFIRM_DELETE_FILE, TMPL_CONFIRM_DELETE_DIR,
    TMPL_DELETE_SUCCESS, TMPL_DELETE_FAILED,
    TMPL_SCANNING_REFS, TMPL_ANALYZING_BLEND, TMPL_REFS_COMPLETE,
    TMPL_NO_REFS_FOUND, TMPL_REFS_FOUND_HEADER, TMPL_REFS_SCANNED_FOOTER,
    TMPL_FAILED_FIND_REFS,
    TOOLTIP_MOVE_TO_TRASH, TOOLTIP_FIND_REFERENCES, TOOLTIP_SHOW_LINKED_FILES, TOOLTIP_PIN_ITEM,
    MSG_MOVED_TO_TRASH_NOTICE, TMPL_MOVED_TO_TRASH, TMPL_FAILED_MOVE_TO_TRASH,
    MSG_ANALYZING_LINKS, MSG_COMPLETE, TMPL_LOADING_BLEND,
    TMPL_FAILED_LIST_LINKS, TMPL_NO_LINKED_FILES
)


class FileSystemProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering file system based on search text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_text = ""
        self.file_system_model = None
        self.project_root = None

    def set_project_root(self, root_path: Path):
        """Set the project root path to enforce boundaries.

        Args:
            root_path: Project root directory path
        """
        self.project_root = root_path

    def set_search_text(self, text: str):
        """Set the search filter text.

        Args:
            text: Search text to filter by
        """
        # Strip leading/trailing whitespace to prevent issues with space at start
        self.search_text = text.strip().lower()
        self.invalidate()

    def _is_within_project_root(self, file_path: Path) -> bool:
        """Check if a path is within the project root.

        Args:
            file_path: Path to check

        Returns:
            True if path is within project root or no project root is set
        """
        if not self.project_root:
            return True

        try:
            # Check if file_path is relative to project_root
            file_path.relative_to(self.project_root)
            return True
        except ValueError:
            # Path is not relative to project_root
            return False

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Determine if a row should be shown based on search filter.

        Args:
            source_row: Row number in source model
            source_parent: Parent index in source model

        Returns:
            True if row should be shown, False otherwise
        """
        if not self.search_text:
            # No filter - show everything
            return True

        # Get the source model
        source_model = self.sourceModel()
        if not source_model:
            return True

        # Get the index for this row
        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return True

        # Get the file path
        file_path = Path(source_model.filePath(index))

        # CRITICAL: Never show anything outside the project path
        if not self._is_within_project_root(file_path):
            return False

        # Check if this item matches
        if self.search_text in file_path.name.lower():
            return True

        # If this is a directory, check if any children match
        if file_path.is_dir():
            return self._has_matching_children(index, source_model)

        return False

    def _has_matching_children(self, parent_index: QModelIndex, source_model) -> bool:
        """Recursively check if any children match the search.

        Args:
            parent_index: Parent index to check
            source_model: Source file system model

        Returns:
            True if any descendant matches the search
        """
        # Get the directory path and check directly on filesystem
        # QFileSystemModel loads asynchronously, so we can't rely on rowCount
        parent_path = Path(source_model.filePath(parent_index))

        if not parent_path.is_dir():
            return False

        # CRITICAL: Ensure parent_path is within project root before searching
        if not self._is_within_project_root(parent_path):
            return False

        try:
            # Check all items in the directory recursively
            # IMPORTANT: Only search within project boundaries
            for item in parent_path.rglob('*'):
                # CRITICAL: Validate each item is within project root
                if not self._is_within_project_root(item):
                    continue

                if self.search_text in item.name.lower():
                    return True
        except (PermissionError, OSError):
            # If we can't access the directory, fall back to Qt model
            pass

        # Fallback to Qt model (for already loaded directories)
        for row in range(source_model.rowCount(parent_index)):
            child_index = source_model.index(row, 0, parent_index)
            if not child_index.isValid():
                continue

            file_path = Path(source_model.filePath(child_index))

            # CRITICAL: Never check paths outside project root
            if not self._is_within_project_root(file_path):
                continue

            # Check if child matches
            if self.search_text in file_path.name.lower():
                return True

            # If child is a directory, check its children
            if file_path.is_dir():
                if self._has_matching_children(child_index, source_model):
                    return True

        return False


class FileItemDelegate(QStyledItemDelegate):
    """Custom delegate to draw action icons on selected rows."""

    def __init__(self, parent=None, proxy_model=None, file_system_model=None, browser_widget=None):
        super().__init__(parent)
        self.icon_size = 16
        self.icon_margin = 4
        self.icon_spacing = 4
        self.proxy_model = proxy_model
        self.file_system_model = file_system_model
        self.browser_widget = browser_widget

    def paint(self, painter, option, index):
        """Paint the item with action icons if selected."""
        super().paint(painter, option, index)

        if self.proxy_model and self.file_system_model:
            source_index = self.proxy_model.mapToSource(index)
            file_path = Path(self.file_system_model.filePath(source_index))
        else:
            model = index.model()
            file_path = Path(model.filePath(index))

        style = option.widget.style()

        x_offset = option.rect.right() - self.icon_margin
        y_pos = option.rect.top() + (option.rect.height() - self.icon_size) // 2

        if self.browser_widget:
            from PySide6.QtWidgets import QStyleOptionButton
            check_option = QStyleOptionButton()
            check_option.rect = QRect(
                x_offset - self.icon_size,
                y_pos,
                self.icon_size,
                self.icon_size
            )
            check_option.state = QStyle.StateFlag.State_Enabled

            if file_path in self.browser_widget.pinned_paths:
                check_option.state |= QStyle.StateFlag.State_On
            else:
                check_option.state |= QStyle.StateFlag.State_Off

            style.drawControl(
                QStyle.ControlElement.CE_CheckBox,
                check_option,
                painter
            )
            x_offset -= (self.icon_size + self.icon_spacing)

        if option.state & QStyle.StateFlag.State_Selected:

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
                x_offset -= (self.icon_size + self.icon_spacing)

            # Draw show links icon (only for .blend files)
            if file_path.is_file() and file_path.suffix.lower() == '.blend':
                links_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
                links_rect = QRect(
                    x_offset - self.icon_size,
                    y_pos,
                    self.icon_size,
                    self.icon_size
                )
                links_icon.paint(painter, links_rect)

    def _is_supported_file(self, file_path):
        """Check if file is a .blend or texture file."""
        suffix = file_path.suffix.lower()
        return suffix == '.blend' or suffix in TEXTURE_EXTENSIONS

    def get_trash_icon_rect(self, option):
        """Get the rectangle where the trash icon is drawn."""
        x_offset = option.rect.right() - self.icon_margin - (self.icon_size + self.icon_spacing)
        return QRect(
            x_offset - self.icon_size,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )

    def get_find_icon_rect(self, option):
        """Get the rectangle where the find references icon is drawn."""
        x_offset = option.rect.right() - self.icon_margin - (self.icon_size + self.icon_spacing) * 2
        return QRect(
            x_offset - self.icon_size,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )

    def get_links_icon_rect(self, option):
        """Get the rectangle where the show links icon is drawn."""
        x_offset = option.rect.right() - self.icon_margin - (self.icon_size + self.icon_spacing) * 3
        return QRect(
            x_offset - self.icon_size,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )

    def get_pin_checkbox_rect(self, option):
        """Get the rectangle where the pin checkbox is drawn."""
        x_offset = option.rect.right() - self.icon_margin
        return QRect(
            x_offset - self.icon_size,
            option.rect.top() + (option.rect.height() - self.icon_size) // 2,
            self.icon_size,
            self.icon_size
        )

    def helpEvent(self, event, view, option, index):
        """Show tooltip when hovering over action icons.

        Args:
            event: Help event
            view: View widget
            option: Style option
            index: Model index

        Returns:
            True if event was handled, False otherwise
        """
        if event.type() == event.Type.ToolTip:
            visual_rect = view.visualRect(index)
            style_option = QStyleOptionViewItem()
            style_option.rect = visual_rect
            pos = event.pos()

            pin_rect = self.get_pin_checkbox_rect(style_option)
            if pin_rect.contains(pos):
                QToolTip.showText(event.globalPos(), TOOLTIP_PIN_ITEM, view)
                return True

            if view.selectionModel().isSelected(index):
                trash_rect = self.get_trash_icon_rect(style_option)
                if trash_rect.contains(pos):
                    QToolTip.showText(event.globalPos(), TOOLTIP_MOVE_TO_TRASH, view)
                    return True

                # Get file path (needed for multiple checks)
                if self.proxy_model and self.file_system_model:
                    source_index = self.proxy_model.mapToSource(index)
                    file_path = Path(self.file_system_model.filePath(source_index))
                else:
                    model = index.model()
                    file_path = Path(model.filePath(index))

                # Check if hovering over find references icon
                find_rect = self.get_find_icon_rect(style_option)
                if find_rect.contains(pos):
                    if file_path.is_file() and self._is_supported_file(file_path):
                        QToolTip.showText(event.globalPos(), TOOLTIP_FIND_REFERENCES, view)
                        return True

                # Check if hovering over show links icon
                links_rect = self.get_links_icon_rect(style_option)
                if links_rect.contains(pos):
                    if file_path.is_file() and file_path.suffix.lower() == '.blend':
                        QToolTip.showText(event.globalPos(), TOOLTIP_SHOW_LINKED_FILES, view)
                        return True

        return super().helpEvent(event, view, option, index)


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
        self.pinned_paths = set()

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
        self.search_box.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_box)

        self.clear_search_btn = QPushButton("Clear")
        self.clear_search_btn.clicked.connect(self._clear_search)
        self.clear_search_btn.setEnabled(False)
        search_layout.addWidget(self.clear_search_btn)

        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(self.collapse_all)
        search_layout.addWidget(self.collapse_all_btn)

        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(self.expand_all)
        search_layout.addWidget(self.expand_all_btn)

        layout.addLayout(search_layout)

        # Tree view with file system model
        self.tree = QTreeView()
        self.file_system_model = QFileSystemModel()

        # Set file filters
        self.file_system_model.setNameFilters(['*.blend', '*.png', '*.jpg', '*.jpeg', '*.hdr', '*.exr'])
        self.file_system_model.setNameFilterDisables(False)  # Hide non-matching files

        # Connect to directoryLoaded signal for state restoration
        self.file_system_model.directoryLoaded.connect(self._on_directory_loaded)

        # Create proxy model for filtering
        self.proxy_model = FileSystemProxyModel(self)
        self.proxy_model.setSourceModel(self.file_system_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.tree.setModel(self.proxy_model)
        self.tree.setSelectionMode(QTreeView.SingleSelection)

        # Enable mouse tracking for hover tooltips
        self.tree.setMouseTracking(True)
        self.tree.viewport().setMouseTracking(True)

        self.delegate = FileItemDelegate(self.tree, self.proxy_model, self.file_system_model, self)
        self.tree.setItemDelegate(self.delegate)

        # Hide size, type, and date columns for simpler view
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)

        # Center the header text both horizontally and vertically
        header = self.tree.header()
        header.setDefaultAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        header.setFixedHeight(24)  # Make header thinner

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
        # CRITICAL: Set project root on proxy model to enforce boundaries
        self.proxy_model.set_project_root(path)

        root_index = self.file_system_model.setRootPath(str(path))
        proxy_root_index = self.proxy_model.mapFromSource(root_index)
        self.tree.setRootIndex(proxy_root_index)
        self.tree.expandToDepth(1)  # Expand first level

    def collapse_all(self):
        """Collapse all directories in the tree, except pinned items."""
        self.tree.collapseAll()
        self._expand_pinned_paths()

    def expand_all(self):
        """Expand all directories in the tree."""
        self.tree.expandAll()

    def _expand_pinned_paths(self):
        """Expand all pinned paths and their ancestors."""
        if not self.project.is_open:
            return

        root_path = self.project.project_root
        if not root_path:
            return

        for pinned_path in self.pinned_paths:
            ancestors = [pinned_path]
            current = pinned_path.parent
            while current != root_path and current > root_path:
                ancestors.append(current)
                current = current.parent

            for path in reversed(ancestors):
                source_index = self.file_system_model.index(str(path))
                if source_index.isValid():
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    if proxy_index.isValid():
                        self.tree.expand(proxy_index)

    def _on_search_text_changed(self, text: str):
        """Handle search text changes to filter matching files.

        Args:
            text: Search text entered by user
        """
        # CRITICAL: Ensure project root is set before filtering
        if self.project.is_open and self.project.project_root:
            self.proxy_model.set_project_root(self.project.project_root)

        self.proxy_model.set_search_text(text)
        self.clear_search_btn.setEnabled(bool(text))

        if text:
            self.tree.expandAll()
        else:
            # When clearing search, ensure we maintain the project root
            if self.project.is_open and self.project.project_root:
                # Re-set the root index to ensure we stay within project directory
                root_index = self.file_system_model.index(str(self.project.project_root))
                proxy_root_index = self.proxy_model.mapFromSource(root_index)
                self.tree.setRootIndex(proxy_root_index)

            self.tree.collapseAll()
            self.tree.expandToDepth(1)
            self._expand_pinned_paths()

    def _clear_search(self):
        """Clear the search box."""
        self.search_box.clear()

    def _on_item_clicked(self, index):
        """Handle file or directory selection.

        Args:
            index: QModelIndex of selected item
        """
        # Map from proxy to source model
        source_index = self.proxy_model.mapToSource(index)
        file_path = Path(self.file_system_model.filePath(source_index))

        # Emit signal for both files and directories
        if file_path.is_file() or file_path.is_dir():
            self.file_selected.emit(file_path)

    def _on_item_double_clicked(self, index):
        """Handle double-click to open .blend file in Blender.

        Args:
            index: QModelIndex of double-clicked item
        """
        # Map from proxy to source model
        source_index = self.proxy_model.mapToSource(index)
        file_path = Path(self.file_system_model.filePath(source_index))

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
                pos = event.pos()
                index = self.tree.indexAt(pos)

                if index.isValid():
                    visual_rect = self.tree.visualRect(index)
                    option = QStyleOptionViewItem()
                    option.rect = visual_rect

                    pin_rect = self.delegate.get_pin_checkbox_rect(option)
                    if pin_rect.contains(pos):
                        self._toggle_pin(index)
                        return True

                    if self.tree.selectionModel().isSelected(index):
                        trash_rect = self.delegate.get_trash_icon_rect(option)
                        if trash_rect.contains(pos):
                            self._delete_selected()
                            return True

                        find_rect = self.delegate.get_find_icon_rect(option)
                        if find_rect.contains(pos):
                            self._find_references()
                            return True

                        links_rect = self.delegate.get_links_icon_rect(option)
                        if links_rect.contains(pos):
                            self._show_linked_files()
                            return True

        return super().eventFilter(obj, event)

    def _toggle_pin(self, index):
        """Toggle pin status for the item at the given index."""
        source_index = self.proxy_model.mapToSource(index)
        file_path = Path(self.file_system_model.filePath(source_index))

        if file_path in self.pinned_paths:
            self.pinned_paths.remove(file_path)
        else:
            self.pinned_paths.add(file_path)

        self.tree.viewport().update()
        self.save_state()

    def _delete_selected(self):
        """Move the currently selected file or directory to trash."""
        selected_path = self.get_selected_path()
        if not selected_path:
            return

        # Show confirmation dialog
        if selected_path.is_dir():
            message = TMPL_CONFIRM_DELETE_DIR.format(dir_path=str(selected_path))
        else:
            message = TMPL_CONFIRM_DELETE_FILE.format(file_path=str(selected_path))

        # Update message to indicate it will be moved to trash
        message += "\n\nIt will be moved to the trash/recycle bin."

        reply = QMessageBox.question(
            self,
            TITLE_CONFIRM_DELETION,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Move to trash
        try:
            send2trash(str(selected_path))

            QMessageBox.information(
                self,
                TITLE_SUCCESS,
                f"'{selected_path.name}' has been moved to trash."
            )

            # Clear selection
            self.tree.clearSelection()

        except Exception as e:
            QMessageBox.critical(
                self,
                TITLE_ERROR,
                f"Failed to move '{selected_path.name}' to trash: {str(e)}"
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

            # Show results in table dialog
            dialog = FileReferencesDialog(
                filename=selected_path.name,
                file_type=file_type,
                referencing_files=referencing_files,
                files_scanned=files_scanned,
                parent=self
            )
            dialog.exec()

        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                TITLE_ERROR,
                TMPL_FAILED_FIND_REFS.format(error=str(e))
            )

    def _show_linked_files(self):
        """Show all files linked by the selected .blend file."""
        selected_path = self.get_selected_path()
        if not selected_path or not selected_path.is_file():
            return

        # Only works for .blend files
        if selected_path.suffix.lower() != '.blend':
            return

        if not self.project.is_open:
            QMessageBox.warning(self, TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
            return

        # Show progress dialog
        progress_dialog = OperationProgressDialog(TITLE_LOADING_LINKS, self)
        progress_dialog.update_progress(0, f"Loading {selected_path.name}...")
        progress_dialog.show()

        try:
            # Run list links script
            blender_service = BlenderService(
                blender_path=self.project.blender_path,
                project_root=self.project.project_root
            )

            progress_dialog.update_progress(50, "Analyzing linked files...")
            result = blender_service.list_linked_files(blend_file=str(selected_path))
            progress_dialog.update_progress(100, "Complete")
            progress_dialog.close()

            if not result.get("success"):
                QMessageBox.critical(
                    self,
                    TITLE_ERROR,
                    f"Failed to list linked files: {result.get('error', 'Unknown error')}"
                )
                return

            linked_libraries = result.get("linked_libraries", [])
            linked_textures = result.get("linked_textures", [])
            linked_materials = result.get("linked_materials", [])
            total_libraries = result.get("total_libraries", 0)
            total_textures = result.get("total_textures", 0)
            total_materials = result.get("total_materials", 0)

            if total_libraries == 0 and total_textures == 0 and total_materials == 0:
                message = f"'{selected_path.name}' has no linked libraries, textures, or materials."
                QMessageBox.information(self, TITLE_LINKED_FILES, message)
                return

            dialog = FileLinksDialog(
                filename=selected_path.name,
                linked_libraries=linked_libraries,
                linked_textures=linked_textures,
                linked_materials=linked_materials,
                parent=self
            )
            dialog.exec()

        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self,
                TITLE_ERROR,
                f"Failed to list linked files: {str(e)}"
            )

    def get_selected_path(self) -> Path | None:
        """Get the currently selected file or directory path.

        Returns:
            Path object or None if nothing selected
        """
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return None

        # Map from proxy to source model
        source_index = self.proxy_model.mapToSource(indexes[0])
        file_path = Path(self.file_system_model.filePath(source_index))
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

            pinned_paths = []
            for path in self.pinned_paths:
                try:
                    rel_path = str(path.relative_to(root_path))
                    pinned_paths.append(rel_path)
                except (ValueError, AttributeError):
                    pass

            file_browser_state = {
                'expanded_paths': expanded_paths,
                'selected_file': selected_item,
                'pinned_paths': pinned_paths
            }
            config_data['file_browser'] = file_browser_state

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save file browser state: {e}")

    def _collect_expanded_paths(self, index: QModelIndex, root_path: Path, expanded_paths: list):
        """Recursively collect expanded paths in the tree.

        Args:
            index: Current index to check (proxy model index)
            root_path: Project root path
            expanded_paths: List to append expanded paths to
        """
        # Check children first
        for row in range(self.proxy_model.rowCount(index)):
            child_index = self.proxy_model.index(row, 0, index)
            if child_index.isValid():
                # Check if this child is expanded
                if self.tree.isExpanded(child_index):
                    # Map to source to get file path
                    source_index = self.proxy_model.mapToSource(child_index)
                    file_path = Path(self.file_system_model.filePath(source_index))
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

            self.pinned_paths = set()
            for rel_path in file_browser_state.get('pinned_paths', []):
                abs_path = root_path / rel_path
                if abs_path.exists():
                    self.pinned_paths.add(abs_path)

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
                source_index = self.file_system_model.index(str(full_path))
                if source_index.isValid():
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    if proxy_index.isValid():
                        self.tree.expand(proxy_index)
                        pending.discard(rel_path)
                        expanded_any = True

        # If no more pending expansions, restore selected file or directory
        if not pending and self.restore_data.get('selected_file'):
            selected_item = self.restore_data['selected_file']
            full_path = root_path / selected_item
            if full_path.exists() and (full_path.is_file() or full_path.is_dir()):
                source_index = self.file_system_model.index(str(full_path))
                if source_index.isValid():
                    proxy_index = self.proxy_model.mapFromSource(source_index)
                    if proxy_index.isValid():
                        self.tree.setCurrentIndex(proxy_index)
                        self.tree.scrollTo(proxy_index)
                        # Emit signal to update operations panel
                        self.file_selected.emit(full_path)

            # Clear restoration data
            self.restore_data = None
            self.pending_restore_state = False
