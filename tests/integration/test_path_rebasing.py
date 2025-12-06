"""Integration tests for path rebasing with actual Blender files."""

import json
import subprocess
from pathlib import Path

import pytest

# Add parent directory to path to import from services
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.blender_service import extract_json_from_output


@pytest.mark.integration
class TestPathRebasingIntegration:
    """Integration tests for path rebasing operations."""

    def test_rebase_blend_paths_after_move(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test rebasing internal paths after moving a .blend file."""
        # Create project structure
        old_dir = tmp_path / "scenes"
        old_dir.mkdir()

        textures_dir = tmp_path / "textures"
        textures_dir.mkdir()

        # Create a dummy texture
        texture = textures_dir / "wood.png"
        texture.write_bytes(b"FAKE_PNG")

        # Create blend file with reference to texture
        blend_file = old_dir / "test.blend"

        # Script to create blend with texture reference
        setup_script = f"""
import bpy

# Create a simple material with image texture
mat = bpy.data.materials.new("TestMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
tex_node = nodes.new('ShaderNodeTexImage')

# Load the texture with relative path
img = bpy.data.images.load("{texture}", check_existing=False)
img.filepath = "//../textures/wood.png"  # Relative path
tex_node.image = img

# Save
bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_script)

        # Create the blend file
        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0, f"Failed to create blend file: {result.stderr}"
        assert blend_file.exists()

        # Now move the blend file to a new location
        new_dir = tmp_path / "exported" / "scenes"
        new_dir.mkdir(parents=True)
        new_blend_path = new_dir / "test.blend"

        # Copy blend file to new location (simulating a move)
        import shutil
        shutil.copy(blend_file, new_blend_path)

        # Run rebase script
        rebase_script = Path(__file__).parent.parent.parent / "blender_lib" / "rebase_blend_paths.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(rebase_script),
                "--",
                "--blend-file", str(new_blend_path),
                "--old-dir", str(old_dir),
                "--new-dir", str(new_dir),
                "--dry-run", "false"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, f"Rebase failed: {result.stderr}"

        # Parse output
        output = result.stdout
        assert "JSON_OUTPUT:" in output

        data = extract_json_from_output(output)

        assert data["success"] is True
        assert len(data["rebased_images"]) > 0

        # Verify the path was rebased correctly
        rebased = data["rebased_images"][0]
        assert rebased["old_path"] == "//../textures/wood.png"
        # New path should account for the deeper nesting
        assert ".." in rebased["new_path"]

    def test_skip_rebasing_co_moved_files(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test that co-moved files don't get their paths rebased."""
        # Create directory structure
        old_dir = tmp_path / "project"
        old_dir.mkdir()

        # Create texture in same directory
        texture = old_dir / "texture.png"
        texture.write_bytes(b"FAKE_PNG")

        # Create blend file with reference to co-located texture
        blend_file = old_dir / "test.blend"

        setup_script = f"""
import bpy

# Create material with texture
mat = bpy.data.materials.new("TestMaterial")
mat.use_nodes = True
nodes = mat.node_tree.nodes
tex_node = nodes.new('ShaderNodeTexImage')

# Load texture with relative path (same directory)
img = bpy.data.images.load("{texture}", check_existing=False)
img.filepath = "//texture.png"
tex_node.image = img

bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_script)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0

        # Move entire directory
        new_dir = tmp_path / "moved_project"
        import shutil
        shutil.copytree(old_dir, new_dir)

        new_blend_path = new_dir / "test.blend"
        new_texture_path = new_dir / "texture.png"

        # Run rebase with moved files list
        rebase_script = Path(__file__).parent.parent.parent / "blender_lib" / "rebase_blend_paths.py"

        # Pass BOTH files as moved
        moved_files = f"{blend_file},{texture}"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(rebase_script),
                "--",
                "--blend-file", str(new_blend_path),
                "--old-dir", str(old_dir),
                "--new-dir", str(new_dir),
                "--moved-files", moved_files,
                "--dry-run", "false"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0

        # Parse output
        output = result.stdout
        data = extract_json_from_output(output)

        assert data["success"] is True

        # The texture path should NOT be rebased (it was skipped)
        assert len(data["rebased_images"]) == 0
        assert len(data["skipped_paths"]) > 0

        skipped = data["skipped_paths"][0]
        assert "also moved" in skipped["reason"].lower()


@pytest.mark.integration
class TestLinkObjectsIntegration:
    """Integration tests for link operations."""

    def test_link_collection_instance_mode(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test linking a collection in instance mode."""
        # Create source blend file with a collection
        source_blend = tmp_path / "source.blend"

        setup_source = f"""
import bpy

# Clear default
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create a collection with an object
col = bpy.data.collections.new("MyAssets")
bpy.context.scene.collection.children.link(col)

# Add a cube to the collection
mesh = bpy.data.meshes.new("Cube")
obj = bpy.data.objects.new("Cube", mesh)
col.objects.link(obj)

bpy.ops.wm.save_as_mainfile(filepath="{source_blend}")
"""

        script_file = tmp_path / "setup_source.py"
        script_file.write_text(setup_source)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0

        # Create target blend file
        target_blend = tmp_path / "target.blend"

        setup_target = f"""
import bpy
bpy.ops.wm.save_as_mainfile(filepath="{target_blend}")
"""

        script_file = tmp_path / "setup_target.py"
        script_file.write_text(setup_target)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0

        # Run link script (dry run first)
        link_script = Path(__file__).parent.parent.parent / "blender_lib" / "link_objects.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(link_script),
                "--",
                "--target-file", str(target_blend),
                "--target-scene", "Scene",
                "--source-file", str(source_blend),
                "--item-names", "MyAssets",
                "--item-types", "collection",
                "--target-collection", "LinkedAssets",
                "--link-mode", "instance",
                "--dry-run", "true"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0

        # Parse dry run output
        output = result.stdout
        data = extract_json_from_output(output)

        assert data["success"] is True
        assert len(data["linked_items"]) == 1
        assert data["linked_items"][0]["name"] == "MyAssets"
        assert data["linked_items"][0]["status"] == "will_link"

    def test_link_naming_conflict_validation(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test that naming conflicts are detected."""
        # Create source blend
        source_blend = tmp_path / "source.blend"

        setup_source = f"""
import bpy
col = bpy.data.collections.new("MyCollection")
bpy.context.scene.collection.children.link(col)
bpy.ops.wm.save_as_mainfile(filepath="{source_blend}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_source)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0

        # Create target
        target_blend = tmp_path / "target.blend"

        setup_target = f"""
import bpy
bpy.ops.wm.save_as_mainfile(filepath="{target_blend}")
"""

        script_file = tmp_path / "setup_target.py"
        script_file.write_text(setup_target)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        # Try to link with conflicting name
        link_script = Path(__file__).parent.parent.parent / "blender_lib" / "link_objects.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(link_script),
                "--",
                "--target-file", str(target_blend),
                "--target-scene", "Scene",
                "--source-file", str(source_blend),
                "--item-names", "MyCollection",
                "--item-types", "collection",
                "--target-collection", "MyCollection",  # CONFLICT!
                "--link-mode", "instance",
                "--dry-run", "true"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail
        assert result.returncode != 0

        # Parse output
        output = result.stdout
        data = extract_json_from_output(output)

        assert data["success"] is False
        assert len(data["errors"]) > 0
        assert any("conflicts" in err.lower() for err in data["errors"])


@pytest.mark.integration
class TestRenameObjectsIntegration:
    """Integration tests for rename operations."""

    def test_rename_objects_in_blend(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test renaming objects in a .blend file."""
        # Create blend file with objects
        blend_file = tmp_path / "test.blend"

        setup_script = f"""
import bpy

# Clear defaults
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create objects
for i in range(3):
    mesh = bpy.data.meshes.new(f"Cube_{{i}}")
    obj = bpy.data.objects.new(f"Cube_{{i}}", mesh)
    bpy.context.scene.collection.objects.link(obj)

bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_script)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        assert result.returncode == 0

        # Run rename operation (dry run)
        rename_script = Path(__file__).parent.parent.parent / "blender_lib" / "rename_objects.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(rename_script),
                "--",
                "--blend-file", str(blend_file),
                "--project-root", str(tmp_path),
                "--item-names", "Cube_0,Cube_1,Cube_2",
                "--find", "Cube",
                "--replace", "Box",
                "--dry-run", "true"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0

        # Parse output
        output = result.stdout
        data = extract_json_from_output(output)

        assert len(data["renamed"]) == 3
        for item in data["renamed"]:
            assert "Cube" in item["old_name"]
            assert "Box" in item["new_name"]

    def test_rename_with_empty_find_text(
        self,
        tmp_path,
        blender_path,
        skip_if_no_blender
    ):
        """Test that empty find text is rejected."""
        blend_file = tmp_path / "test.blend"

        # Create minimal blend file
        setup_script = f"""
import bpy
bpy.ops.wm.save_as_mainfile(filepath="{blend_file}")
"""

        script_file = tmp_path / "setup.py"
        script_file.write_text(setup_script)

        result = subprocess.run(
            [str(blender_path), "--background", "--python", str(script_file)],
            capture_output=True,
            timeout=30
        )

        # Try to rename with empty find text
        rename_script = Path(__file__).parent.parent.parent / "blender_lib" / "rename_objects.py"

        result = subprocess.run(
            [
                str(blender_path),
                "--background",
                "--python", str(rename_script),
                "--",
                "--blend-file", str(blend_file),
                "--project-root", str(tmp_path),
                "--item-names", "Object",
                "--find", "",  # Empty!
                "--replace", "Box",
                "--dry-run", "true"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should still succeed but with error in output
        output = result.stdout
        data = extract_json_from_output(output)

        assert len(data["errors"]) > 0
        assert any("empty" in err.lower() for err in data["errors"])
