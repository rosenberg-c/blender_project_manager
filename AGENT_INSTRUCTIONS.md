# Agent Instructions for Blender Project Manager

## Code Maintainability Guidelines

When working on this codebase, follow these strict maintainability principles:

### 1. String Management

**ALWAYS** use the centralized strings file for user-facing text:
- **Location**: `gui/ui_strings.py`
- **Never** hardcode dialog titles, messages, or button text directly in code
- **Add new strings** to `ui_strings.py` before using them
- **Categories**:
  - `TITLE_*` - Dialog and window titles
  - `MSG_*` - Common messages
  - `BTN_*` - Button text
  - `LABEL_*` - UI labels
  - `TMPL_*` - Template messages (use `.format()` for placeholders)

**Example**:
```python
# ❌ BAD - Hardcoded strings
QMessageBox.warning(self, "No Project", "Please open a project first.")
progress_dialog.update_progress(0, "Scanning project...")

# ✅ GOOD - Use ui_strings.py
from gui.ui_strings import TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST
QMessageBox.warning(self, TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
```

### 2. Constants Management

**ALWAYS** use the centralized constants file for application-wide values:
- **Location**: `blender_lib/constants.py`
- **Never** duplicate constant lists or magic values
- **Available constants**:
  - `TEXTURE_EXTENSIONS` - Supported texture file formats
  - `BLEND_EXTENSIONS` - Blender file formats
  - `BACKUP_EXTENSIONS` - Backup file formats
  - `TIMEOUT_*` - Operation timeout values
  - `IGNORE_PATTERNS` - Directory ignore patterns

**Example**:
```python
# ❌ BAD - Duplicated constants
texture_extensions = ['.png', '.jpg', '.jpeg', '.exr', '.hdr', '.tif', '.tiff']
is_texture = suffix in texture_extensions

# ✅ GOOD - Use constants.py
from blender_lib.constants import TEXTURE_EXTENSIONS
is_texture = suffix in TEXTURE_EXTENSIONS
```

### 3. Separation of Concerns

**ALWAYS** maintain clear boundaries between layers:

- **GUI Layer** (`gui/`):
  - Handle only UI events and display
  - Delegate business logic to services
  - Keep UI components focused and small

- **Service Layer** (`services/`):
  - Contain business logic and orchestration
  - Interface between GUI and Blender scripts
  - No direct UI code (no QMessageBox, etc.)

- **Blender Scripts** (`blender_lib/`):
  - Pure Blender operations
  - Return structured JSON results
  - No knowledge of GUI

**Example**:
```python
# ❌ BAD - Business logic in GUI
class FileBrowserWidget:
    def _find_references(self):
        # ... lots of Blender interaction code here ...

# ✅ GOOD - Delegate to service
class FileBrowserWidget:
    def _find_references(self):
        result = self.blender_service.find_references(target_file)
        self._display_references_result(result)
```

### 4. Error Handling

**ALWAYS** use consistent error handling patterns:

- Catch specific exceptions when possible
- Provide user-friendly error messages from `ui_strings.py`
- Log technical details for debugging
- Always close progress dialogs in `finally` blocks

**Example**:
```python
# ✅ GOOD - Consistent error handling
progress_dialog = None
try:
    progress_dialog = OperationProgressDialog(TITLE_FINDING_REFS, self)
    progress_dialog.show()

    result = self.service.do_operation()

    if not result.get("success"):
        QMessageBox.critical(self, TITLE_ERROR,
            TMPL_OPERATION_FAILED.format(message=result.get("error")))
        return

    # ... handle success ...

except Exception as e:
    QMessageBox.critical(self, TITLE_ERROR,
        TMPL_OPERATION_FAILED.format(message=str(e)))
finally:
    if progress_dialog:
        progress_dialog.close()
```

### 5. Code Duplication

**NEVER** copy-paste code:
- Extract common patterns into helper methods
- Use base classes for shared functionality
- Create utility functions for repeated operations

**Example**:
```python
# ❌ BAD - Duplicated validation
def operation_a(self):
    if not self.project.is_open:
        QMessageBox.warning(self, "No Project", "Please open a project first.")
        return
    # ... do operation A ...

def operation_b(self):
    if not self.project.is_open:
        QMessageBox.warning(self, "No Project", "Please open a project first.")
        return
    # ... do operation B ...

# ✅ GOOD - Extract to helper
def _check_project_open(self) -> bool:
    """Check if project is open, show warning if not."""
    if not self.project.is_open:
        QMessageBox.warning(self, TITLE_NO_PROJECT, MSG_OPEN_PROJECT_FIRST)
        return False
    return True

def operation_a(self):
    if not self._check_project_open():
        return
    # ... do operation A ...
```

### 6. File Organization

**ALWAYS** follow the established architecture:

```
blender_project_manager/
├── blender_lib/          # Pure Blender scripts (Python scripts run inside Blender)
│   ├── constants.py      # Shared constants
│   └── script_utils.py   # Shared utilities for scripts
├── core/                 # Core utilities (file scanning, etc.)
├── controllers/          # Application controllers
├── services/             # Business logic layer
│   └── blender_service.py
├── gui/                  # GUI layer
│   ├── ui_strings.py     # ALL user-facing strings
│   ├── operations/       # Operation-specific UI tabs
│   └── *.py             # UI components
└── tests/               # Test suite
```

### 7. Testing Requirements

**ALWAYS** write tests for new features:
- Unit tests for business logic
- Integration tests for Blender operations
- Mock external dependencies (Blender, file system when appropriate)
- Aim for high coverage of critical paths

### 8. Documentation and Comments

**ALWAYS** document public interfaces:
- Use docstrings for all public methods and classes
- Include `Args:`, `Returns:`, and `Raises:` sections
- Keep docstrings concise but complete

**AVOID unnecessary comments:**
- Code should be self-documenting through clear variable/function names
- Only add comments when code behavior is non-obvious
- Comments should explain **WHY**, not **WHAT**
- If you need to explain what code does, consider refactoring for clarity

**Good reasons to add comments:**
- Complex algorithms or business logic
- Performance optimizations that look unusual
- Workarounds for bugs in external libraries
- Important constraints or assumptions
- Security-related decisions

**Examples**:

```python
# ❌ BAD - Unnecessary comments that state the obvious
def rename_file(old_path, new_path):
    # Check if old path exists
    if not old_path.exists():
        return False

    # Move the file to new location
    shutil.move(str(old_path), str(new_path))

    # Return success
    return True

# ✅ GOOD - Self-documenting code, only comment the non-obvious
def rename_file(old_path, new_path):
    if not old_path.exists():
        return False

    # OPTIMIZATION: Fast path for same-directory renames
    # If moving within the same directory, relative paths don't need rebasing
    # This avoids the 20-second Blender startup overhead
    if old_path.parent == new_path.parent:
        shutil.move(str(old_path), str(new_path))
        return True

    # Different directories - use Blender to rebase internal paths
    return _move_with_rebasing(old_path, new_path)
```

```python
# ❌ BAD - Comment explains what (code already shows this)
# Loop through all blend files
for blend_file in blend_files:
    # Process the blend file
    process(blend_file)

# ✅ GOOD - No comment needed, code is clear
for blend_file in blend_files:
    process(blend_file)

# ✅ ALSO GOOD - Comment explains why (non-obvious constraint)
# Skip generated/packed images to avoid rebasing internal Blender data
for image in images:
    if not image.filepath or image.packed_file:
        continue
    rebase_path(image.filepath)
```

**PROACTIVE CLEANUP:**
- **Remove unnecessary comments when you see them** during code work
- Treat comment cleanup as part of routine maintenance
- If editing a file with obvious comments (like `# Loop through files`), remove them
- Don't make separate commits just for comment removal - include in your current work
- Exception: Don't remove comments from code you're not already modifying unless doing a dedicated cleanup

**Example during regular work:**
```python
# You're editing this function to add a new parameter
def process_files(file_list, new_param):
    # Loop through all files  ← REMOVE: obvious
    for file in file_list:
        # Process each file  ← REMOVE: obvious
        process(file)

    # Return success  ← REMOVE: obvious
    return True

# Should become:
def process_files(file_list, new_param):
    for file in file_list:
        process(file)
    return True
```

## Common Refactoring Patterns

### Moving Hardcoded Strings to ui_strings.py

1. Identify the hardcoded string
2. Determine the appropriate category (TITLE_, MSG_, BTN_, etc.)
3. Add to `gui/ui_strings.py` with a clear, descriptive name
4. Import and use in your code
5. Update all occurrences if the string is duplicated

### Extracting Constants

1. Find duplicated values or magic numbers
2. Add to `blender_lib/constants.py` with documentation
3. Import and use throughout codebase
4. Remove all duplicates

### Extracting Helper Methods

1. Identify repeated code blocks (>2 occurrences)
2. Extract to a private helper method (`_method_name`)
3. Add clear docstring
4. Replace all occurrences with method call

## Pre-Commit Checklist

Before committing code, verify:

- [ ] No hardcoded UI strings (all in `ui_strings.py`)
- [ ] No duplicated constants (all in `constants.py`)
- [ ] No copy-pasted code blocks
- [ ] Proper separation of concerns (UI/Service/Blender layers)
- [ ] Consistent error handling with proper cleanup
- [ ] Tests added/updated for new functionality
- [ ] Docstrings added for public methods
- [ ] No unnecessary comments (only comment the WHY, not the WHAT)
- [ ] Code follows existing patterns in the module

## When in Doubt

1. **Check existing code** - Find similar functionality and match its pattern
2. **Prefer simplicity** - Don't over-engineer
3. **Ask "Is this maintainable?"** - Will another developer understand this in 6 months?
4. **Extract, don't duplicate** - If you're copying code, extract it instead
5. **Clean as you go** - Remove unnecessary comments when editing files
