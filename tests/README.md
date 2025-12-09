># Test Suite for Blender Project Manager

This directory contains comprehensive tests for the Blender Project Manager application.

## Test Organization

```
tests/
├── unit/                   # Unit tests (pure logic, no dependencies)
│   ├── test_path_utils.py
│   ├── test_validation.py
│   ├── test_file_scanner.py
│   └── test_operation_planner.py
├── integration/            # Integration tests (require Blender)
│   ├── test_path_rebasing.py
│   └── test_blender_operations.py
├── fixtures/               # Test data and fixtures
│   ├── simple.blend
│   └── textures/
└── conftest.py            # Pytest configuration and shared fixtures

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests (fast, no Blender required)
```bash
pytest -m unit
```

### Run only integration tests (requires Blender)
```bash
pytest -m integration
```

### Run with verbose output
```bash
pytest -v
```

### Run a specific test file
```bash
pytest tests/unit/test_path_utils.py
```

### Run a specific test
```bash
pytest tests/unit/test_path_utils.py::TestRebaseRelativePath::test_rebase_simple_relative_path
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test pure business logic
- No external dependencies (no Blender, no Qt)
- Fast execution
- Always runnable

Examples:
- Path rebasing calculations
- File type detection
- Validation logic
- Directory scanning

### Integration Tests (`@pytest.mark.integration`)
- Test actual Blender operations
- Require Blender installation
- Slower execution
- Skipped if Blender not found

Examples:
- Rebasing paths in real .blend files
- Linking objects between files
- Renaming objects in .blend files

## Architecture

The test suite follows a clean architecture approach:

1. **Core Module** (`core/`)
   - Pure Python business logic
   - No dependencies on bpy or Qt
   - Easily testable with unit tests

2. **Blender Scripts** (`blender_lib/`)
   - Thin wrappers around core logic
   - Handle bpy interaction
   - Tested with integration tests

3. **Test Fixtures**
   - Shared test data in `fixtures/`
   - Pytest fixtures in `conftest.py`
   - Factory fixtures for creating test files

## Writing New Tests

### Unit Test Template

```python
import pytest
from core.module_name import function_name


class TestFunctionName:
    """Tests for function_name."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = function_name(input_data)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge case handling."""
        result = function_name(edge_case_input)
        assert result == expected_edge_output
```

### Integration Test Template

```python
import pytest
from pathlib import Path


@pytest.mark.integration
class TestBlenderOperation:
    """Integration tests for Blender operation."""

    def test_operation(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test the operation with real Blender."""
        # Create test files
        # Run Blender script
        # Verify results
        pass
```

## Fixtures

### Path Fixtures
- `tmp_path` - Temporary directory for each test (pytest built-in)
- `fixtures_dir` - Directory containing test fixtures
- `test_data_dir` - Temporary copy of fixtures for each test
- `empty_project_dir` - Empty project directory

### Blender Fixtures
- `blender_path` - Path to Blender executable (None if not found)
- `skip_if_no_blender` - Skip test if Blender not available
- `create_test_blend_file` - Factory for creating .blend files
- `create_test_texture` - Factory for creating texture files

### Project Fixtures
- `sample_project_structure` - Sample project directory structure

## Coverage

To run tests with coverage:

```bash
pytest --cov=core --cov=blender_lib --cov=services
```

Generate HTML coverage report:

```bash
pytest --cov=core --cov=blender_lib --cov=services --cov-report=html
```

## Continuous Integration

Tests are designed to run in CI environments:
- Unit tests always run
- Integration tests run only if Blender is available
- Use `pytest --tb=short` for concise output

## Troubleshooting

### "Blender not found"
Integration tests require Blender to be installed and in PATH.

On macOS:
```bash
export PATH="/Applications/Blender.app/Contents/MacOS:$PATH"
```

### "Module not found"
Ensure you're running pytest from the project root:
```bash
cd blender_project_manager
pytest
```

### Slow tests
Use `-m unit` to run only fast unit tests during development.
