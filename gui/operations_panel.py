"""Operations panel for file operations."""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget
)

from controllers.file_operations_controller import FileOperationsController
from gui.operations import (
    MoveRenameTab,
    RenameObjectsTab,
    LinkObjectsTab,
    UtilitiesTab
)
from gui.theme import Theme
from gui.ui_strings import LABEL_NO_FILE_SELECTED


class OperationsPanelWidget(QWidget):
    """Panel for configuring and executing file operations."""

    def __init__(self, controller: FileOperationsController, config_file: Path = None, parent=None):
        """Initialize operations panel.

        Args:
            controller: File operations controller
            config_file: Path to config file for state persistence
            parent: Parent widget
        """
        super().__init__(parent)
        self.controller = controller
        self.config_file = config_file
        self.current_file: Path | None = None
        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)

        title = QLabel("<h2>File Operations</h2>")
        layout.addWidget(title)

        # Current file display
        file_label = QLabel("<b>Selected File:</b>")
        layout.addWidget(file_label)

        self.file_display = QLabel(LABEL_NO_FILE_SELECTED)
        self.file_display.setWordWrap(True)
        self.file_display.setStyleSheet(Theme.get_file_display_style())
        layout.addWidget(self.file_display)

        # Separator
        layout.addSpacing(10)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tab instances
        self.move_tab = MoveRenameTab(self.controller, self)
        self.rename_tab = RenameObjectsTab(self.controller, self, self.config_file)
        self.link_tab = LinkObjectsTab(self.controller, self, self.config_file)
        self.utilities_tab = UtilitiesTab(self.controller, self)

        # Add tabs to tab widget
        self.tabs.addTab(self.move_tab, "Move/Rename")
        self.tabs.addTab(self.rename_tab, "Rename Objects")
        self.tabs.addTab(self.link_tab, "Link Objects")
        self.tabs.addTab(self.utilities_tab, "Utilities")

    def set_file(self, file_path: Path):
        """Set the currently selected file or directory.

        Args:
            file_path: Path to the selected file or directory
        """
        self.current_file = file_path

        # Update main file display
        if file_path.is_dir():
            self.file_display.setText(f"<b>{file_path.name}/</b><br><small>{str(file_path)}</small>")
        else:
            self.file_display.setText(f"<b>{file_path.name}</b><br><small>{str(file_path)}</small>")

        # Notify all tabs
        self.move_tab.set_file(file_path)
        self.rename_tab.set_file(file_path)
        self.link_tab.set_file(file_path)
        self.utilities_tab.set_file(file_path)

    def apply_pending_restorations(self):
        """Apply any pending restorations after project is opened.

        This is called by the main window after a project is opened
        to restore any state that couldn't be restored during initialization
        (e.g., locked file in link tab).
        """
        # Only link tab has pending restorations
        self.link_tab.apply_pending_restorations()
