# Blender Project Manager - Refactoring Plan

**Status:** Not Started
**Last Updated:** 2025-12-07
**Completion:** 0 / 68 tasks (0%)

---

## Overview

This refactoring plan addresses critical code duplication and architectural issues discovered in the codebase:

- **205+ hardcoded UI strings** scattered across 16 files
- **File extensions duplicated 5 times** across the codebase
- **`rebase_relative_path()` duplicated 4 times** with different implementations
- **`find_blend_files()` duplicated 4 times**
- **JSON output handling duplicated in 13 Blender scripts**
- **operations_panel.py is 1,860 LOC** (monolithic file)

---

## Execution Strategy

**Approach:** Moderate risk - run low-risk phases in parallel where safe

**Timeline:** 3 weeks (recommended)
- Week 1: Phase 1 (UI Strings) + Phase 3 (Path Utils) in parallel
- Week 2: Phase 2 (Blender Scripts)
- Week 3: Phase 4 (Split Panel)

---

## PHASE 1: UI String Centralization

**Goal:** Fix hardcoded UI strings scattered across 205+ locations
**Priority:** HIGH (User's immediate pain point)
**Risk:** LOW (no logic changes)
**Status:** Not Started

### Setup
- [ ] 1.1. Create `gui/ui_strings.py` with all string constants
  - [ ] Dialog titles (TITLE_NO_FILE, TITLE_ERROR, etc.)
  - [ ] Common messages (MSG_NO_FILE_SELECTED, etc.)
  - [ ] Button text (BTN_EXECUTE_MOVE, BTN_LOADING, etc.)
  - [ ] Labels (LABEL_NO_FILE_SELECTED, etc.)
  - [ ] Template messages (TMPL_CONFIRM_MOVE, etc.)

### Update Files
- [ ] 1.2. Update `gui/main_window.py` (2 QMessageBox calls)
  - [ ] Add `from gui.ui_strings import *`
  - [ ] Replace hardcoded strings with constants
  - [ ] Test: Application launch and project selection

- [ ] 1.3. Update `gui/file_browser.py` (3 QMessageBox calls)
  - [ ] Add import
  - [ ] Replace hardcoded strings
  - [ ] Test: File browser functionality

- [ ] 1.4. Update `gui/operations_panel.py` (46 QMessageBox calls)
  - [ ] Add import
  - [ ] Replace lines 666, 846, 985: `"No File"` → `TITLE_NO_FILE`
  - [ ] Replace lines 57, 1051, 1105, 1200: `"<i>No file selected</i>"` → `LABEL_NO_FILE_SELECTED`
  - [ ] Replace lines 997, 1225: Duplicate supported types → `MSG_SUPPORTED_TYPES`
  - [ ] Replace all other hardcoded strings systematically
  - [ ] Test: All operations (move, rename, link, utilities)

### Verification
- [ ] 1.5. Trigger each dialog type manually, verify text displays correctly
- [ ] 1.6. Run full test suite, ensure no regression
- [ ] 1.7. Git commit: "Phase 1: Centralize UI strings"

---

## PHASE 2: Blender Script Utilities Consolidation

**Goal:** Eliminate duplication in 13 Blender scripts
**Priority:** CRITICAL
**Risk:** MEDIUM (touches core functionality)
**Status:** Not Started

### Setup
- [ ] 2.1. Create `blender_lib/script_utils.py`
  - [ ] `output_json()` function
  - [ ] `create_error_result()` function
  - [ ] `create_success_result()` function
  - [ ] `JSON_OUTPUT_MARKER` constant

- [ ] 2.2. Create `blender_lib/constants.py`
  - [ ] TEXTURE_EXTENSIONS list
  - [ ] BLEND_EXTENSIONS list
  - [ ] BACKUP_EXTENSIONS list
  - [ ] TIMEOUT constants (SHORT, MEDIUM, LONG, VERY_LONG)

### Pilot Script
- [ ] 2.3. Update `blender_lib/list_scenes.py` (PILOT)
  - [ ] Add imports from script_utils
  - [ ] Replace `print("JSON_OUTPUT:" + ...)` → `output_json(result)`
  - [ ] Test: Run script, verify JSON output unchanged
  - [ ] Verify no breaking changes

### Update All Blender Scripts
- [ ] 2.4. Update `blender_lib/link_objects.py`
- [ ] 2.5. Update `blender_lib/rename_texture.py`
- [ ] 2.6. Update `blender_lib/rename_objects.py`
- [ ] 2.7. Update `blender_lib/rebase_blend_paths.py`
- [ ] 2.8. Update `blender_lib/list_objects.py`
- [ ] 2.9. Update `blender_lib/move_scene.py`
- [ ] 2.10. Update remaining 6 Blender scripts with JSON_OUTPUT pattern

### Update Service Layer
- [ ] 2.11. Update `services/blender_service.py`
  - [ ] Add `from blender_lib.script_utils import JSON_OUTPUT_MARKER`
  - [ ] Replace `"JSON_OUTPUT:"` → `JSON_OUTPUT_MARKER` in `extract_json_from_output()`

- [ ] 2.12. Update `gui/operations_panel.py` timeouts
  - [ ] Add `from blender_lib.constants import TIMEOUT_MEDIUM, TIMEOUT_LONG`
  - [ ] Replace hardcoded 60, 120, 180 with constants

### Verification
- [ ] 2.13. Test script_utils.py functions in isolation
- [ ] 2.14. Run each modified Blender script, verify JSON output
- [ ] 2.15. Execute all operations in GUI, verify no breaking changes
- [ ] 2.16. Git commit: "Phase 2: Consolidate Blender script utilities"

---

## PHASE 3: Path Utilities Consolidation

**Goal:** Eliminate duplicate path and file scanning functions
**Priority:** CRITICAL
**Risk:** LOW (well-tested utilities)
**Status:** Not Started

### Phase 3a: Path Utilities
- [ ] 3.1. Update `blender_lib/path_operations.py`
  - [ ] Replace duplicate implementation with re-export from `core.path_utils`
  - [ ] Import: `rebase_relative_path`, `resolve_blender_path`, etc.
  - [ ] Add `__all__` export list

- [ ] 3.2. Update `blender_lib/move_scene.py`
  - [ ] Delete lines 11-35 (inline `rebase_relative_path` duplicate)
  - [ ] Add: `from blender_lib.path_operations import rebase_relative_path`

- [ ] 3.3. Test path utilities
  - [ ] Run: `pytest tests/unit/test_path_utils.py`
  - [ ] Test move operations manually

### Phase 3b: File Scanning
- [ ] 3.4. Update `services/filesystem_service.py`
  - [ ] Remove duplicate `find_blend_files` implementation
  - [ ] Add: `from core.file_scanner import find_blend_files`

- [ ] 3.5. Update `blender_lib/rename_texture.py`
  - [ ] Delete lines 11-24 (inline `find_blend_files`)
  - [ ] Add: `from core.file_scanner import find_blend_files`

- [ ] 3.6. Test file scanning
  - [ ] Test file browser in application
  - [ ] Verify .blend file discovery works

### Phase 3c: Ignore Patterns
- [ ] 3.7. Add IGNORE_PATTERNS to `blender_lib/constants.py`
  - [ ] Define list: `.git`, `.venv`, `__pycache__`, etc.

- [ ] 3.8. Update `core/file_scanner.py` to import IGNORE_PATTERNS from constants
- [ ] 3.9. Remove duplicate ignore patterns from `services/filesystem_service.py`
- [ ] 3.10. Test file browser filtering works correctly

### Verification
- [ ] 3.11. Run: `pytest tests/unit/test_path_utils.py`
- [ ] 3.12. Run: `pytest tests/integration/`
- [ ] 3.13. Test move/rename operations, verify paths update correctly
- [ ] 3.14. Git commit: "Phase 3: Consolidate path utilities"

---

## PHASE 4: Split operations_panel.py

**Goal:** Break down 1,860 LOC monolithic file into focused modules
**Priority:** HIGH (architectural improvement)
**Risk:** MEDIUM (large refactor)
**Status:** Not Started

### Setup
- [ ] 4.1. Create directory: `gui/operations/`
- [ ] 4.2. Create `gui/operations/__init__.py` with exports

### Create Base Class
- [ ] 4.3. Create `gui/operations/base_tab.py` (~100 LOC)
  - [ ] BaseOperationTab class
  - [ ] `show_loading_state()` method
  - [ ] `restore_button_state()` method
  - [ ] `show_error()`, `show_warning()`, `show_info()` methods
  - [ ] `ask_confirmation()` method

### Extract Tabs (One at a time, test after each)
- [ ] 4.4. Create `gui/operations/utilities_tab.py` (~100 LOC)
  - [ ] Extract from operations_panel.py lines 369-409
  - [ ] Inherit from BaseOperationTab
  - [ ] Test: Utilities tab works independently

- [ ] 4.5. Create `gui/operations/move_rename_tab.py` (~250 LOC)
  - [ ] Extract from operations_panel.py lines 75-128
  - [ ] Inherit from BaseOperationTab
  - [ ] Test: Move/rename tab works

- [ ] 4.6. Create `gui/operations/rename_objects_tab.py` (~300 LOC)
  - [ ] Extract from operations_panel.py lines 130-227
  - [ ] Inherit from BaseOperationTab
  - [ ] Test: Rename objects tab works

- [ ] 4.7. Create `gui/operations/link_objects_tab.py` (~400 LOC)
  - [ ] Extract from operations_panel.py lines 228-368
  - [ ] Inherit from BaseOperationTab
  - [ ] Test: Link objects tab works

### Update Main Panel
- [ ] 4.8. Refactor `gui/operations_panel.py` to lightweight container (~150 LOC)
  - [ ] Import all tab modules
  - [ ] Create tab instances in `setup_ui()`
  - [ ] Add tabs to QTabWidget
  - [ ] Implement `set_file()` to notify all tabs

### Verification
- [ ] 4.9. Test each tab independently with mocked controller
- [ ] 4.10. Test full operations panel with all tabs
- [ ] 4.11. Manual test: Click through all tabs
- [ ] 4.12. Manual test: Execute each operation type
- [ ] 4.13. Verify no feature regression
- [ ] 4.14. Git commit: "Phase 4: Split operations_panel into focused modules"

---

## Final Verification

- [ ] 5.1. Run full test suite: `pytest tests/`
- [ ] 5.2. Manual smoke test: Launch application
- [ ] 5.3. Manual smoke test: Open project
- [ ] 5.4. Manual smoke test: Move/rename file
- [ ] 5.5. Manual smoke test: Rename objects in .blend
- [ ] 5.6. Manual smoke test: Link objects between .blend files
- [ ] 5.7. Manual smoke test: Clean backup files
- [ ] 5.8. Verify all UI strings can be changed from `gui/ui_strings.py`
- [ ] 5.9. Verify no duplicate code remains (search for patterns)
- [ ] 5.10. Git tag: `refactor-complete-v1.0`

---

## Success Metrics

### Code Quality Improvements
- [ ] ✓ All UI strings defined in single file (`gui/ui_strings.py`)
- [ ] ✓ Zero duplicate message strings
- [ ] ✓ Zero duplicate path utility functions
- [ ] ✓ Zero duplicate file scanning functions
- [ ] ✓ Zero duplicate JSON_OUTPUT patterns
- [ ] ✓ All Blender scripts use shared utilities
- [ ] ✓ No file > 500 LOC

### Functionality Verification
- [ ] ✓ All tests pass
- [ ] ✓ No feature regression
- [ ] ✓ All operations work correctly

### Maintainability Wins
- [ ] ✓ User can change any label from one location
- [ ] ✓ Easier to find and modify code
- [ ] ✓ Clearer code organization
- [ ] ✓ Reduced duplicate code by ~80%

---

## Rollback Points

Each phase has a git commit, allowing rollback to any point:

1. **After Phase 1:** Can rollback UI strings if issues found
2. **After Phase 2:** Can rollback Blender script changes independently
3. **After Phase 3:** Can rollback path utilities consolidation
4. **After Phase 4:** Can rollback panel split and restore monolithic file

---

## Notes & Observations

*(Add notes here as you progress through the refactoring)*

-

---

## Files Created

### Phase 1
- [ ] `gui/ui_strings.py`

### Phase 2
- [ ] `blender_lib/script_utils.py`
- [ ] `blender_lib/constants.py`

### Phase 4
- [ ] `gui/operations/__init__.py`
- [ ] `gui/operations/base_tab.py`
- [ ] `gui/operations/utilities_tab.py`
- [ ] `gui/operations/move_rename_tab.py`
- [ ] `gui/operations/rename_objects_tab.py`
- [ ] `gui/operations/link_objects_tab.py`

---

## Critical Files Modified

### Phase 1 (3 files)
- [ ] `gui/main_window.py`
- [ ] `gui/file_browser.py`
- [ ] `gui/operations_panel.py`

### Phase 2 (15+ files)
- [ ] `blender_lib/list_scenes.py` (PILOT)
- [ ] `blender_lib/link_objects.py`
- [ ] `blender_lib/rename_texture.py`
- [ ] `blender_lib/rename_objects.py`
- [ ] `blender_lib/rebase_blend_paths.py`
- [ ] `blender_lib/list_objects.py`
- [ ] `blender_lib/move_scene.py`
- [ ] Plus 6 more Blender scripts
- [ ] `services/blender_service.py`
- [ ] `gui/operations_panel.py`

### Phase 3 (5 files)
- [ ] `blender_lib/path_operations.py`
- [ ] `blender_lib/move_scene.py`
- [ ] `services/filesystem_service.py`
- [ ] `blender_lib/rename_texture.py`
- [ ] `core/file_scanner.py`

### Phase 4 (1 file)
- [ ] `gui/operations_panel.py` (refactored to container)
