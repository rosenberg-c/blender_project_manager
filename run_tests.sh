#!/bin/bash

# Test runner script for Blender Project Manager

set -e

echo "=== Blender Project Manager Test Suite ==="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest not found. Install with:"
    echo "  pip install -r requirements-test.txt"
    exit 1
fi

# Check for Blender
if command -v blender &> /dev/null; then
    BLENDER_PATH=$(which blender)
    echo "✓ Blender found at: $BLENDER_PATH"
else
    # Check macOS location
    if [ -f "/Applications/Blender.app/Contents/MacOS/Blender" ]; then
        echo "✓ Blender found at: /Applications/Blender.app/Contents/MacOS/Blender"
    else
        echo "⚠ Warning: Blender not found. Integration tests will be skipped."
    fi
fi

echo ""
echo "Running tests..."
echo ""

# Default: run all tests
if [ -z "$1" ]; then
    pytest -v
# Run specific test category
elif [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    pytest -v -m unit
elif [ "$1" = "integration" ]; then
    echo "Running integration tests only..."
    pytest -v -m integration
elif [ "$1" = "coverage" ]; then
    echo "Running tests with coverage..."
    pytest --cov=core --cov=blender_lib --cov=services --cov-report=term --cov-report=html
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
else
    # Run specific test file or pattern
    pytest -v "$@"
fi

echo ""
echo "=== Tests Complete ==="
