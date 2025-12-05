"""Main application window."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QStatusBar,
    QLabel, QPushButton, QLineEdit, QFrame
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

        # Config file for storing last project path
        self.config_dir = Path.home() / '.blender_project_manager'
        self.config_file = self.config_dir / 'last_project.json'

        # Initialize controllers
        self.project_controller = ProjectController()
        self.file_ops_controller = FileOperationsController(self.project_controller)

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

        # Try to load last project automatically
        self.load_last_project()

    def setup_ui(self):
        """Create UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Add project selector bar at top
        project_bar = self.create_project_selector_bar()
        main_layout.addWidget(project_bar)

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

    def create_project_selector_bar(self) -> QWidget:
        """Create the project selector bar at the top of the window."""
        bar = QFrame()
        bar.setFrameShape(QFrame.StyledPanel)
        bar.setStyleSheet(
            "QFrame { background-color: #f5f5f5; border: 1px solid #cccccc; "
            "border-radius: 3px; padding: 2px; }"
        )
        bar.setMaximumHeight(35)  # Limit height to single row

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # Label
        label = QLabel("<b>Project:</b>")
        label.setMaximumHeight(25)
        layout.addWidget(label)

        # Project path display (read-only line edit)
        self.project_path_display = QLineEdit()
        self.project_path_display.setReadOnly(True)
        self.project_path_display.setPlaceholderText("No project selected")
        self.project_path_display.setMaximumHeight(25)
        self.project_path_display.setStyleSheet(
            "QLineEdit { background-color: white; color: #333333; "
            "padding: 3px 5px; border: 1px solid #cccccc; border-radius: 2px; }"
        )
        layout.addWidget(self.project_path_display, stretch=1)

        # Select/Change button
        self.select_project_btn = QPushButton("Select Project...")
        self.select_project_btn.clicked.connect(self.select_project)
        self.select_project_btn.setMaximumHeight(25)
        self.select_project_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 3px 12px; border-radius: 2px; font-size: 12px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        layout.addWidget(self.select_project_btn)

        return bar

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
        # Start from current project or home
        start_dir = str(Path.home())
        if self.project_controller.is_open and self.project_controller.project_root:
            start_dir = str(self.project_controller.project_root.parent)

        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Blender Project Root Directory",
            start_dir
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
            self.project_path_display.setText(str(project_root))
            self.file_browser.set_root(project_root)
            self.status_bar.showMessage(f"Project: {project_root}")
            self.setWindowTitle(f"Blender Project Manager - {project_root.name}")

            # Save as last project
            self.save_last_project(project_root)

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

    def save_last_project(self, project_root: Path):
        """Save the last opened project path to config file.

        Args:
            project_root: Project root path to save
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            config_data = {"last_project": str(project_root)}
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save last project: {e}")

    def load_last_project(self):
        """Load and open the last used project if it exists."""
        try:
            if not self.config_file.exists():
                return

            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            last_project = config_data.get('last_project')
            if last_project:
                last_project_path = Path(last_project)
                if last_project_path.exists() and last_project_path.is_dir():
                    # Open silently without showing info dialog
                    self._open_project_silent(last_project_path)
                else:
                    self.status_bar.showMessage("Last project no longer exists. Please select a project.")

        except Exception as e:
            print(f"Warning: Could not load last project: {e}")

    def _open_project_silent(self, project_root: Path):
        """Open project without showing the info dialog.

        Args:
            project_root: Root directory of the project
        """
        success = self.project_controller.open_project(project_root)

        if success:
            # Update UI
            self.project_path_display.setText(str(project_root))
            self.file_browser.set_root(project_root)
            self.status_bar.showMessage(f"Loaded project: {project_root}")
            self.setWindowTitle(f"Blender Project Manager - {project_root.name}")
        else:
            self.status_bar.showMessage("Failed to load last project. Please select a project.")

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
