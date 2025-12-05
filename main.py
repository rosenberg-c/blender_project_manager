"""Blender Project Manager - Main Entry Point.

A desktop GUI application for managing Blender projects with automatic
reference tracking and updating.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Blender Project Manager")
    app.setOrganizationName("BlenderTools")
    app.setApplicationVersion("0.1.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
