"""Blender Project Manager - Main Entry Point.

A desktop GUI application for managing Blender projects with automatic
reference tracking and updating.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow
from gui.theme import Theme


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Blender Project Manager")
    app.setOrganizationName("BlenderTools")
    app.setApplicationVersion("0.1.0")

    # Set application icon
    icon_path = Path(__file__).parent / 'resources' / 'icons' / 'app_icon_current.svg'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Create and show main window (theme will be loaded in MainWindow.__init__)
    window = MainWindow()

    # Apply global theme stylesheet after window loads theme preference
    app.setStyleSheet(Theme.get_stylesheet())

    window.show()

    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
