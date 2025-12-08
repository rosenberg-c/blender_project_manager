"""Wrapper for executing Python code via Blender subprocess."""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable
import threading


class BlenderRunner:
    """Executes Python code via Blender's Python interpreter.

    All operations that require the 'bpy' module must run through Blender's
    Python interpreter. This class manages subprocess calls to Blender.
    """

    def __init__(self, blender_path: Path, timeout: int = 300):
        """Initialize BlenderRunner.

        Args:
            blender_path: Path to Blender executable
            timeout: Maximum time to wait for operations (seconds)
        """
        self.blender_path = blender_path
        self.timeout = timeout

        if not self.blender_path.exists():
            raise FileNotFoundError(
                f"Blender not found at: {self.blender_path}\n"
                "Please check your configuration."
            )

    def run_script(self,
                   script_path: Path,
                   args: Dict[str, str],
                   timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a Python script via Blender --background --python.

        Args:
            script_path: Path to the Python script to execute
            args: Dictionary of arguments to pass to the script
            timeout: Optional timeout override

        Returns:
            CompletedProcess with stdout, stderr, and returncode

        Raises:
            subprocess.TimeoutExpired: If operation takes too long
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        cmd = [
            str(self.blender_path),
            '--background',  # Run without GUI
            '--python', str(script_path),
            '--'  # Separator for script arguments
        ]

        # Add script arguments
        for key, value in args.items():
            cmd.extend([f'--{key}', str(value)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False  # Don't raise on non-zero exit - Blender often returns non-zero even on success
            )

            # Only raise error if there's actual failure (no JSON output, critical errors, etc.)
            # Let the caller decide if the output is acceptable
            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Blender operation timed out after {timeout or self.timeout} seconds"
            ) from e

    def run_script_with_progress(self,
                                  script_path: Path,
                                  args: Dict[str, str],
                                  progress_callback: Callable[[str], None],
                                  timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute a Python script via Blender with real-time progress updates.

        This method captures stdout in real-time and calls the progress_callback
        for each line of output.

        Args:
            script_path: Path to the Python script to execute
            args: Dictionary of arguments to pass to the script
            progress_callback: Callback function called for each line of output
            timeout: Optional timeout override

        Returns:
            CompletedProcess with stdout, stderr, and returncode

        Raises:
            subprocess.TimeoutExpired: If operation takes too long
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        cmd = [
            str(self.blender_path),
            '--background',  # Run without GUI
            '--python', str(script_path),
            '--'  # Separator for script arguments
        ]

        # Add script arguments
        for key, value in args.items():
            cmd.extend([f'--{key}', str(value)])

        try:
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Collect all output
            stdout_lines = []
            stderr_lines = []

            def read_stdout():
                """Read stdout and call progress callback."""
                for line in process.stdout:
                    line = line.rstrip()
                    stdout_lines.append(line)
                    # Call progress callback for each line
                    progress_callback(line)

            def read_stderr():
                """Read stderr."""
                for line in process.stderr:
                    stderr_lines.append(line.rstrip())

            # Start threads to read output
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            stdout_thread.start()
            stderr_thread.start()

            # Wait for process to complete
            try:
                process.wait(timeout=timeout or self.timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                raise TimeoutError(
                    f"Blender operation timed out after {timeout or self.timeout} seconds"
                )

            # Wait for threads to finish reading
            stdout_thread.join()
            stderr_thread.join()

            # Create a CompletedProcess result
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout='\n'.join(stdout_lines),
                stderr='\n'.join(stderr_lines)
            )

            return result

        except Exception as e:
            if isinstance(e, TimeoutError):
                raise
            raise RuntimeError(f"Failed to execute Blender script: {str(e)}") from e

    def run_inline(self, python_code: str, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Execute inline Python code via Blender --python-expr.

        Args:
            python_code: Python code to execute
            timeout: Optional timeout override

        Returns:
            CompletedProcess with stdout, stderr, and returncode
        """
        cmd = [
            str(self.blender_path),
            '--background',
            '--python-expr', python_code
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False  # Don't raise on non-zero exit
            )
            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Blender operation timed out after {timeout or self.timeout} seconds"
            ) from e

    def test_connection(self) -> bool:
        """Test if Blender is accessible and working.

        Returns:
            True if Blender is accessible, False otherwise
        """
        try:
            result = self.run_inline("print('Blender OK')", timeout=10)
            return "Blender OK" in result.stdout
        except Exception:
            return False
