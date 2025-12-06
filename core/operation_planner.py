"""Planning logic for operations without executing them."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple

from .file_scanner import find_blend_files, find_texture_files, TEXTURE_EXTENSIONS, BLEND_EXTENSIONS
from .path_utils import resolve_blender_path, rebase_relative_path


@dataclass
class MoveImpact:
    """Impact analysis for a file/directory move."""
    files_to_move: List[Path]
    blend_files_affected: List[Path]  # .blend files with references to moved files
    total_files: int
    total_size: int


def plan_directory_move(old_dir: Path, new_dir: Path) -> MoveImpact:
    """Plan what will happen when moving a directory.

    Args:
        old_dir: Source directory
        new_dir: Destination directory

    Returns:
        MoveImpact with details about what will be affected
    """
    files_to_move = []

    if not old_dir.exists() or not old_dir.is_dir():
        return MoveImpact(
            files_to_move=[],
            blend_files_affected=[],
            total_files=0,
            total_size=0
        )

    # Find all .blend and texture files in directory
    blend_files = []
    texture_files = []

    for ext in BLEND_EXTENSIONS:
        blend_files.extend(old_dir.rglob(f'*{ext}'))

    for ext in TEXTURE_EXTENSIONS:
        texture_files.extend(old_dir.rglob(f'*{ext}'))

    files_to_move = blend_files + texture_files

    # Calculate total size
    total_size = 0
    for file_path in files_to_move:
        try:
            total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass

    return MoveImpact(
        files_to_move=files_to_move,
        blend_files_affected=blend_files,  # All blend files in dir will need rebasing
        total_files=len(files_to_move),
        total_size=total_size
    )


def find_files_to_rebase_for_move(
    moved_files: List[Path],
    project_root: Path
) -> List[Path]:
    """Find .blend files that need path rebasing after files are moved.

    Args:
        moved_files: List of files that were/will be moved
        project_root: Project root directory to search

    Returns:
        List of .blend files that might reference the moved files
    """
    # Find all .blend files in project
    all_blend_files = find_blend_files(project_root)

    # Filter out .blend files that are in the moved_files list
    moved_file_set = set(moved_files)
    files_to_check = [f for f in all_blend_files if f not in moved_file_set]

    return files_to_check


def extract_moved_file_paths(
    files: List[Path],
    old_parent: Path
) -> List[str]:
    """Extract old absolute paths for moved files.

    Args:
        files: List of files being moved
        old_parent: Old parent directory

    Returns:
        List of old absolute paths as strings
    """
    return [str(f.resolve()) for f in files]


def should_rebase_path(
    referenced_path: str,
    moved_files_old_paths: Set[str],
    blend_dir: Path
) -> bool:
    """Determine if a path should be rebased.

    A path should NOT be rebased if the referenced file was also moved
    (relative relationship is preserved).

    Args:
        referenced_path: Blender path (may be relative //)
        moved_files_old_paths: Set of old absolute paths of files that were moved
        blend_dir: Directory containing the .blend file

    Returns:
        True if path should be rebased
    """
    # Only check relative paths
    if not referenced_path.startswith("//"):
        return False

    # Resolve to absolute path
    abs_path = resolve_blender_path(referenced_path, blend_dir)

    # If the referenced file was also moved, don't rebase
    if str(abs_path.resolve()) in moved_files_old_paths:
        return False

    return True
