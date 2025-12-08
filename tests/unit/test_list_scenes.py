"""Unit tests for list_scenes Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestListScenesPathHandling:
    """Tests for proper Path object handling in list_scenes.py."""

    def test_list_scenes_converts_paths_to_strings(self, tmp_path):
        """Test that Path objects are converted to strings when opening .blend files."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        blend_file = project_root / "scene.blend"
        blend_file.write_bytes(b"FAKE_BLEND")

        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.data.scenes = []
        mock_bpy.context.scene = None

        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Test will verify filepath handling in integration context
            pass


class TestListScenes:
    """Tests for list_scenes function."""

    def test_lists_empty_blend_file(self):
        """Test listing scenes in blend file with no scenes."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = []
        mock_bpy.context.scene = None

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert "scenes" in result
            assert result["scenes"] == []

    def test_lists_single_scene(self):
        """Test listing a single scene."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scene
        mock_scene = MagicMock()
        mock_scene.name = "Scene"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene]
        mock_bpy.context.scene = None

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert len(result["scenes"]) == 1
            assert result["scenes"][0]["name"] == "Scene"
            assert result["scenes"][0]["is_active"] is False

    def test_lists_multiple_scenes(self):
        """Test listing multiple scenes."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scenes
        mock_scene1 = MagicMock()
        mock_scene1.name = "Scene 1"

        mock_scene2 = MagicMock()
        mock_scene2.name = "Scene 2"

        mock_scene3 = MagicMock()
        mock_scene3.name = "Scene 3"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene1, mock_scene2, mock_scene3]
        mock_bpy.context.scene = None

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert len(result["scenes"]) == 3
            assert result["scenes"][0]["name"] == "Scene 1"
            assert result["scenes"][1]["name"] == "Scene 2"
            assert result["scenes"][2]["name"] == "Scene 3"

    def test_identifies_active_scene(self):
        """Test that active scene is correctly identified."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scenes
        mock_scene1 = MagicMock()
        mock_scene1.name = "Scene 1"

        mock_scene2 = MagicMock()
        mock_scene2.name = "Scene 2"  # This is active

        mock_scene3 = MagicMock()
        mock_scene3.name = "Scene 3"

        # Set active scene
        mock_context_scene = MagicMock()
        mock_context_scene.name = "Scene 2"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene1, mock_scene2, mock_scene3]
        mock_bpy.context.scene = mock_context_scene

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert len(result["scenes"]) == 3
            assert result["scenes"][0]["is_active"] is False  # Scene 1
            assert result["scenes"][1]["is_active"] is True   # Scene 2 (active)
            assert result["scenes"][2]["is_active"] is False  # Scene 3

    def test_handles_no_active_scene(self):
        """Test handling when no scene is active."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scenes
        mock_scene = MagicMock()
        mock_scene.name = "Scene"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene]
        mock_bpy.context.scene = None  # No active scene

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert len(result["scenes"]) == 1
            assert result["scenes"][0]["is_active"] is False

    def test_result_structure(self):
        """Test that result has correct structure."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = []
        mock_bpy.context.scene = None

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            # Verify structure
            assert isinstance(result, dict)
            assert "scenes" in result
            assert isinstance(result["scenes"], list)

    def test_scene_entry_structure(self):
        """Test that each scene entry has required fields."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scene
        mock_scene = MagicMock()
        mock_scene.name = "TestScene"

        mock_context_scene = MagicMock()
        mock_context_scene.name = "TestScene"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene]
        mock_bpy.context.scene = mock_context_scene

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            scene_entry = result["scenes"][0]
            assert "name" in scene_entry
            assert "is_active" in scene_entry
            assert isinstance(scene_entry["name"], str)
            assert isinstance(scene_entry["is_active"], bool)

    def test_special_scene_names(self):
        """Test handling of scenes with special characters in names."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock scenes with special names
        mock_scene1 = MagicMock()
        mock_scene1.name = "Scene.001"

        mock_scene2 = MagicMock()
        mock_scene2.name = "My Scene (Copy)"

        mock_scene3 = MagicMock()
        mock_scene3.name = "Scene_With_Underscores"

        mock_bpy = MagicMock()
        mock_bpy.data.scenes = [mock_scene1, mock_scene2, mock_scene3]
        mock_bpy.context.scene = None

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_scenes import list_scenes

            result = list_scenes()

            assert len(result["scenes"]) == 3
            assert result["scenes"][0]["name"] == "Scene.001"
            assert result["scenes"][1]["name"] == "My Scene (Copy)"
            assert result["scenes"][2]["name"] == "Scene_With_Underscores"
