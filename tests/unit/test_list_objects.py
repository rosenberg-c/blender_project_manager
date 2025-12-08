"""Unit tests for list_objects Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestListObjectsPathHandling:
    """Tests for proper Path object handling in list_objects.py."""

    def test_list_objects_function_works(self):
        """Test that list_objects_and_collections function works correctly.

        This verifies the core function doesn't require path handling,
        as paths are handled by argparse in the main block.
        """
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy with empty scene
        mock_bpy = MagicMock()
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            # Verify function works without path arguments
            assert "objects" in result
            assert "collections" in result
            assert isinstance(result["objects"], list)
            assert isinstance(result["collections"], list)


class TestListObjectsAndCollections:
    """Tests for list_objects_and_collections function."""

    def test_lists_empty_scene(self):
        """Test listing objects in empty scene."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            assert "objects" in result
            assert "collections" in result
            assert result["objects"] == []
            assert result["collections"] == []

    def test_lists_objects(self):
        """Test listing objects in scene."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock objects
        mock_obj1 = MagicMock()
        mock_obj1.name = "Cube"
        mock_obj1.type = "MESH"
        mock_obj1.users_collection = []

        mock_obj2 = MagicMock()
        mock_obj2.name = "Camera"
        mock_obj2.type = "CAMERA"
        mock_obj2.users_collection = []

        mock_bpy = MagicMock()
        mock_bpy.data.objects = [mock_obj1, mock_obj2]
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            assert len(result["objects"]) == 2
            assert result["objects"][0]["name"] == "Cube"
            assert result["objects"][0]["type"] == "MESH"
            assert result["objects"][1]["name"] == "Camera"
            assert result["objects"][1]["type"] == "CAMERA"

    def test_lists_collections(self):
        """Test listing collections in scene."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock collections
        mock_col1 = MagicMock()
        mock_col1.name = "Collection 1"
        mock_col1.objects = []
        mock_col1.children = []

        mock_col2 = MagicMock()
        mock_col2.name = "Collection 2"
        mock_col2.objects = [MagicMock(), MagicMock()]  # 2 objects
        mock_col2.children = [MagicMock()]  # 1 child collection

        mock_bpy = MagicMock()
        mock_bpy.data.objects = []
        mock_bpy.data.collections = [mock_col1, mock_col2]

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            assert len(result["collections"]) == 2
            assert result["collections"][0]["name"] == "Collection 1"
            assert result["collections"][0]["objects_count"] == 0
            assert result["collections"][0]["children_count"] == 0
            assert result["collections"][1]["name"] == "Collection 2"
            assert result["collections"][1]["objects_count"] == 2
            assert result["collections"][1]["children_count"] == 1

    def test_objects_with_collections(self):
        """Test that objects list their collection memberships."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock collections
        mock_col1 = MagicMock()
        mock_col1.name = "Collection 1"

        mock_col2 = MagicMock()
        mock_col2.name = "Collection 2"

        # Mock object in multiple collections
        mock_obj = MagicMock()
        mock_obj.name = "Cube"
        mock_obj.type = "MESH"
        mock_obj.users_collection = [mock_col1, mock_col2]

        mock_bpy = MagicMock()
        mock_bpy.data.objects = [mock_obj]
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            assert len(result["objects"]) == 1
            assert result["objects"][0]["name"] == "Cube"
            assert "Collection 1" in result["objects"][0]["collections"]
            assert "Collection 2" in result["objects"][0]["collections"]

    def test_result_structure(self):
        """Test that result has correct structure."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        mock_bpy.data.objects = []
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            # Verify structure
            assert isinstance(result, dict)
            assert "objects" in result
            assert "collections" in result
            assert isinstance(result["objects"], list)
            assert isinstance(result["collections"], list)

    def test_object_types(self):
        """Test that different object types are correctly identified."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Create objects of different types
        object_types = [
            ("Cube", "MESH"),
            ("Light", "LIGHT"),
            ("Camera", "CAMERA"),
            ("Empty", "EMPTY"),
            ("Armature", "ARMATURE")
        ]

        mock_objects = []
        for name, obj_type in object_types:
            mock_obj = MagicMock()
            mock_obj.name = name
            mock_obj.type = obj_type
            mock_obj.users_collection = []
            mock_objects.append(mock_obj)

        mock_bpy = MagicMock()
        mock_bpy.data.objects = mock_objects
        mock_bpy.data.collections = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from list_objects import list_objects_and_collections

            result = list_objects_and_collections()

            assert len(result["objects"]) == 5
            for i, (name, obj_type) in enumerate(object_types):
                assert result["objects"][i]["name"] == name
                assert result["objects"][i]["type"] == obj_type
