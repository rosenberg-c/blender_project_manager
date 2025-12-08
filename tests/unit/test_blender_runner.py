"""Unit tests for BlenderRunner."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import subprocess
import pytest


class TestBlenderRunnerInitialization:
    """Tests for BlenderRunner initialization."""

    def test_init_with_valid_blender_path(self, tmp_path):
        """Test initialization with valid Blender path."""
        from blender_lib.blender_runner import BlenderRunner

        # Create fake Blender executable
        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash\necho 'fake blender'")

        runner = BlenderRunner(blender_path, timeout=60)

        assert runner.blender_path == blender_path
        assert runner.timeout == 60

    def test_init_with_nonexistent_blender_path(self, tmp_path):
        """Test that initialization fails with nonexistent Blender path."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "nonexistent_blender"

        with pytest.raises(FileNotFoundError, match="Blender not found"):
            BlenderRunner(blender_path)

    def test_default_timeout(self, tmp_path):
        """Test that default timeout is 300 seconds."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        assert runner.timeout == 300


class TestRunScript:
    """Tests for run_script method."""

    def test_run_script_builds_correct_command(self, tmp_path):
        """Test that run_script builds the correct subprocess command."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            runner.run_script(
                script_path,
                {"arg1": "value1", "arg2": "value2"}
            )

            # Verify subprocess.run was called with correct command
            call_args = mock_run.call_args[0][0]
            assert str(blender_path) in call_args
            assert '--background' in call_args
            assert '--python' in call_args
            assert str(script_path) in call_args
            assert '--' in call_args
            assert '--arg1' in call_args
            assert 'value1' in call_args
            assert '--arg2' in call_args
            assert 'value2' in call_args

    def test_run_script_with_nonexistent_script(self, tmp_path):
        """Test that run_script raises error for nonexistent script."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        script_path = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError, match="Script not found"):
            runner.run_script(script_path, {})

    def test_run_script_returns_completed_process(self, tmp_path):
        """Test that run_script returns CompletedProcess."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            expected_result = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="output", stderr="error"
            )
            mock_run.return_value = expected_result

            result = runner.run_script(script_path, {})

            assert result == expected_result

    def test_run_script_with_custom_timeout(self, tmp_path):
        """Test that run_script uses custom timeout."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path, timeout=300)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            runner.run_script(script_path, {}, timeout=120)

            # Verify timeout was passed
            assert mock_run.call_args[1]['timeout'] == 120

    def test_run_script_handles_timeout_exception(self, tmp_path):
        """Test that run_script handles TimeoutExpired."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=10)

            with pytest.raises(TimeoutError, match="timed out"):
                runner.run_script(script_path, {})


class TestRunScriptWithProgress:
    """Tests for run_script_with_progress method."""

    def test_run_script_with_progress_calls_callback(self, tmp_path):
        """Test that progress callback is called for each line of output."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        # Mock process
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = iter(["line1\n", "line2\n", "line3\n"])
        mock_process.stderr = iter([])

        callback_lines = []

        def progress_callback(line):
            callback_lines.append(line)

        with patch('subprocess.Popen', return_value=mock_process):
            runner.run_script_with_progress(
                script_path,
                {},
                progress_callback
            )

            # Verify callback was called for each line
            assert "line1" in callback_lines
            assert "line2" in callback_lines
            assert "line3" in callback_lines

    def test_run_script_with_progress_builds_correct_command(self, tmp_path):
        """Test that correct command is built."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = iter([])
        mock_process.stderr = iter([])

        with patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value = mock_process

            runner.run_script_with_progress(
                script_path,
                {"arg1": "value1"},
                lambda line: None
            )

            # Verify Popen was called with correct command
            call_args = mock_popen.call_args[0][0]
            assert str(blender_path) in call_args
            assert '--background' in call_args
            assert '--python' in call_args
            assert str(script_path) in call_args
            assert '--' in call_args
            assert '--arg1' in call_args
            assert 'value1' in call_args

    def test_run_script_with_progress_handles_timeout(self, tmp_path):
        """Test that timeout is handled correctly."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        mock_process = MagicMock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=10)
        mock_process.stdout = iter([])
        mock_process.stderr = iter([])

        with patch('subprocess.Popen', return_value=mock_process):
            with pytest.raises(TimeoutError, match="timed out"):
                runner.run_script_with_progress(
                    script_path,
                    {},
                    lambda line: None,
                    timeout=10
                )

            # Verify process was killed
            assert mock_process.kill.called

    def test_run_script_with_progress_returns_completed_process(self, tmp_path):
        """Test that CompletedProcess is returned with combined output."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        script_path = tmp_path / "test_script.py"
        script_path.write_text("print('test')")

        runner = BlenderRunner(blender_path)

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = iter(["line1\n", "line2\n"])
        mock_process.stderr = iter(["error1\n"])

        with patch('subprocess.Popen', return_value=mock_process):
            result = runner.run_script_with_progress(
                script_path,
                {},
                lambda line: None
            )

            # Verify result structure
            assert isinstance(result, subprocess.CompletedProcess)
            assert result.returncode == 0
            assert "line1" in result.stdout
            assert "line2" in result.stdout
            assert "error1" in result.stderr


class TestRunInline:
    """Tests for run_inline method."""

    def test_run_inline_builds_correct_command(self, tmp_path):
        """Test that run_inline builds correct command."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )

            runner.run_inline("print('hello')")

            # Verify command structure
            call_args = mock_run.call_args[0][0]
            assert str(blender_path) in call_args
            assert '--background' in call_args
            assert '--python-expr' in call_args
            assert "print('hello')" in call_args

    def test_run_inline_returns_result(self, tmp_path):
        """Test that run_inline returns CompletedProcess."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            expected_result = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="output", stderr=""
            )
            mock_run.return_value = expected_result

            result = runner.run_inline("print('test')")

            assert result == expected_result

    def test_run_inline_handles_timeout(self, tmp_path):
        """Test that run_inline handles timeout."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=10)

            with pytest.raises(TimeoutError, match="timed out"):
                runner.run_inline("print('test')")


class TestTestConnection:
    """Tests for test_connection method."""

    def test_test_connection_success(self, tmp_path):
        """Test successful connection test."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch.object(runner, 'run_inline') as mock_run_inline:
            mock_run_inline.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="Blender OK", stderr=""
            )

            result = runner.test_connection()

            assert result is True
            assert mock_run_inline.call_args[0][0] == "print('Blender OK')"
            assert mock_run_inline.call_args[1]['timeout'] == 10

    def test_test_connection_failure(self, tmp_path):
        """Test failed connection test."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch.object(runner, 'run_inline') as mock_run_inline:
            mock_run_inline.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="Error"
            )

            result = runner.test_connection()

            assert result is False

    def test_test_connection_handles_exception(self, tmp_path):
        """Test that test_connection handles exceptions gracefully."""
        from blender_lib.blender_runner import BlenderRunner

        blender_path = tmp_path / "blender"
        blender_path.write_text("#!/bin/bash")

        runner = BlenderRunner(blender_path)

        with patch.object(runner, 'run_inline') as mock_run_inline:
            mock_run_inline.side_effect = Exception("Connection failed")

            result = runner.test_connection()

            assert result is False
