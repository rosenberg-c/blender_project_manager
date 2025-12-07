"""Constants for Blender operations.

This module contains all constants used across Blender scripts and the application
to eliminate duplication and provide a single source of truth.
"""

# ============================================================================
# File Extensions
# ============================================================================

# Texture file extensions supported by Blender
TEXTURE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']

# Blender file extensions
BLEND_EXTENSIONS = ['.blend']

# Blender backup file extensions
BACKUP_EXTENSIONS = ['.blend1', '.blend2']

# All supported file extensions
ALL_SUPPORTED_EXTENSIONS = TEXTURE_EXTENSIONS + BLEND_EXTENSIONS

# ============================================================================
# Timeout Values (in seconds)
# ============================================================================

# Short operations (listing, simple queries)
TIMEOUT_SHORT = 60

# Medium operations (rename, basic file operations)
TIMEOUT_MEDIUM = 120

# Long operations (move files, link objects)
TIMEOUT_LONG = 180

# Very long operations (large directory moves)
TIMEOUT_VERY_LONG = 300

# ============================================================================
# Ignore Patterns
# ============================================================================

# Directory patterns to ignore when scanning projects
IGNORE_PATTERNS = [
    '.git',
    '.venv',
    'venv',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '.DS_Store',
    'build',
    'dist',
    '*.egg-info'
]
