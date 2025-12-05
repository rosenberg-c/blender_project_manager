"""File browser widget with tree view."""

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QTreeView, QFileSystemModel
)

from controllers.project_controller import ProjectController


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

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files...")
        layout.addWidget(self.search_box)

        # Tree view with file system model
        self.tree = QTreeView()
        self.model = QFileSystemModel()

        # Set file filters
        self.model.setNameFilters(['*.blend', '*.png', '*.jpg', '*.jpeg', '*.hdr', '*.exr'])
        self.model.setNameFilterDisables(False)  # Hide non-matching files

        self.tree.setModel(self.model)
        self.tree.setSelectionMode(QTreeView.SingleSelection)

        # Hide size, type, and date columns for simpler view
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)

        # Enable sorting
        self.tree.setSortingEnabled(True)

        # Connect selection signal
        self.tree.clicked.connect(self._on_item_clicked)

        layout.addWidget(self.tree)

    def set_root(self, path: Path):
        """Set the root directory for the file browser.

        Args:
            path: Root directory path
        """
        root_index = self.model.setRootPath(str(path))
        self.tree.setRootIndex(root_index)
        self.tree.expandToDepth(1)  # Expand first level

    def _on_item_clicked(self, index):
        """Handle file selection.

        Args:
            index: QModelIndex of selected item
        """
        file_path = Path(self.model.filePath(index))

        if file_path.is_file():
            self.file_selected.emit(file_path)

    def get_selected_path(self) -> Path | None:
        """Get the currently selected file path.

        Returns:
            Path object or None if nothing selected
        """
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return None

        file_path = Path(self.model.filePath(indexes[0]))
        return file_path if file_path.is_file() else None

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

            # Get selected file
            selected_file = None
            selected_path = self.get_selected_path()
            if selected_path and root_path:
                try:
                    # Store as relative path to project root
                    selected_file = str(selected_path.relative_to(root_path))
                except ValueError:
                    pass  # Selected file is outside project root

            # Save to config
            file_browser_state = {
                'expanded_paths': expanded_paths,
                'selected_file': selected_file
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
        if self.tree.isExpanded(index):
            file_path = Path(self.model.filePath(index))
            if file_path.is_dir() and file_path != root_path:
                try:
                    # Store as relative path to project root
                    rel_path = str(file_path.relative_to(root_path))
                    expanded_paths.append(rel_path)
                except ValueError:
                    pass  # Path is outside project root

            # Check children
            for row in range(self.model.rowCount(index)):
                child_index = self.model.index(row, 0, index)
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

            # Restore expanded paths
            expanded_paths = file_browser_state.get('expanded_paths', [])
            for rel_path in expanded_paths:
                full_path = root_path / rel_path
                if full_path.exists() and full_path.is_dir():
                    index = self.model.index(str(full_path))
                    self.tree.expand(index)

            # Restore selected file
            selected_file = file_browser_state.get('selected_file')
            if selected_file:
                full_path = root_path / selected_file
                if full_path.exists() and full_path.is_file():
                    index = self.model.index(str(full_path))
                    self.tree.setCurrentIndex(index)
                    self.tree.scrollTo(index)
                    # Emit signal to update operations panel
                    self.file_selected.emit(full_path)

        except Exception as e:
            print(f"Warning: Could not restore file browser state: {e}")
