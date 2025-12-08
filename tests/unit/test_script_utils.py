"""Unit tests for script_utils module."""

import json
import sys
from unittest.mock import patch, call
import pytest


class TestOutputJson:
    """Tests for output_json function."""

    def test_output_json_prints_with_marker(self, capsys):
        """Test that output_json prints JSON with the standard marker."""
        from blender_lib.script_utils import output_json, JSON_OUTPUT_MARKER

        data = {"key": "value", "number": 42}

        output_json(data)

        captured = capsys.readouterr()
        assert JSON_OUTPUT_MARKER in captured.out
        assert '"key": "value"' in captured.out
        assert '"number": 42' in captured.out

    def test_output_json_formats_as_json(self, capsys):
        """Test that output is valid JSON."""
        from blender_lib.script_utils import output_json, JSON_OUTPUT_MARKER

        data = {
            "success": True,
            "items": ["a", "b", "c"],
            "count": 3
        }

        output_json(data)

        captured = capsys.readouterr()
        # Extract JSON from output (after marker)
        json_str = captured.out.split(JSON_OUTPUT_MARKER)[1]
        parsed = json.loads(json_str)

        assert parsed == data

    def test_output_json_handles_nested_data(self, capsys):
        """Test that nested dictionaries are handled correctly."""
        from blender_lib.script_utils import output_json

        data = {
            "outer": {
                "inner": {
                    "deep": "value"
                }
            }
        }

        output_json(data)

        captured = capsys.readouterr()
        assert "outer" in captured.out
        assert "inner" in captured.out
        assert "deep" in captured.out


class TestCreateErrorResult:
    """Tests for create_error_result function."""

    def test_create_error_result_basic(self):
        """Test basic error result creation."""
        from blender_lib.script_utils import create_error_result

        result = create_error_result("Something went wrong")

        assert result["success"] is False
        assert result["error"] == "Something went wrong"
        assert "Something went wrong" in result["errors"]
        assert result["warnings"] == []

    def test_create_error_result_with_kwargs(self):
        """Test that additional kwargs are included in result."""
        from blender_lib.script_utils import create_error_result

        result = create_error_result(
            "Error occurred",
            file="test.blend",
            line_number=42
        )

        assert result["success"] is False
        assert result["error"] == "Error occurred"
        assert result["file"] == "test.blend"
        assert result["line_number"] == 42

    def test_create_error_result_with_traceback(self):
        """Test error result with traceback."""
        from blender_lib.script_utils import create_error_result

        result = create_error_result(
            "Exception occurred",
            traceback="Traceback (most recent call last):\n  File..."
        )

        assert result["success"] is False
        assert "traceback" in result
        assert "Traceback" in result["traceback"]

    def test_create_error_result_structure(self):
        """Test that error result has all required fields."""
        from blender_lib.script_utils import create_error_result

        result = create_error_result("Test error")

        # Verify all standard fields exist
        assert "success" in result
        assert "error" in result
        assert "errors" in result
        assert "warnings" in result
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)


class TestCreateSuccessResult:
    """Tests for create_success_result function."""

    def test_create_success_result_basic(self):
        """Test basic success result creation."""
        from blender_lib.script_utils import create_success_result

        result = create_success_result()

        assert result["success"] is True
        assert result["error"] == ""
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_create_success_result_with_data(self):
        """Test success result with additional data."""
        from blender_lib.script_utils import create_success_result

        result = create_success_result(
            message="Operation completed",
            items_processed=10,
            duration=5.2
        )

        assert result["success"] is True
        assert result["message"] == "Operation completed"
        assert result["items_processed"] == 10
        assert result["duration"] == 5.2

    def test_create_success_result_with_warnings(self):
        """Test that warnings can be included in success result."""
        from blender_lib.script_utils import create_success_result

        result = create_success_result(
            warnings=["Warning 1", "Warning 2"]
        )

        assert result["success"] is True
        assert len(result["warnings"]) == 2
        assert "Warning 1" in result["warnings"]

    def test_create_success_result_structure(self):
        """Test that success result has all required fields."""
        from blender_lib.script_utils import create_success_result

        result = create_success_result()

        # Verify all standard fields exist
        assert "success" in result
        assert "error" in result
        assert "errors" in result
        assert "warnings" in result
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)


class TestExitWithError:
    """Tests for exit_with_error function."""

    def test_exit_with_error_calls_sys_exit(self, capsys):
        """Test that exit_with_error calls sys.exit(1)."""
        from blender_lib.script_utils import exit_with_error

        with pytest.raises(SystemExit) as exc_info:
            exit_with_error("Test error")

        assert exc_info.value.code == 1

    def test_exit_with_error_outputs_json(self, capsys):
        """Test that exit_with_error outputs JSON before exiting."""
        from blender_lib.script_utils import exit_with_error, JSON_OUTPUT_MARKER

        with pytest.raises(SystemExit):
            exit_with_error("Test error", extra_field="value")

        captured = capsys.readouterr()
        assert JSON_OUTPUT_MARKER in captured.out
        assert "Test error" in captured.out
        assert "extra_field" in captured.out

    def test_exit_with_error_creates_error_result(self, capsys):
        """Test that exit_with_error creates proper error result."""
        from blender_lib.script_utils import exit_with_error, JSON_OUTPUT_MARKER

        with pytest.raises(SystemExit):
            exit_with_error("Error message", code=500)

        captured = capsys.readouterr()
        json_str = captured.out.split(JSON_OUTPUT_MARKER)[1]
        result = json.loads(json_str)

        assert result["success"] is False
        assert result["error"] == "Error message"
        assert result["code"] == 500


class TestExitWithSuccess:
    """Tests for exit_with_success function."""

    def test_exit_with_success_calls_sys_exit(self, capsys):
        """Test that exit_with_success calls sys.exit(0)."""
        from blender_lib.script_utils import exit_with_success

        with pytest.raises(SystemExit) as exc_info:
            exit_with_success()

        assert exc_info.value.code == 0

    def test_exit_with_success_outputs_json(self, capsys):
        """Test that exit_with_success outputs JSON before exiting."""
        from blender_lib.script_utils import exit_with_success, JSON_OUTPUT_MARKER

        with pytest.raises(SystemExit):
            exit_with_success(message="Success!", count=42)

        captured = capsys.readouterr()
        assert JSON_OUTPUT_MARKER in captured.out
        assert "Success!" in captured.out
        assert "count" in captured.out

    def test_exit_with_success_creates_success_result(self, capsys):
        """Test that exit_with_success creates proper success result."""
        from blender_lib.script_utils import exit_with_success, JSON_OUTPUT_MARKER

        with pytest.raises(SystemExit):
            exit_with_success(result="done", items=5)

        captured = capsys.readouterr()
        json_str = captured.out.split(JSON_OUTPUT_MARKER)[1]
        result = json.loads(json_str)

        assert result["success"] is True
        assert result["result"] == "done"
        assert result["items"] == 5


class TestJsonOutputMarker:
    """Tests for JSON_OUTPUT_MARKER constant."""

    def test_json_output_marker_is_string(self):
        """Test that JSON_OUTPUT_MARKER is a string."""
        from blender_lib.script_utils import JSON_OUTPUT_MARKER

        assert isinstance(JSON_OUTPUT_MARKER, str)

    def test_json_output_marker_value(self):
        """Test the expected value of JSON_OUTPUT_MARKER."""
        from blender_lib.script_utils import JSON_OUTPUT_MARKER

        assert JSON_OUTPUT_MARKER == "JSON_OUTPUT:"
