"""File scanning utilities for finding .blend and texture files."""

import os
import sys
from pathlib import Path
from typing import List, Set

# Import constants from centralized location
sys.path.insert(0, str(Path(__file__).parent.parent))
from blender_lib.constants import TEXTURE_EXTENSIONS, BLEND_EXTENSIONS, IGNORE_PATTERNS

# Convert list constants to sets for faster lookup
TEXTURE_EXTENSIONS = set(TEXTURE_EXTENSIONS)
BLEND_EXTENSIONS = set(BLEND_EXTENSIONS)
DEFAULT_IGNORE_DIRS = set(IGNORE_PATTERNS)


def find_blend_files(
    root_path: Path,
    ignore_dirs: Set[str] = None,
    recursive: bool = True
) -> List[Path]:
    """Find all .blend files under root path.

    Args:
        root_path: Directory to search
        ignore_dirs: Set of directory names to ignore
        recursive: If True, search subdirectories

    Returns:
        List of paths to .blend files
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    blend_files = []

    if not root_path.exists() or not root_path.is_dir():
        return blend_files

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Remove ignored directories in-place to prevent os.walk from entering them
            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs and not d.startswith(".")
            ]

            for fname in filenames:
                if fname.lower().endswith(".blend") and not fname.startswith("."):
                    blend_files.append(Path(dirpath) / fname)
    else:
        # Non-recursive: only check immediate children
        for item in root_path.iterdir():
            if item.is_file() and item.suffix.lower() == ".blend":
                blend_files.append(item)

    return sorted(blend_files)


def find_texture_files(
    root_path: Path,
    ignore_dirs: Set[str] = None,
    extensions: Set[str] = None,
    recursive: bool = True
) -> List[Path]:
    """Find all texture files under root path.

    Args:
        root_path: Directory to search
        ignore_dirs: Set of directory names to ignore
        extensions: Set of file extensions to include (with dots)
        recursive: If True, search subdirectories

    Returns:
        List of paths to texture files
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    if extensions is None:
        extensions = TEXTURE_EXTENSIONS

    # Normalize extensions to lowercase
    extensions = {ext.lower() for ext in extensions}

    texture_files = []

    if not root_path.exists() or not root_path.is_dir():
        return texture_files

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Remove ignored directories
            dirnames[:] = [
                d for d in dirnames
                if d not in ignore_dirs and not d.startswith(".")
            ]

            for fname in filenames:
                if not fname.startswith("."):
                    file_path = Path(dirpath) / fname
                    if file_path.suffix.lower() in extensions:
                        texture_files.append(file_path)
    else:
        # Non-recursive
        for item in root_path.iterdir():
            if item.is_file() and item.suffix.lower() in extensions:
                texture_files.append(item)

    return sorted(texture_files)


def find_backup_files(
    root_path: Path,
    ignore_dirs: Set[str] = None
) -> List[Path]:
    """Find all Blender backup files (.blend1, .blend2).

    Args:
        root_path: Directory to search
        ignore_dirs: Set of directory names to ignore

    Returns:
        List of paths to backup files
    """
    if ignore_dirs is None:
        ignore_dirs = DEFAULT_IGNORE_DIRS

    backup_files = []
    backup_extensions = {'.blend1', '.blend2'}

    if not root_path.exists() or not root_path.is_dir():
        return backup_files

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Remove ignored directories
        dirnames[:] = [
            d for d in dirnames
            if d not in ignore_dirs and not d.startswith(".")
        ]

        for fname in filenames:
            file_path = Path(dirpath) / fname
            if file_path.suffix.lower() in backup_extensions:
                backup_files.append(file_path)

    return sorted(backup_files)


def get_file_type(file_path: Path) -> str:
    """Determine file type (blend, texture, or other).

    Args:
        file_path: Path to file

    Returns:
        'blend', 'texture', or 'other'
    """
    suffix = file_path.suffix.lower()

    if suffix in BLEND_EXTENSIONS:
        return 'blend'
    elif suffix in TEXTURE_EXTENSIONS:
        return 'texture'
    else:
        return 'other'


def is_texture_file(file_path: Path) -> bool:
    """Check if file is a supported texture file."""
    return file_path.suffix.lower() in TEXTURE_EXTENSIONS


def is_blend_file(file_path: Path) -> bool:
    """Check if file is a .blend file."""
    return file_path.suffix.lower() == '.blend'


def calculate_directory_size(directory: Path, pattern: str = None) -> int:
    """Calculate total size of files in directory.

    Args:
        directory: Directory to calculate size for
        pattern: Optional glob pattern to filter files

    Returns:
        Total size in bytes
    """
    total_size = 0

    if not directory.exists() or not directory.is_dir():
        return 0

    if pattern:
        files = directory.rglob(pattern)
    else:
        files = directory.rglob('*')

    for file_path in files:
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except (OSError, PermissionError):
                # Skip files we can't access
                pass

    return total_size
