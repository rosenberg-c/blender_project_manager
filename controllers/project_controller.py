"""Main project controller managing application state."""

import json
from pathlib import Path
from typing import Optional

from services.blender_service import BlenderService
from services.filesystem_service import FilesystemService


class ProjectController:
    """Manages project state and coordinates services."""

    def __init__(self):
        """Initialize project controller."""
        self.project_root: Optional[Path] = None
        self.blender_path: Optional[Path] = None
        self.blender_service: Optional[BlenderService] = None
        self.filesystem_service: Optional[FilesystemService] = None
        self._is_open = False

        # Load configuration
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from file.

        Returns:
            Configuration dictionary
        """
        config_path = Path(__file__).parent.parent / "config" / "default_config.json"

        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return {
                "blender": {
                    "macos_path": "/Applications/Blender.app/Contents/MacOS/Blender"
                }
            }

    def get_default_blender_path(self) -> Path:
        """Get the default Blender path for this platform.

        Returns:
            Path to Blender executable
        """
        import platform
        system = platform.system().lower()

        if system == 'darwin':
            return Path(self.config['blender']['macos_path'])
        elif system == 'windows':
            return Path(self.config['blender']['windows_path'])
        else:
            return Path(self.config['blender']['linux_path'])

    def open_project(self, project_root: Path, blender_path: Optional[Path] = None) -> bool:
        """Open a Blender project.

        Args:
            project_root: Root directory of the project
            blender_path: Optional path to Blender (uses default if not provided)

        Returns:
            True if project opened successfully, False otherwise
        """
        if not project_root.exists():
            print(f"Error: Project root does not exist: {project_root}")
            return False

        if not project_root.is_dir():
            print(f"Error: Project root is not a directory: {project_root}")
            return False

        # Use default Blender path if not provided
        if blender_path is None:
            blender_path = self.get_default_blender_path()

        if not blender_path.exists():
            print(f"Error: Blender not found at: {blender_path}")
            return False

        # Initialize services
        self.project_root = project_root
        self.blender_path = blender_path
        self.blender_service = BlenderService(blender_path, project_root)
        self.filesystem_service = FilesystemService(project_root)
        self._is_open = True

        print(f"Project opened: {project_root}")
        return True

    def close_project(self):
        """Close the current project."""
        self.project_root = None
        self.blender_path = None
        self.blender_service = None
        self.filesystem_service = None
        self._is_open = False

    @property
    def is_open(self) -> bool:
        """Check if a project is currently open.

        Returns:
            True if project is open, False otherwise
        """
        return self._is_open

    def get_project_info(self) -> dict:
        """Get information about the current project.

        Returns:
            Dictionary with project information
        """
        if not self.is_open:
            return {}

        blend_files = self.filesystem_service.find_blend_files() if self.filesystem_service else []

        return {
            "project_root": str(self.project_root),
            "blender_path": str(self.blender_path),
            "blend_files_count": len(blend_files),
            "is_open": self.is_open
        }
