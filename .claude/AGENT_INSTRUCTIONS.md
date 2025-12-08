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

### 8. Documentation

**ALWAYS** document public interfaces:
- Use docstrings for all public methods and classes
- Include `Args:`, `Returns:`, and `Raises:` sections
- Keep docstrings concise but complete
- **Don't** add unnecessary comments for self-evident code

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
- [ ] No unnecessary comments
- [ ] Code follows existing patterns in the module

## When in Doubt

1. **Check existing code** - Find similar functionality and match its pattern
2. **Prefer simplicity** - Don't over-engineer
3. **Ask "Is this maintainable?"** - Will another developer understand this in 6 months?
4. **Extract, don't duplicate** - If you're copying code, extract it instead
