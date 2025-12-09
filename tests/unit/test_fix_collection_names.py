"""Unit tests for fix_collection_names Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestFixCollectionNames:
    """Tests for collection name remapping functionality."""

    def test_remap_instance_collection_updates_empty(self, tmp_path):
        """Test remapping instance mode collection updates Empty object."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy
        mock_bpy = MagicMock()

        # Mock Empty object with old collection instance
        mock_old_collection = MagicMock()
        mock_old_collection.name = "Tree"
        mock_old_collection.users = 0

        mock_empty = MagicMock()
        mock_empty.name = "Tree_Instance"
        mock_empty.instance_type = 'COLLECTION'
        mock_empty.instance_collection = mock_old_collection

        mock_bpy.data.objects.get = MagicMock(return_value=mock_empty)

        # Mock library loading for new collection
        mock_new_collection = MagicMock()
        mock_new_collection.name = "Tree_v2"

        mock_data_from = MagicMock()
        mock_data_from.collections = ["Tree_v2"]
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)
        mock_bpy.data.collections.get = MagicMock(return_value=mock_new_collection)
        mock_bpy.data.collections.remove = MagicMock()
        mock_bpy.path.abspath = lambda p: str(tmp_path / "assets.blend")

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from fix_collection_names import remap_instance_collection

            result = remap_instance_collection(
                str(tmp_path / "assets.blend"),
                "Tree",
                "Tree_v2",
                "Tree_Instance"
            )

            # Should succeed
            assert result["success"] is True
            assert result["old_name"] == "Tree"
            assert result["new_name"] == "Tree_v2"
            assert result["mode"] == "instance"

            # Empty's instance_collection should be updated
            assert mock_empty.instance_collection == mock_new_collection

    def test_remap_individual_collection_updates_hierarchy(self, tmp_path):
        """Test remapping individual mode collection updates scene hierarchy."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy
        mock_bpy = MagicMock()

        # Mock old collection
        mock_old_collection = MagicMock()
        mock_old_collection.name = "Tree"
        mock_old_collection.users = 0

        # Mock parent collection containing old collection
        mock_parent = MagicMock()
        mock_child1 = MagicMock()
        mock_child1.name = "Tree"

        # Mock children as a container with link/unlink methods
        mock_children = MagicMock()
        mock_children.__iter__ = lambda self: iter([mock_child1])
        mock_children.link = MagicMock()
        mock_children.unlink = MagicMock()
        mock_parent.children = mock_children

        # Create a mock collections container that is both iterable and has .get
        mock_collections_container = MagicMock()
        mock_collections_container.__iter__ = lambda self: iter([mock_parent])

        mock_bpy.data.collections = mock_collections_container

        # Mock new collection
        mock_new_collection = MagicMock()
        mock_new_collection.name = "Tree_v2"

        mock_data_from = MagicMock()
        mock_data_from.collections = ["Tree_v2"]
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        # After loading, get should return new collection
        def get_side_effect(name):
            if name == "Tree":
                return mock_old_collection
            elif name == "Tree_v2":
                return mock_new_collection
            return None

        mock_collections_container.get = MagicMock(side_effect=get_side_effect)
        mock_bpy.data.collections.remove = MagicMock()
        mock_bpy.path.abspath = lambda p: str(tmp_path / "assets.blend")

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from fix_collection_names import remap_individual_collection

            result = remap_individual_collection(
                str(tmp_path / "assets.blend"),
                "Tree",
                "Tree_v2"
            )

            # Should succeed
            assert result["success"] is True
            assert result["old_name"] == "Tree"
            assert result["new_name"] == "Tree_v2"
            assert result["mode"] == "individual"

            # Parent should have link/unlink called
            assert mock_children.link.called
            assert mock_children.unlink.called

    def test_remap_handles_missing_instance_object(self, tmp_path):
        """Test remapping fails gracefully when instance object not found."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        mock_bpy.data.objects.get = MagicMock(return_value=None)
        mock_bpy.path.abspath = lambda p: str(tmp_path / "assets.blend")

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from fix_collection_names import remap_instance_collection

            result = remap_instance_collection(
                str(tmp_path / "assets.blend"),
                "Tree",
                "Tree_v2",
                "Missing_Instance"
            )

            # Should fail with error
            assert result["success"] is False
            assert len(result["errors"]) > 0
            assert "not found" in result["errors"][0].lower()

    def test_remap_handles_missing_new_collection(self, tmp_path):
        """Test remapping fails when new collection doesn't exist in library."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()

        mock_empty = MagicMock()
        mock_empty.instance_type = 'COLLECTION'
        mock_bpy.data.objects.get = MagicMock(return_value=mock_empty)

        # New collection not in library
        mock_data_from = MagicMock()
        mock_data_from.collections = ["Oak", "Bush"]  # Tree_v2 not here
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)
        mock_bpy.path.abspath = lambda p: str(tmp_path / "assets.blend")

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from fix_collection_names import remap_instance_collection

            result = remap_instance_collection(
                str(tmp_path / "assets.blend"),
                "Tree",
                "Tree_v2",
                "Tree_Instance"
            )

            # Should fail
            assert result["success"] is False
            assert len(result["errors"]) > 0
            assert "not found in library" in result["errors"][0].lower()
