"""File browser widget with tree view."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit,
    QTreeView, QFileSystemModel
)

from controllers.project_controller import ProjectController


class FileBrowserWidget(QWidget):
    """File browser with tree view and search."""

    file_selected = Signal(Path)

    def __init__(self, project_controller: ProjectController, parent=None):
        """Initialize file browser.

        Args:
            project_controller: The project controller
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project_controller

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
