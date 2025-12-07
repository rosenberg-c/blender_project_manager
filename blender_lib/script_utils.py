"""Shared utilities for Blender scripts.

This module provides common functions used across all Blender scripts to eliminate
code duplication and ensure consistent error handling and output formatting.
"""

import json
import sys
from typing import Any, Dict


# Standard JSON output marker for parsing script results
JSON_OUTPUT_MARKER = "JSON_OUTPUT:"


def output_json(data: Dict[str, Any]) -> None:
    """Output JSON with standard marker for parsing by the main application.

    Args:
        data: Dictionary to output as JSON
    """
    print(f"{JSON_OUTPUT_MARKER}{json.dumps(data, indent=2)}")


def create_error_result(error_message: str, **kwargs) -> Dict[str, Any]:
    """Create a standard error result dictionary.

    Args:
        error_message: The error message to include
        **kwargs: Additional fields to include in the result

    Returns:
        Dictionary with error result structure
    """
    result = {
        "success": False,
        "error": error_message,
        "errors": [error_message],
        "warnings": []
    }
    result.update(kwargs)
    return result


def create_success_result(**kwargs) -> Dict[str, Any]:
    """Create a standard success result dictionary.

    Args:
        **kwargs: Fields to include in the result

    Returns:
        Dictionary with success result structure
    """
    result = {
        "success": True,
        "error": "",
        "errors": [],
        "warnings": []
    }
    result.update(kwargs)
    return result


def exit_with_error(error_message: str, **kwargs) -> None:
    """Output an error result and exit.

    Args:
        error_message: The error message
        **kwargs: Additional fields to include in the result
    """
    output_json(create_error_result(error_message, **kwargs))
    sys.exit(1)


def exit_with_success(**kwargs) -> None:
    """Output a success result and exit.

    Args:
        **kwargs: Fields to include in the result
    """
    output_json(create_success_result(**kwargs))
    sys.exit(0)
