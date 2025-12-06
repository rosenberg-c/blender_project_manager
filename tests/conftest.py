"""Pytest configuration and shared fixtures."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Generator, List

import pytest


# ==============================================================================
# Path Fixtures
# ==============================================================================

@pytest.fixture
def fixtures_dir() -> Path:
    """Directory containing test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_data_dir(tmp_path: Path, fixtures_dir: Path) -> Path:
    """Temporary directory with test data copied from fixtures.

    Each test gets a fresh copy of the fixtures directory.
    """
    test_dir = tmp_path / "test_data"
    if fixtures_dir.exists():
        shutil.copytree(fixtures_dir, test_dir)
    else:
        test_dir.mkdir(parents=True)
    return test_dir


@pytest.fixture
def empty_project_dir(tmp_path: Path) -> Path:
    """Empty project directory for testing."""
    project_dir = tmp_path / "empty_project"
    project_dir.mkdir(parents=True)
    return project_dir


# ==============================================================================
# Blender Fixtures
# ==============================================================================

@pytest.fixture(scope="session")
def blender_path() -> Path:
    """Path to Blender executable.

    Returns None if Blender not found (integration tests will be skipped).
    """
    # Try to find Blender
    try:
        result = subprocess.run(
            ['which', 'blender'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass

    # Check common macOS location
    macos_blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    if macos_blender.exists():
        return macos_blender

    return None


@pytest.fixture
def skip_if_no_blender(blender_path):
    """Skip test if Blender is not available."""
    if blender_path is None:
        pytest.skip("Blender not found - skipping integration test")


# ==============================================================================
# File Creation Helpers
# ==============================================================================

@pytest.fixture
def create_test_blend_file(tmp_path: Path, blender_path: Path):
    """Factory fixture to create test .blend files."""

    def _create_blend(
        name: str = "test.blend",
        scene_name: str = "Scene",
        add_objects: List[str] = None,
        add_collections: List[str] = None
    ) -> Path:
        """Create a minimal .blend file using Blender.

        Args:
            name: Filename for the .blend file
            scene_name: Name of the scene
            add_objects: List of object names to create
            add_collections: List of collection names to create

        Returns:
            Path to created .blend file
        """
        if blender_path is None:
            pytest.skip("Blender not available")

        blend_file = tmp_path / name

        # Create a Python script to set up the blend file
        script = f"""
import bpy

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Rename scene
bpy.context.scene.name = "{scene_name}"

# Add objects
{_generate_object_creation(add_objects or [])}

# Add collections
{_generate_collection_creation(add_collections or [])}

# Save
bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup_blend.py"
        script_file.write_text(script)

        # Run Blender in background to create the file
        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(script_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create .blend file: {result.stderr}")

        if not blend_file.exists():
            raise RuntimeError(f"Blend file was not created: {blend_file}")

        return blend_file

    return _create_blend


def _generate_object_creation(object_names: List[str]) -> str:
    """Generate Python code to create objects."""
    if not object_names:
        return "# No objects to create"

    code = []
    for name in object_names:
        code.append(f"""
# Create object: {name}
mesh = bpy.data.meshes.new("{name}")
obj = bpy.data.objects.new("{name}", mesh)
bpy.context.scene.collection.objects.link(obj)
""")

    return "\n".join(code)


def _generate_collection_creation(collection_names: List[str]) -> str:
    """Generate Python code to create collections."""
    if not collection_names:
        return "# No collections to create"

    code = []
    for name in collection_names:
        code.append(f"""
# Create collection: {name}
col = bpy.data.collections.new("{name}")
bpy.context.scene.collection.children.link(col)
""")

    return "\n".join(code)


@pytest.fixture
def create_test_texture(tmp_path: Path):
    """Factory fixture to create test texture files."""

    def _create_texture(
        name: str = "test_texture.png",
        width: int = 64,
        height: int = 64,
        color: tuple = (255, 0, 0, 255)
    ) -> Path:
        """Create a minimal test texture file.

        Args:
            name: Filename
            width: Image width in pixels
            height: Image height in pixels
            color: RGBA color tuple

        Returns:
            Path to created texture file
        """
        try:
            from PIL import Image
        except ImportError:
            # If PIL not available, create a dummy file
            texture_file = tmp_path / name
            texture_file.write_bytes(b"FAKE_PNG")
            return texture_file

        texture_file = tmp_path / name
        img = Image.new('RGBA', (width, height), color)
        img.save(texture_file)

        return texture_file

    return _create_texture


# ==============================================================================
# Project Structure Fixtures
# ==============================================================================

@pytest.fixture
def sample_project_structure(tmp_path: Path) -> Path:
    """Create a sample project directory structure.

    Structure:
        project/
        ├── scenes/
        │   ├── main.blend
        │   └── secondary.blend
        ├── assets/
        │   └── props.blend
        ├── textures/
        │   ├── wood.png
        │   └── metal.jpg
        └── renders/
    """
    project_root = tmp_path / "sample_project"

    # Create directories
    scenes_dir = project_root / "scenes"
    assets_dir = project_root / "assets"
    textures_dir = project_root / "textures"
    renders_dir = project_root / "renders"

    scenes_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)
    textures_dir.mkdir(parents=True)
    renders_dir.mkdir(parents=True)

    # Create dummy files
    (scenes_dir / "main.blend").write_bytes(b"FAKE_BLEND")
    (scenes_dir / "secondary.blend").write_bytes(b"FAKE_BLEND")
    (assets_dir / "props.blend").write_bytes(b"FAKE_BLEND")
    (textures_dir / "wood.png").write_bytes(b"FAKE_PNG")
    (textures_dir / "metal.jpg").write_bytes(b"FAKE_JPG")

    return project_root


# ==============================================================================
# Assertion Helpers
# ==============================================================================

def assert_paths_equal(path1: Path, path2: Path):
    """Assert two paths point to the same location."""
    assert path1.resolve() == path2.resolve()


def assert_file_contains_text(file_path: Path, text: str):
    """Assert file contains specified text."""
    assert file_path.exists(), f"File does not exist: {file_path}"
    content = file_path.read_text()
    assert text in content, f"Text '{text}' not found in {file_path}"


def assert_json_output(output: str, expected_keys: List[str]):
    """Assert output contains valid JSON with expected keys."""
    assert "JSON_OUTPUT:" in output, "No JSON_OUTPUT marker found"

    json_start = output.find("JSON_OUTPUT:") + len("JSON_OUTPUT:")
    json_text = output[json_start:].strip()

    try:
        data = json.loads(json_text.split('\n')[0])
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in output: {e}\nOutput: {json_text[:200]}")

    for key in expected_keys:
        assert key in data, f"Expected key '{key}' not found in JSON output"

    return data
