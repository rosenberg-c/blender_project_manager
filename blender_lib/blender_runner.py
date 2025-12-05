"""Wrapper for executing Python code via Blender subprocess."""

import subprocess
from pathlib import Path
from typing import Dict, Optional


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
            subprocess.CalledProcessError: If Blender exits with error
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
                check=True
            )
            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Blender operation timed out after {timeout or self.timeout} seconds"
            ) from e

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Blender exited with error code {e.returncode}:\n"
                f"STDOUT: {e.stdout}\n"
                f"STDERR: {e.stderr}"
            ) from e

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
                check=True
            )
            return result

        except subprocess.TimeoutExpired as e:
            raise TimeoutError(
                f"Blender operation timed out after {timeout or self.timeout} seconds"
            ) from e

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Blender exited with error code {e.returncode}:\n"
                f"STDOUT: {e.stdout}\n"
                f"STDERR: {e.stderr}"
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
