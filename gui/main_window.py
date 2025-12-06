"""Main application window."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QStatusBar,
    QLabel, QPushButton, QLineEdit, QFrame, QApplication
)

from controllers.project_controller import ProjectController
from controllers.file_operations_controller import FileOperationsController
from gui.file_browser import FileBrowserWidget
from gui.operations_panel import OperationsPanelWidget
from gui.theme import Theme


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

        # Load theme preference FIRST, before creating any UI
        self.load_theme_preference()

        # Initialize controllers
        self.project_controller = ProjectController()
        self.file_ops_controller = FileOperationsController(self.project_controller)

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

        # Restore window geometry and splitter state
        self.restore_window_state()

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
        self.splitter = QSplitter(Qt.Horizontal)

        # Left: File browser
        self.file_browser = FileBrowserWidget(self.project_controller, self.config_file)
        self.file_browser.file_selected.connect(self._on_file_selected)
        self.splitter.addWidget(self.file_browser)

        # Right: Operations panel
        self.operations_panel = OperationsPanelWidget(self.file_ops_controller, self.config_file)
        self.splitter.addWidget(self.operations_panel)

        # Set initial sizes (2:1 ratio)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter)

    def create_project_selector_bar(self) -> QWidget:
        """Create the project selector bar at the top of the window."""
        self.project_bar = QFrame()
        self.project_bar.setFrameShape(QFrame.StyledPanel)
        self.project_bar.setStyleSheet(Theme.get_project_bar_style())
        self.project_bar.setMaximumHeight(42)  # Very compact height
        self.project_bar.setMinimumHeight(32)

        layout = QHBoxLayout(self.project_bar)
        layout.setContentsMargins(3, 3, 3, 3)  # Very tight margins
        layout.setSpacing(5)

        # Label
        label = QLabel("<b>Project:</b>")
        layout.addWidget(label)

        # Project path display (read-only line edit)
        self.project_path_display = QLineEdit()
        self.project_path_display.setReadOnly(True)
        self.project_path_display.setPlaceholderText("No project selected")
        self.project_path_display.setFixedHeight(22)
        layout.addWidget(self.project_path_display, stretch=1)

        # Select/Change button
        self.select_project_btn = QPushButton("Select Project...")
        self.select_project_btn.clicked.connect(self.select_project)
        self.select_project_btn.setFixedHeight(22)
        self.select_project_btn.setProperty("class", "primary")
        layout.addWidget(self.select_project_btn)

        # Theme toggle button
        self.theme_toggle_btn = QPushButton("🌙")  # Default icon
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        self.theme_toggle_btn.setFixedHeight(22)
        self.theme_toggle_btn.setFixedWidth(28)
        self.theme_toggle_btn.setToolTip("Toggle dark/light theme")
        layout.addWidget(self.theme_toggle_btn)

        # Apply compact button styles
        self._update_project_bar_button_styles()

        # Set correct icon based on current theme
        current_theme = Theme.current_theme
        self.theme_toggle_btn.setText("☀️" if current_theme == 'light' else "🌙")

        return self.project_bar

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

            # Restore file browser state (expanded paths and selected file)
            self.file_browser.restore_state()

            # Apply pending restorations in operations panel (e.g., locked file)
            self.operations_panel.apply_pending_restorations()

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

            # Load existing config to preserve theme preference
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            config_data["last_project"] = str(project_root)

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

            # Restore file browser state (expanded paths and selected file)
            self.file_browser.restore_state()

            # Apply pending restorations in operations panel (e.g., locked file)
            self.operations_panel.apply_pending_restorations()
        else:
            self.status_bar.showMessage("Failed to load last project. Please select a project.")

    def _on_file_selected(self, file_path: Path):
        """Handle file selection from browser.

        Args:
            file_path: Path to selected file
        """
        self.operations_panel.set_file(file_path)
        self.status_bar.showMessage(f"Selected: {file_path.name}")

    def _update_project_bar_button_styles(self):
        """Update project bar button styles with theme colors and compact padding."""
        c = Theme.get_colors()

        # Primary button (Select Project) - compact with theme colors
        self.select_project_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['primary']};
                color: {c['text_inverse']};
                border: none;
                padding: 2px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['primary_hover']};
            }}
        """)

        # Theme toggle button - compact with base button colors
        self.theme_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['bg_secondary']};
                color: {c['text_primary']};
                border: 1px solid {c['border_medium']};
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {c['bg_tertiary']};
                border-color: {c['border_dark']};
            }}
        """)

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = Theme.toggle_theme()

        # Update the app stylesheet
        QApplication.instance().setStyleSheet(Theme.get_stylesheet())

        # Update component-specific styles that don't use global stylesheet
        self.project_bar.setStyleSheet(Theme.get_project_bar_style())
        self.operations_panel.file_display.setStyleSheet(Theme.get_file_display_style())

        # Update project bar buttons with new theme colors
        self._update_project_bar_button_styles()

        # Update button icon
        self.theme_toggle_btn.setText("☀️" if new_theme == 'light' else "🌙")

        # Save theme preference
        self.save_theme_preference(new_theme)

    def save_theme_preference(self, theme: str):
        """Save the current theme preference to config file.

        Args:
            theme: Theme name ('light' or 'dark')
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Load existing config or create new one
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            config_data['theme'] = theme

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save theme preference: {e}")

    def load_theme_preference(self):
        """Load and apply the saved theme preference."""
        try:
            if not self.config_file.exists():
                return

            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            theme = config_data.get('theme', 'light')
            Theme.set_theme(theme)

            # Update button icon based on loaded theme (if button exists)
            if hasattr(self, 'theme_toggle_btn'):
                self.theme_toggle_btn.setText("☀️" if theme == 'light' else "🌙")

        except Exception as e:
            print(f"Warning: Could not load theme preference: {e}")

    def save_window_state(self):
        """Save window geometry and splitter state to config file."""
        try:
            import base64

            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Save window geometry
            geometry = self.saveGeometry()
            config_data['window_geometry'] = base64.b64encode(geometry.data()).decode('utf-8')

            # Save splitter state
            splitter_state = self.splitter.saveState()
            config_data['splitter_state'] = base64.b64encode(splitter_state.data()).decode('utf-8')

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save window state: {e}")

    def restore_window_state(self):
        """Restore window geometry and splitter state from config file."""
        try:
            import base64
            from PySide6.QtCore import QByteArray

            if not self.config_file.exists():
                return

            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            # Restore window geometry
            if 'window_geometry' in config_data:
                geometry_data = base64.b64decode(config_data['window_geometry'])
                self.restoreGeometry(QByteArray(geometry_data))

            # Restore splitter state
            if 'splitter_state' in config_data:
                splitter_data = base64.b64decode(config_data['splitter_state'])
                self.splitter.restoreState(QByteArray(splitter_data))

        except Exception as e:
            print(f"Warning: Could not restore window state: {e}")

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
            "<li>Light/Dark theme support</li>"
            "</ul>"
            "<p>Built with Python and PySide6 (Qt for Python)</p>"
        )

    def closeEvent(self, event):
        """Handle window close event.

        Args:
            event: QCloseEvent
        """
        # Save window state before closing
        self.save_window_state()

        # Save file browser state
        self.file_browser.save_state()

        # Close project if open
        if self.project_controller.is_open:
            self.project_controller.close_project()
        event.accept()
