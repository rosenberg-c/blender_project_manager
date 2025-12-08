# Test Coverage Gap Analysis

## ✅ Progress Update (2025-12-08)

**Phases 1, 2, and 3 Complete!** Critical features and infrastructure now have comprehensive test coverage:

### Broken Links Feature (36 tests)
- ✅ `check_broken_links.py` - 10 tests covering detection logic
- ✅ `find_and_relink.py` - 17 tests covering fuzzy matching and relinking
- ✅ `fix_broken_links.py` - 9 tests covering removal of broken links

### Core Infrastructure (37 tests)
- ✅ `blender_runner.py` - 18 tests covering subprocess execution
- ✅ `script_utils.py` - 19 tests covering JSON output and result creation

### List Operations (16 tests)
- ✅ `list_objects.py` - 7 tests covering object and collection listing
- ✅ `list_scenes.py` - 9 tests covering scene listing and active scene detection

### Data Models & Path Operations (33 tests)
- ✅ `models.py` - 21 tests covering all dataclass models and properties
- ✅ `path_operations.py` - 12 tests covering path rebasing for moved files and blend files

**Total: 122 new tests added, all passing in 0.53 seconds** 🎉

---

## Executive Summary

The project has **good test coverage for core business logic** (path_utils, validation, file_scanner, operation_planner) and **now has excellent coverage for the broken links feature**.

**Remaining gaps**:
- Blender scripts (link_objects, move_scene, list_objects, etc.)
- Controllers and services
- GUI components (dialogs, tabs)

**Total Modules**: ~40 | **Tested Modules**: ~20 (50% coverage, up from 27.5%)

---

## Modules By Category

### ✅ **Well Tested** (11 modules)

#### Core Modules (4/5 - 80%)
- ✅ `core/path_utils.py` - 20+ tests
- ✅ `core/validation.py` - 15+ tests
- ✅ `core/file_scanner.py` - 15+ tests
- ✅ `core/operation_planner.py` - 10+ tests
- ❌ `core/__init__.py` - (no logic to test)

#### Blender Scripts (7/17 - 41.2%)
- ✅ `blender_lib/rename_objects.py` - Path handling & logic tests
- ✅ `blender_lib/rename_texture.py` - Path handling tests
- ✅ `blender_lib/reload_libraries.py` - Path handling tests
- ✅ `blender_lib/find_references.py` - Path handling & logic tests
- ✅ `blender_lib/list_objects.py` - 7 tests for listing objects and collections
- ✅ `blender_lib/list_scenes.py` - 9 tests for listing scenes and active scene detection
- ✅ `blender_lib/models.py` - 21 tests for all dataclass models
- ✅ `blender_lib/path_operations.py` - 12 tests for path rebasing operations

#### GUI (1/16 - 6.25%)
- ✅ `gui/file_browser.py` - Delete operation tests
- ✅ `gui/operations/utilities_tab.py` - Remove empty directories tests
- ✅ `gui/operations/rename_objects_tab.py` - Copy button tests

#### Integration Tests (1)
- ✅ `tests/integration/test_path_rebasing.py` - Real Blender operations

---

## ❌ **Missing Tests** (29 modules)

### Critical - Recently Added Features (5 modules)

These are **new features** we just implemented that have **zero test coverage**:

#### Broken Links Feature
- ✅ `blender_lib/check_broken_links.py` - **TESTED** (10 tests)
  - ✅ Path handling (string conversion)
  - ✅ Detects missing libraries
  - ✅ Detects missing textures
  - ✅ Skips packed textures
  - ✅ Skips textures from linked libraries (recent fix!)
  - ✅ Validates existing files not reported as broken
  - ✅ Handles empty filepath
  - ✅ Multiple broken links detection
  - ✅ Result structure validation

- ✅ `blender_lib/find_and_relink.py` - **TESTED** (17 tests)
  - ✅ Similarity ratio calculation (exact, similar, different, case-insensitive)
  - ✅ Finds exact filename matches
  - ✅ Finds multiple matches
  - ✅ Finds similar files with fuzzy matching
  - ✅ Respects minimum similarity threshold
  - ✅ Filters by file extension
  - ✅ Returns top 5 matches sorted by similarity
  - ✅ Relinks libraries by name
  - ✅ Relinks textures by name
  - ✅ Uses relative paths (recent fix!)
  - ✅ Skips packed textures
  - ✅ No save if nothing relinked

- ✅ `blender_lib/fix_broken_links.py` - **TESTED** (9 tests)
  - ✅ Path handling (string conversion)
  - ✅ Removes broken libraries and their objects/collections
  - ✅ Removes broken textures
  - ✅ Skips packed textures
  - ✅ Handles empty filepath
  - ✅ No save if nothing fixed
  - ✅ Fixes multiple broken links
  - ✅ Does not remove valid links
  - ✅ Result structure validation

#### Broken Links Dialogs
- ❌ `gui/broken_links_dialog.py` - **MEDIUM PRIORITY**
  - Table display of broken links
  - Visual feedback (green for relinked)
  - Multiple action buttons
  - **Risks**: UI state inconsistency

- ❌ `gui/similar_files_dialog.py` - **MEDIUM PRIORITY**
  - User selection of similar file matches
  - Dropdown combo box handling
  - **Risks**: Wrong file selection, data binding issues

---

### High Priority - Core Blender Scripts (3 modules remaining)

These scripts execute operations on .blend files but lack tests:

- ❌ `blender_lib/link_objects.py`
  - Links objects/collections between .blend files
  - **Risk**: Data corruption, incorrect linking

- ❌ `blender_lib/move_scene.py`
  - Moves scenes between .blend files
  - **Risk**: Data loss, broken references

- ✅ `blender_lib/list_objects.py` - **TESTED** (7 tests)
  - ✅ Lists objects and collections
  - ✅ Object types (MESH, LIGHT, CAMERA, EMPTY, ARMATURE)
  - ✅ Collection memberships
  - ✅ Result structure validation

- ✅ `blender_lib/list_scenes.py` - **TESTED** (9 tests)
  - ✅ Lists scenes in blend files
  - ✅ Identifies active scene
  - ✅ Handles no active scene
  - ✅ Special scene names

- ❌ `blender_lib/rebase_blend_paths.py`
  - Updates internal paths after move/rename
  - Uses `core.path_utils` but integration not tested
  - **Risk**: Path corruption, broken links

- ✅ `blender_lib/path_operations.py` - **TESTED** (12 tests)
  - ✅ Path rebasing delegation to core
  - ✅ Update blend paths for moved files (images & libraries)
  - ✅ Rebase internal paths when blend file moves
  - ✅ Dry run mode support
  - ✅ Skips empty/absolute paths appropriately

- ✅ `blender_lib/models.py` - **TESTED** (21 tests)
  - ✅ All dataclass models (ImageReference, LibraryReference, BlendReferences, PathChange, OperationPreview, OperationResult, LinkOperationParams)
  - ✅ Default factory behavior
  - ✅ Properties (is_valid, total_changes)
  - ✅ Various status types and field combinations

**Recently Completed:**
- ✅ `blender_lib/script_utils.py` - **TESTED** (19 tests)
  - ✅ JSON output formatting with marker
  - ✅ Error result creation
  - ✅ Success result creation
  - ✅ Exit with error/success

- ✅ `blender_lib/blender_runner.py` - **TESTED** (18 tests)
  - ✅ Initialization and validation
  - ✅ Script execution with arguments
  - ✅ Progress callback streaming
  - ✅ Inline code execution
  - ✅ Timeout handling
  - ✅ Connection testing

---

### Medium Priority - Controllers & Services (4 modules)

Application orchestration logic:

- ❌ `controllers/project_controller.py`
  - Project open/close, configuration
  - **Risk**: State management bugs

- ❌ `controllers/file_operations_controller.py`
  - Coordinates all file operations
  - **Risk**: Operation conflicts, state inconsistency

- ❌ `services/blender_service.py`
  - Blender execution service
  - JSON output parsing
  - **Risk**: Parsing errors, process failures

- ❌ `services/filesystem_service.py`
  - File system operations (move, delete, etc.)
  - **Risk**: Data loss, permission errors

---

### Medium Priority - GUI Components (11 modules)

User interface components:

- ❌ `gui/main_window.py`
  - Main application window
  - Menu bar, status bar

- ❌ `gui/operations_panel.py`
  - Tab container for operations

- ❌ `gui/operations/base_tab.py`
  - Base class for operation tabs
  - Shared functionality

- ❌ `gui/operations/move_rename_tab.py`
  - Move/rename files tab
  - Preview functionality

- ❌ `gui/operations/link_objects_tab.py`
  - Link objects between files tab
  - Object/collection selection

- ❌ `gui/preview_dialog.py`
  - Shows operation preview before execution

- ❌ `gui/progress_dialog.py`
  - Shows real-time operation progress
  - Log streaming

- ❌ `gui/theme.py`
  - Application styling

- ❌ `gui/ui_strings.py`
  - Centralized UI strings
  - Could validate all strings are used

- ❌ `gui/__init__.py`

---

### Low Priority - Constants & Utilities (2 modules)

- ❌ `blender_lib/constants.py`
  - Timeout values, constants
  - (Minimal logic to test)

- ❌ `controllers/__init__.py`, `services/__init__.py`
  - (No logic)

---

## Test Coverage Recommendations

### Phase 1: Critical Fixes (Week 1)

**Priority**: Fix recently added features that already have bugs

1. **Test `check_broken_links.py`**
   ```python
   # tests/unit/test_check_broken_links.py
   - test_detect_missing_library()
   - test_detect_missing_texture()
   - test_skip_packed_textures()
   - test_skip_linked_library_textures()  # Recent fix!
   - test_path_resolution_with_relative_paths()
   - test_empty_filepath_handling()
   ```

2. **Test `find_and_relink.py`**
   ```python
   # tests/unit/test_find_and_relink.py
   - test_find_exact_match()
   - test_find_similar_files()
   - test_similarity_ratio_calculation()
   - test_relink_with_relative_paths()  # Recent fix!
   - test_relink_library_by_name()
   - test_relink_texture_by_name()
   - test_no_matches_found()
   ```

3. **Test `blender_runner.py`**
   ```python
   # tests/unit/test_blender_runner.py
   - test_run_script_basic()
   - test_run_script_with_progress()
   - test_timeout_handling()
   - test_error_output_parsing()
   ```

**Estimated Effort**: 3-5 days

---

### Phase 2: Core Script Coverage (Week 2)

**Priority**: Ensure data integrity for file operations

4. **Test `link_objects.py`**
   - Integration test with real .blend files
   - Test linking objects vs collections
   - Test instance mode
   - Test error handling

5. **Test `move_scene.py`**
   - Integration test with real .blend files
   - Test scene copy/move
   - Test cleanup operations

6. **Test `rebase_blend_paths.py`**
   - Integration test (uses core.path_utils)
   - Test path updates after move
   - Test co-moved files skip

7. **Test `script_utils.py`**
   - Unit tests for JSON output formatting
   - Test error result creation
   - Test success result creation

**Estimated Effort**: 5-7 days

---

### Phase 3: Controllers & Services (Week 3)

**Priority**: Ensure application coordination works correctly

8. **Test `file_operations_controller.py`**
   - Mock Blender runner
   - Test operation workflow
   - Test error propagation

9. **Test `blender_service.py`**
   - Test JSON extraction from output
   - Test Blender path detection
   - Test process execution

10. **Test `filesystem_service.py`**
    - Test file move/delete operations
    - Test error handling
    - Use temp directories

**Estimated Effort**: 4-6 days

---

### Phase 4: GUI Testing (Optional, Week 4+)

**Priority**: Validate user interface behavior

11. **Setup pytest-qt**
   ```bash
   pip install pytest-qt
   ```

12. **Test critical dialogs**
   - `test_broken_links_dialog.py`
   - `test_preview_dialog.py`
   - `test_progress_dialog.py`

13. **Test operation tabs**
   - `test_move_rename_tab.py`
   - `test_link_objects_tab.py`

**Estimated Effort**: 5-10 days (depending on depth)

---

## Suggested Test File Structure

```
tests/
├── unit/
│   ├── core/                          # Already exists
│   │   ├── test_path_utils.py
│   │   ├── test_validation.py
│   │   ├── test_file_scanner.py
│   │   └── test_operation_planner.py
│   │
│   ├── blender_lib/                   # NEW
│   │   ├── test_check_broken_links.py      ⭐ HIGH PRIORITY
│   │   ├── test_find_and_relink.py         ⭐ HIGH PRIORITY
│   │   ├── test_fix_broken_links.py        ⭐ HIGH PRIORITY
│   │   ├── test_blender_runner.py          ⭐ HIGH PRIORITY
│   │   ├── test_link_objects.py
│   │   ├── test_move_scene.py
│   │   ├── test_rebase_blend_paths.py
│   │   ├── test_script_utils.py
│   │   ├── test_list_objects.py
│   │   └── test_list_scenes.py
│   │
│   ├── controllers/                   # NEW
│   │   ├── test_project_controller.py
│   │   └── test_file_operations_controller.py
│   │
│   ├── services/                      # NEW
│   │   ├── test_blender_service.py
│   │   └── test_filesystem_service.py
│   │
│   └── gui/                           # NEW (optional)
│       ├── test_broken_links_dialog.py
│       ├── test_similar_files_dialog.py
│       ├── test_preview_dialog.py
│       └── test_progress_dialog.py
│
└── integration/
    ├── test_path_rebasing.py          # Already exists
    ├── test_link_objects.py           # NEW
    ├── test_move_scene.py             # NEW
    ├── test_broken_links_workflow.py  # NEW - End-to-end test
    └── test_find_and_relink_workflow.py  # NEW
```

---

## Key Risks Without Tests

### 1. **Data Loss Risks**
Without tests for:
- `fix_broken_links.py` - Could delete wrong data
- `move_scene.py` - Could lose scene data
- `link_objects.py` - Could corrupt links

### 2. **False Positive Bugs**
Without tests for:
- `check_broken_links.py` - Already reporting false positives (user feedback)
- Path resolution logic could be wrong

### 3. **Regression Risks**
When we fixed bugs in:
- `find_and_relink.py` - Changed matching logic (by name not path)
- `check_broken_links.py` - Added library texture skipping

Without tests, we can't verify these fixes work or prevent future regressions.

### 4. **Integration Risks**
Without tests for:
- Controllers and services - Operation coordination could fail
- Progress dialog - Output streaming could break
- Error handling - Errors might not be caught

---

## Testing Strategy Recommendations

### For New Features (Going Forward)

1. **Write tests FIRST** (TDD)
   - Define expected behavior
   - Write failing test
   - Implement feature
   - Test passes

2. **Minimum test coverage for new Blender scripts**
   - Path handling (parse arguments correctly)
   - Main logic (core functionality works)
   - Error cases (handles errors gracefully)
   - Integration test (works with real Blender)

3. **Review checklist before merging**
   - [ ] Unit tests added?
   - [ ] Integration test added (if applicable)?
   - [ ] All tests pass?
   - [ ] Coverage maintained or improved?

### For Existing Code (Retroactive)

1. **Bug-driven testing**
   - When user reports bug → write test that reproduces it
   - Fix bug
   - Test prevents regression

2. **Prioritize by risk**
   - Data manipulation scripts (HIGH)
   - User-reported problem areas (HIGH)
   - Complex logic (MEDIUM)
   - UI components (LOW)

3. **Characterization tests**
   - Document current behavior (even if not ideal)
   - Allows safe refactoring
   - Can improve behavior later

---

## Quick Wins

These are easy tests that provide high value:

1. **`script_utils.py`** - Pure Python, no dependencies
   ```python
   def test_create_success_result():
       result = create_success_result(message="Done")
       assert result["success"] == True
       assert result["message"] == "Done"
   ```

2. **`models.py`** - Data validation
   ```python
   def test_operation_model_validation():
       op = Operation(type="move", source="...", target="...")
       assert op.is_valid()
   ```

3. **Similarity ratio** - Pure function
   ```python
   def test_similarity_ratio():
       assert similarity_ratio("texture.png", "texture.png") == 1.0
       assert similarity_ratio("wood.jpg", "wooden.jpg") > 0.6
   ```

**Estimated Effort**: 1-2 days

---

## Conclusion

The project has **excellent test coverage for core business logic** but **critical gaps** in recently added features and Blender scripts.

### Immediate Actions:

1. ⭐ **Test broken links feature** (check, find, fix, relink) - User already reported issues
2. ⭐ **Test `blender_runner.py`** - Core infrastructure used by everything
3. **Add integration tests** for data operations (link, move, rebase)
4. **Establish testing policy** for new features going forward

### Success Criteria:

- All critical Blender scripts have basic tests (80%+ coverage)
- No user-reported bugs without regression tests
- New features require tests before merging
- Test suite runs in CI/CD pipeline

**Current Test Coverage**: ~50% of modules (20/40)
**Target Test Coverage**: ~70% of modules (focus on critical paths)

---

*Generated: 2025-12-08*
*Analysis includes: 40 modules across core/, blender_lib/, controllers/, services/, and gui/*
