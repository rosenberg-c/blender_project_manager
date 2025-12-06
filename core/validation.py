"""Validation logic for operations."""

from pathlib import Path
from typing import List, Tuple, Optional


def validate_move_operation(
    old_path: Path,
    new_path: Path
) -> Tuple[List[str], List[str]]:
    """Validate a file/directory move operation.

    Args:
        old_path: Source path
        new_path: Destination path

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check source exists
    if not old_path.exists():
        errors.append(f"Source does not exist: {old_path}")

    # Check destination doesn't exist
    if new_path.exists():
        errors.append(f"Destination already exists: {new_path}")

    # Check destination parent exists
    if not new_path.parent.exists():
        errors.append(f"Destination directory does not exist: {new_path.parent}")

    # Check source and destination aren't the same
    if old_path == new_path:
        errors.append("Source and destination are the same")

    return errors, warnings


def validate_rename_operation(
    find_text: str,
    replace_text: str,
    item_names: List[str]
) -> Tuple[List[str], List[str]]:
    """Validate a rename operation.

    Args:
        find_text: Text to find
        replace_text: Text to replace with
        item_names: Names of items to rename

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check find text is not empty
    if not find_text:
        errors.append("Find text cannot be empty")

    # Check if item_names is empty
    if not item_names:
        warnings.append("No items selected for renaming")

    # Check if find text exists in at least one item
    if item_names and find_text:
        matches = [name for name in item_names if find_text in name]
        if not matches:
            warnings.append(f"Find text '{find_text}' not found in any selected items")

    # Check for duplicate names after replacement
    # Note: replace_text can be empty string (valid for removing text)
    if item_names and find_text:
        new_names = [name.replace(find_text, replace_text) for name in item_names]
        duplicates = [name for name in new_names if new_names.count(name) > 1]
        if duplicates:
            unique_duplicates = list(set(duplicates))
            warnings.append(
                f"Renaming will create duplicate names: {', '.join(unique_duplicates)}"
            )

    return errors, warnings


def validate_link_operation(
    source_file: Path,
    target_file: Path,
    item_names: List[str],
    item_types: List[str],
    target_collection: str,
    link_mode: str
) -> Tuple[List[str], List[str]]:
    """Validate a link operation.

    Args:
        source_file: Source .blend file
        target_file: Target .blend file
        item_names: Names of items to link
        item_types: Types of items ('object' or 'collection')
        target_collection: Target collection name
        link_mode: 'instance' or 'individual'

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check source file exists
    if not source_file.exists():
        errors.append(f"Source file does not exist: {source_file}")

    # Check target file exists
    if not target_file.exists():
        errors.append(f"Target file does not exist: {target_file}")

    # Check item names and types match
    if len(item_names) != len(item_types):
        errors.append("Number of item names must match number of item types")

    # Check for valid item types
    valid_types = {'object', 'collection'}
    invalid_types = [t for t in item_types if t not in valid_types]
    if invalid_types:
        errors.append(f"Invalid item types: {', '.join(invalid_types)}")

    # Check link mode
    if link_mode not in {'instance', 'individual'}:
        errors.append(f"Invalid link mode: {link_mode}. Must be 'instance' or 'individual'")

    # Check instance mode requirements
    if link_mode == 'instance':
        collection_count = sum(1 for t in item_types if t == 'collection')
        object_count = sum(1 for t in item_types if t == 'object')

        if collection_count != 1 or object_count > 0:
            errors.append("Instance mode requires exactly one collection to be selected")

    # Check for naming conflicts
    if target_collection in item_names:
        errors.append(
            f"Target collection name '{target_collection}' conflicts with an item being linked"
        )

    # Check target collection name is not empty
    if not target_collection:
        errors.append("Target collection name cannot be empty")

    return errors, warnings


def check_name_conflict(new_name: str, existing_names: List[str]) -> bool:
    """Check if a new name conflicts with existing names.

    Args:
        new_name: Name to check
        existing_names: List of existing names

    Returns:
        True if conflict exists
    """
    return new_name in existing_names
