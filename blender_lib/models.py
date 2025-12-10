"""Data models for Blender project management."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class ImageReference:
    """An image reference found in a blend file."""
    name: str
    filepath: str
    is_relative: bool
    resolved_path: Optional[Path] = None
    exists: bool = False


@dataclass
class LibraryReference:
    """A library reference found in a blend file."""
    name: str
    filepath: str
    is_relative: bool
    resolved_path: Optional[Path] = None
    exists: bool = False
    linked_objects: List[str] = field(default_factory=list)
    linked_collections: List[str] = field(default_factory=list)


@dataclass
class BlendReferences:
    """All references found in a blend file."""
    blend_path: Path
    images: List[ImageReference] = field(default_factory=list)
    libraries: List[LibraryReference] = field(default_factory=list)
    scan_date: Optional[datetime] = None


@dataclass
class PathChange:
    """A single path change in an operation preview."""
    file_path: Path           # Which file will be modified
    item_type: str            # 'image' or 'library'
    item_name: str            # Name of the image/library
    old_path: str             # Current path
    new_path: str             # New path
    status: str = 'ok'        # 'ok', 'warning', 'error'


@dataclass
class OperationPreview:
    """Preview of what an operation will change."""
    operation_name: str
    changes: List[PathChange] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if operation can be executed (no errors)."""
        return len(self.errors) == 0

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.changes)


@dataclass
class OperationResult:
    """Result of executing an operation."""
    success: bool
    message: str = ""
    errors: List[str] = field(default_factory=list)
    changes_made: int = 0


@dataclass
class LinkOperationParams:
    """Parameters for linking objects/collections between .blend files."""
    target_file: Path
    target_scene: str
    source_file: Path
    item_names: List[str]       # Names of objects/collections to link
    item_types: List[str]        # 'object' or 'collection' for each item
    target_collection: str       # Collection name to create/use in target
    link_mode: str = 'instance'  # 'instance' (Blender default) or 'individual'
    hide_viewport: bool = False  # Hide the target collection (eye icon) in outliner
    hide_instancer: bool = False  # Hide instancer visualization for Empty objects
