"""Centralized UI strings for the Blender Project Manager application.

This module contains all user-facing strings used in dialogs, messages, buttons,
and labels throughout the application. Centralizing these strings makes it easy
to update any UI text from a single location.
"""

# ============================================================================
# Dialog Titles
# ============================================================================

TITLE_PROJECT_OPENED = "Project Opened"
TITLE_ERROR = "Error"
TITLE_SUCCESS = "Success"
TITLE_NO_FILE = "No File"
TITLE_NO_SELECTION = "No Selection"
TITLE_MISSING_INPUT = "Missing Input"
TITLE_NO_ITEMS = "No Items"
TITLE_NO_CHANGE = "No Change"
TITLE_CONFIRM_OPERATION = "Confirm Operation"
TITLE_CONFIRM_RENAME = "Confirm Rename"
TITLE_CONFIRM_LINK = "Confirm Link"
TITLE_CONFIRM_DELETION = "Confirm Deletion"
TITLE_NO_SOURCE_FILE = "No Source File"
TITLE_FILE_NOT_FOUND = "File Not Found"
TITLE_NO_SCENE = "No Scene"
TITLE_NO_SOURCE = "No Source"
TITLE_NO_COLLECTION = "No Collection"
TITLE_LOAD_ERROR = "Load Error"
TITLE_LINK_ERRORS = "Link Errors"
TITLE_LINK_FAILED = "Link Failed"
TITLE_NO_PROJECT = "No Project"
TITLE_NO_BACKUP_FILES = "No Backup Files"
TITLE_CLEANUP_COMPLETE = "Cleanup Complete"
TITLE_RELOAD_COMPLETE = "Reload Complete"
TITLE_LINK_COMPLETE = "Link Complete"
TITLE_BLENDER_NOT_FOUND = "Blender Not Found"
TITLE_ERROR_OPENING_FILE = "Error Opening File"
TITLE_FINDING_REFERENCES = "Finding References"
TITLE_FIND_REFERENCES_RESULTS = "Find References Results"
TITLE_NO_EMPTY_DIRS = "No Empty Directories"
TITLE_REMOVE_EMPTY_DIRS = "Remove Empty Directories"
TITLE_RELOAD_LIBS = "Reload Library Links"
TITLE_UNSUPPORTED_FILE = "Unsupported File Type"

# ============================================================================
# Common Messages
# ============================================================================

MSG_SELECT_BLEND_FILE = "Please select a .blend file first."
MSG_SELECT_FILE = "Please select a file first."
MSG_SELECT_ITEMS_TO_RENAME = "Please select items to rename."
MSG_ENTER_FIND_TEXT = "Please enter text to find."
MSG_NO_VALID_ITEMS = "No valid items selected."
MSG_SOURCE_TARGET_SAME = "Source and target are the same."
MSG_SELECT_SOURCE_BLEND = "Please select a source .blend file in the file browser."
MSG_SELECT_TARGET_SCENE = "Please select a target scene."
MSG_SELECT_VALID_SOURCE = "Please select a valid source .blend file in the file browser."
MSG_SELECT_ITEMS_TO_LINK = "Please select items to link."
MSG_ENTER_COLLECTION_NAME = "Please enter a target collection name."
MSG_OPEN_PROJECT_FIRST = "Please open a project first."
MSG_NO_BACKUP_FILES_FOUND = "No .blend1 or .blend2 backup files found in the project."
MSG_BLENDER_NOT_CONFIGURED = "Cannot open file: Blender path not configured.\n\nPlease ensure a project is open with a valid Blender installation."
MSG_NO_EMPTY_DIRS_FOUND = "No empty directories found in the project."
MSG_UNSUPPORTED_FILE_TYPE = "Please select a .blend file or texture file (.png, .jpg, .exr, etc.)."

# ============================================================================
# Button Text
# ============================================================================

BTN_EXECUTE_MOVE = "Execute Move"
BTN_PROCESSING = "Processing..."
BTN_EXECUTING = "Executing..."
BTN_LOADING = "Loading..."
BTN_LOAD_OBJECTS_COLLECTIONS = "Load Objects/Collections"

# ============================================================================
# Labels
# ============================================================================

LABEL_NO_FILE_SELECTED = "<i>No file selected</i>"
LABEL_NO_BLEND_SELECTED = "<i>No .blend file selected</i>"
LABEL_SELECT_BLEND_IN_BROWSER = "<i>Select a .blend file in the file browser (You must first lock target file)</i>"
LABEL_MOVE_PERFORMANCE_INFO = "<i>Note: Each .blend file scan requires launching Blender (~1-2 seconds per file). Operations may take time with many files in your project.</i>"

# ============================================================================
# Template Messages (use .format() to fill in placeholders)
# ============================================================================

TMPL_PROJECT_INFO = "Project: {project_name}\nRoot: {project_root}\n.blend files found: {blend_count}"
TMPL_SOURCE_FILE_NOT_FOUND = "Source file not found: {file_path}"
TMPL_FAILED_TO_LOAD = "Failed to load objects/collections:\n\n{error}"
TMPL_FAILED_TO_OPEN_BLENDER = "Failed to open {file_name} in Blender:\n\n{error}"
TMPL_OPERATION_FAILED = "Operation failed:\n\n{message}"
TMPL_FAILED_TO_CLEAN = "Failed to clean backup files:\n\n{error}"

TMPL_CONFIRM_MOVE = "Move/rename {item_type}?\n\nFrom: {old_path}\nTo: {new_path}\n\nAll .blend files referencing this will be updated."
TMPL_CONFIRM_RENAME_OBJECTS = "This will rename the selected objects/collections in the .blend file.\n\nAre you sure you want to continue?"
TMPL_CONFIRM_LINK = "This will link the selected objects/collections into the target .blend file.\n\nAre you sure you want to continue?"
TMPL_CONFIRM_DELETE_BACKUPS = "Found {count} backup file(s):\n  • {blend1_count} .blend1 file(s)\n  • {blend2_count} .blend2 file(s)\n\nTotal size: {size_mb:.2f} MB\n\nAre you sure you want to delete these files?\n\nThis action cannot be undone."

TMPL_SUCCESS_WITH_CHANGES = "{message}\n\n{changes} changes made."
TMPL_LINK_COMPLETE = "{message}\n\n{changes} item(s) linked."

TMPL_CONFIRM_DELETE_FILE = "Are you sure you want to delete this file?\n\n{file_path}\n\nThis action cannot be undone."
TMPL_CONFIRM_DELETE_DIR = "Are you sure you want to delete this directory and all its contents?\n\n{dir_path}\n\nThis action cannot be undone."
TMPL_DELETE_SUCCESS = "Successfully deleted:\n{path}"
TMPL_DELETE_FAILED = "Failed to delete:\n{path}\n\nError: {error}"

# Find References templates
TMPL_SCANNING_REFS = "Scanning project for references to {filename}..."
TMPL_ANALYZING_BLEND = "Analyzing .blend files..."
TMPL_REFS_COMPLETE = "Complete!"
TMPL_NO_REFS_FOUND = "No references found.\n\nScanned {count} .blend file(s)."
TMPL_REFS_FOUND_HEADER = "Found {count} file(s) referencing {filename}:"
TMPL_REFS_SCANNED_FOOTER = "Scanned {count} .blend file(s)."
TMPL_FAILED_FIND_REFS = "Failed to find references:\n\n{error}"

# Utilities templates
TMPL_FAILED_REMOVE_DIRS = "Failed to remove empty directories:\n\n{error}"
TMPL_FAILED_RELOAD_LIBS = "Failed to reload library links:\n\n{error}"
