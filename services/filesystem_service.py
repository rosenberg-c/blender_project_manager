"""Filesystem operations and scanning."""

import os
from pathlib import Path
from typing import List, Set

from core.file_scanner import find_blend_files as core_find_blend_files


class FilesystemService:
    """Handles file system operations and scanning."""

    def __init__(self, project_root: Path):
        """Initialize filesystem service.

        Args:
            project_root: Root directory of the Blender project
        """
        self.project_root = project_root
        self.ignore_patterns: Set[str] = {
            '.git', '.svn', '__pycache__',
            '.DS_Store', '.idea', '.vscode'
        }
        self.ignore_hidden = True

    def find_blend_files(self) -> List[Path]:
        """Find all .blend files in the project.

        Delegates to core.file_scanner.find_blend_files.

        Returns:
            List of Path objects for .blend files
        """
        return core_find_blend_files(self.project_root, self.ignore_patterns)

    def find_files_by_extension(self, extensions: List[str]) -> List[Path]:
        """Find all files with given extensions.

        Args:
            extensions: List of extensions (e.g., ['.jpg', '.png'])

        Returns:
            List of Path objects
        """
        files = []

        for dirpath, dirnames, filenames in os.walk(self.project_root):
            # Prune ignored directories
            dirnames[:] = [
                d for d in dirnames
                if d not in self.ignore_patterns
                and (not self.ignore_hidden or not d.startswith('.'))
            ]

            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(Path(dirpath) / filename)

        return files

    def is_project_path(self, path: Path) -> bool:
        """Check if path is within the project root.

        Args:
            path: Path to check

        Returns:
            True if path is within project, False otherwise
        """
        try:
            path.relative_to(self.project_root)
            return True
        except ValueError:
            return False
