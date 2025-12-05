"""Main application window."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QStatusBar
)

from controllers.project_controller import ProjectController
from controllers.file_operations_controller import FileOperationsController
from gui.file_browser import FileBrowserWidget
from gui.operations_panel import OperationsPanelWidget


class MainWindow(QMainWindow):
    """Main application window for Blender Project Manager."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        self.setWindowTitle("Blender Project Manager")
        self.resize(1400, 800)

        # Initialize controllers
        self.project_controller = ProjectController()
        self.file_ops_controller = FileOperationsController(self.project_controller)

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

        # Show project selection on startup
        self.select_project()

    def setup_ui(self):
        """Create UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create horizontal splitter for file browser and operations panel
        splitter = QSplitter(Qt.Horizontal)

        # Left: File browser
        self.file_browser = FileBrowserWidget(self.project_controller)
        self.file_browser.file_selected.connect(self._on_file_selected)
        splitter.addWidget(self.file_browser)

        # Right: Operations panel
        self.operations_panel = OperationsPanelWidget(self.file_ops_controller)
        splitter.addWidget(self.operations_panel)

        # Set initial sizes (2:1 ratio)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def setup_menu(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = file_menu.addAction("&Open Project...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_project)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("&Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self.show_about)

    def setup_statusbar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def select_project(self):
        """Show project selection dialog."""
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Blender Project Root Directory",
            str(Path.home())
        )

        if project_dir:
            self.open_project(Path(project_dir))

    def open_project(self, project_root: Path):
        """Open a Blender project.

        Args:
            project_root: Root directory of the project
        """
        success = self.project_controller.open_project(project_root)

        if success:
            # Update UI
            self.file_browser.set_root(project_root)
            self.status_bar.showMessage(f"Project: {project_root}")
            self.setWindowTitle(f"Blender Project Manager - {project_root.name}")

            # Show project info
            info = self.project_controller.get_project_info()
            QMessageBox.information(
                self,
                "Project Opened",
                f"Project: {project_root.name}\n"
                f"Root: {project_root}\n"
                f".blend files found: {info.get('blend_files_count', 0)}"
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open project at:\n{project_root}\n\n"
                "Please check that Blender is installed at the expected location."
            )

    def _on_file_selected(self, file_path: Path):
        """Handle file selection from browser.

        Args:
            file_path: Path to selected file
        """
        self.operations_panel.set_file(file_path)
        self.status_bar.showMessage(f"Selected: {file_path.name}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Blender Project Manager",
            "<h2>Blender Project Manager</h2>"
            "<p>Version 0.1.0 (MVP)</p>"
            "<p>A desktop application for managing Blender projects with "
            "automatic reference tracking and updating.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Visual file browser</li>"
            "<li>Move/rename files with automatic reference updates</li>"
            "<li>Preview changes before applying</li>"
            "<li>Progress tracking</li>"
            "</ul>"
            "<p>Built with Python and PySide6 (Qt for Python)</p>"
        )

    def closeEvent(self, event):
        """Handle window close event.

        Args:
            event: QCloseEvent
        """
        reply = QMessageBox.question(
            self,
            "Quit",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.project_controller.is_open:
                self.project_controller.close_project()
            event.accept()
        else:
            event.ignore()
