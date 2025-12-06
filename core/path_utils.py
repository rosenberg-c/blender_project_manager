"""Pure path manipulation utilities."""

import os
from pathlib import Path
from typing import Optional


def rebase_relative_path(original_path: str, old_dir: Path, new_dir: Path) -> str:
    """Convert Blender relative path when blend file moves.

    When a .blend file moves to a new directory, its relative paths (//)
    need to be updated to still point to the same absolute locations.

    Args:
        original_path: Blender path starting with '//'
        old_dir: Directory where blend currently lives
        new_dir: Directory where blend will move to

    Returns:
        New relative path that points to same absolute location

    Example:
        >>> old_dir = Path("/project/scenes")
        >>> new_dir = Path("/project/exported/scenes")
        >>> rebase_relative_path("//../../textures/wood.jpg", old_dir, new_dir)
        "//../../../textures/wood.jpg"
    """
    if not original_path.startswith("//"):
        return original_path

    # Strip leading '//' and normalize slashes
    rel_part = original_path[2:].replace("\\", "/")

    # Get absolute path as seen from old blend directory
    abs_from_old = os.path.normpath(os.path.join(str(old_dir), rel_part))

    # Calculate new relative path from new blend directory
    try:
        new_rel = os.path.relpath(abs_from_old, str(new_dir))
        new_rel = new_rel.replace("\\", "/")
    except ValueError:
        # Can't make relative path (different drives on Windows)
        return original_path

    return "//" + new_rel


def resolve_blender_path(blender_path: str, blend_dir: Path) -> Path:
    """Resolve a Blender path (relative or absolute) to absolute path.

    Args:
        blender_path: Path that may start with '//' for relative
        blend_dir: Directory containing the .blend file

    Returns:
        Absolute path
    """
    if blender_path.startswith("//"):
        rel_part = blender_path[2:].replace("\\", "/")
        return Path(os.path.normpath(os.path.join(str(blend_dir), rel_part)))
    return Path(blender_path)


def make_blender_relative(abs_path: Path, blend_dir: Path) -> str:
    """Convert absolute path to Blender relative path.

    Args:
        abs_path: Absolute path to convert
        blend_dir: Directory containing the .blend file

    Returns:
        Blender relative path starting with '//'
    """
    try:
        rel_path = os.path.relpath(str(abs_path), str(blend_dir))
        rel_path = rel_path.replace("\\", "/")
        return "//" + rel_path
    except ValueError:
        # Can't make relative (different drives on Windows)
        return str(abs_path)


def is_blender_path_relative(path: str) -> bool:
    """Check if a path is Blender relative (starts with //)."""
    return path.startswith("//")


def normalize_path_separators(path: str) -> str:
    """Normalize path separators to forward slashes (Blender standard)."""
    return path.replace("\\", "/")


def get_path_depth(path: str) -> int:
    """Get the depth of a relative path (number of directory levels).

    Args:
        path: Relative path (may start with //)

    Returns:
        Number of directory separators
    """
    # Remove leading // if present
    clean_path = path[2:] if path.startswith("//") else path
    return clean_path.count('/') + clean_path.count('\\')
