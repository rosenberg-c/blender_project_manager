# Testing Guide

This document explains the testing architecture and how to write and run tests for the Blender Project Manager.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [CI/CD Integration](#cicd-integration)

## Overview

The test suite is designed to be:
- **Fast**: Unit tests run without external dependencies
- **Reliable**: No complex mocks or test doubles
- **Comprehensive**: Covers both pure logic and Blender integration
- **Maintainable**: Clear separation between unit and integration tests

### Test Statistics

- **Unit Tests**: ~50+ tests for pure business logic
- **Integration Tests**: ~15+ tests for Blender operations
- **Code Coverage**: Targeting 80%+ for core modules

## Architecture

### Core Module Pattern

To make the codebase testable without convoluted mocks, we follow a simple pattern:

```
┌─────────────────┐
│  Blender Script │  ← Thin wrapper, calls core + bpy
│  (blender_lib)  │
└────────┬────────┘
         │
         ├──────────────────────┐
         ↓                      ↓
┌─────────────────┐    ┌─────────────────┐
│   Core Module   │    │   bpy (Blender) │
│   (pure logic)  │    │   (external)    │
└────────┬────────┘    └─────────────────┘
         │
         ↓
   ┌────────────┐
   │ Unit Tests │
   └────────────┘
```

**Key Principles:**

1. **Extract Pure Logic**: Business logic goes in `core/` module
   - No `bpy` imports
   - No Qt imports
   - Just Python standard library

2. **Keep Scripts Thin**: Blender scripts are minimal wrappers
   - Parse arguments
   - Call core functions
   - Use bpy to execute changes
   - Return results as JSON

3. **Test Both Layers**:
   - Unit tests for `core/` (fast, no dependencies)
   - Integration tests for `blender_lib/` (slower, requires Blender)

### Directory Structure

```
blender_project_manager/
├── core/                          # Pure business logic (testable)
│   ├── path_utils.py             # Path manipulation
│   ├── validation.py             # Input validation
│   ├── file_scanner.py           # File discovery
│   └── operation_planner.py      # Operation planning
├── blender_lib/                   # Blender scripts (thin wrappers)
│   ├── rebase_blend_paths.py    # Uses core.path_utils
│   ├── rename_objects.py         # Uses core.file_scanner
│   └── link_objects.py           # Uses core.validation
├── tests/
│   ├── unit/                     # Unit tests (no dependencies)
│   │   ├── test_path_utils.py
│   │   ├── test_validation.py
│   │   ├── test_file_scanner.py
│   │   └── test_operation_planner.py
│   ├── integration/              # Integration tests (require Blender)
│   │   └── test_path_rebasing.py
│   ├── fixtures/                 # Test data
│   └── conftest.py              # Shared fixtures
└── pytest.ini                    # Pytest configuration
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
./run_tests.sh

# Or use pytest directly
pytest
```

### Specific Test Categories

```bash
# Run only unit tests (fast, no Blender needed)
./run_tests.sh unit

# Run only integration tests (requires Blender)
./run_tests.sh integration

# Run with coverage report
./run_tests.sh coverage
```

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_path_utils.py

# Run a specific test class
pytest tests/unit/test_path_utils.py::TestRebaseRelativePath

# Run a specific test
pytest tests/unit/test_path_utils.py::TestRebaseRelativePath::test_rebase_simple_relative_path

# Run tests matching a pattern
pytest -k "test_rebase"
```

### Verbose Output

```bash
# More detailed output
pytest -v

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

## Writing Tests

### Unit Test Example

Unit tests are for pure functions in the `core/` module:

```python
"""tests/unit/test_my_module.py"""

import pytest
from pathlib import Path
from core.my_module import my_function


class TestMyFunction:
    """Tests for my_function."""

    def test_basic_case(self):
        """Test basic functionality."""
        result = my_function("input")
        assert result == "expected_output"

    def test_with_path(self, tmp_path):
        """Test with file system."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = my_function(test_file)
        assert result is not None

    def test_edge_case(self):
        """Test edge case handling."""
        result = my_function("")
        assert result == ""

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            my_function(None)
```

### Integration Test Example

Integration tests run actual Blender scripts:

```python
"""tests/integration/test_my_operation.py"""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
class TestMyBlenderOperation:
    """Integration tests for Blender operation."""

    def test_operation(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test operation with real Blender."""
        # Create test .blend file
        blend_file = tmp_path / "test.blend"

        setup_script = f"""
import bpy
# ... setup code ...
bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_script)

        # Run setup
        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0
        assert blend_file.exists()

        # Run actual operation
        operation_script = Path(__file__).parent.parent.parent / "blender_lib" / "my_script.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(operation_script),
                "--",
                "--arg1", "value1",
                "--dry-run", "true"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Verify results
        assert result.returncode == 0

        # Parse JSON output
        output = result.stdout
        json_start = output.find("JSON_OUTPUT:") + len("JSON_OUTPUT:")
        json_text = output[json_start:].strip().split('\n')[0]
        data = json.loads(json_text)

        assert data["success"] is True
```

### Using Fixtures

Pytest provides powerful fixtures:

```python
def test_with_fixtures(
    tmp_path,              # Temporary directory (pytest built-in)
    fixtures_dir,          # Our test fixtures directory
    test_data_dir,         # Copy of fixtures in tmp location
    sample_project_structure,  # Pre-built project structure
    blender_path,          # Path to Blender (or None)
    skip_if_no_blender     # Skip if Blender not available
):
    """Test using various fixtures."""
    # tmp_path is unique for each test
    test_file = tmp_path / "test.txt"
    test_file.write_text("data")

    # test_data_dir has copies of fixtures
    blend_file = test_data_dir / "simple.blend"
    assert blend_file.exists()

    # sample_project_structure is a complete project
    scenes_dir = sample_project_structure / "scenes"
    assert scenes_dir.exists()
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_pure_logic():
    """Fast test with no dependencies."""
    pass

@pytest.mark.integration
def test_with_blender():
    """Requires Blender installation."""
    pass

@pytest.mark.slow
def test_long_running():
    """Test that takes >1 second."""
    pass

@pytest.mark.file_operations
def test_file_manipulation():
    """Test that creates/modifies files."""
    pass
```

Run tests by marker:

```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

## Test Coverage

### Measuring Coverage

```bash
# Run with coverage
pytest --cov=core --cov=blender_lib --cov=services

# Generate HTML report
pytest --cov=core --cov=blender_lib --cov=services --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Goals

- **Core modules**: 90%+ coverage
- **Blender scripts**: 70%+ coverage (integration tests)
- **Services**: 80%+ coverage
- **Overall**: 80%+ coverage

### What to Test

**High Priority:**
- All functions in `core/` module
- Critical paths in Blender operations
- Error handling and edge cases
- Validation logic

**Medium Priority:**
- UI logic (with pytest-qt)
- File system operations
- Configuration management

**Low Priority:**
- One-line property accessors
- Simple __init__ methods
- Logging statements

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run unit tests
      run: pytest -m unit --cov=core --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2

  integration:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Install Blender
      run: |
        sudo snap install blender --classic

    - name: Run integration tests
      run: pytest -m integration
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Run unit tests before commit
echo "Running unit tests..."
pytest -m unit -q

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed. Commit aborted."
    exit 1
fi

echo "✓ Unit tests passed"
exit 0
```

## Best Practices

### DO:
- ✅ Write unit tests for all `core/` modules
- ✅ Use `tmp_path` fixture for file operations
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Keep tests focused (one concept per test)
- ✅ Use pytest fixtures for common setup

### DON'T:
- ❌ Write integration tests for pure logic (use unit tests)
- ❌ Test implementation details
- ❌ Share state between tests
- ❌ Use complex mocking (refactor code instead)
- ❌ Skip cleanup (use fixtures and tmp_path)
- ❌ Test external libraries (trust they work)

### Test Naming Convention

```python
def test_<what>_<when>_<expected>():
    """Test that <specific behavior>."""
```

Examples:
```python
def test_rebase_path_when_moved_to_deeper_directory_returns_longer_path():
    """Test that moving to deeper directory increases path length."""

def test_validate_link_when_names_conflict_returns_error():
    """Test that naming conflicts are detected."""

def test_find_blend_files_when_directory_empty_returns_empty_list():
    """Test that empty directories return no files."""
```

## Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'core'`
**Solution**: Run pytest from project root directory

**Problem**: Integration tests skipped
**Solution**: Install Blender and ensure it's in PATH

**Problem**: Tests fail with "Permission denied"
**Solution**: Tests are modifying files outside tmp_path - use fixtures

**Problem**: Slow test execution
**Solution**: Run only unit tests during development: `pytest -m unit`

**Problem**: Fixture not found
**Solution**: Check `conftest.py` is present in `tests/` directory

## Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
