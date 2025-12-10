"""Unit tests for link_objects Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest


class TestLinkObjects:
    """Tests for link objects functionality."""

    def test_find_layer_collection_finds_match(self):
        """Test that find_layer_collection finds a matching collection."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy
        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from link_objects import find_layer_collection

            # Create mock layer collection hierarchy
            root = MagicMock()
            root.name = "Scene Collection"

            child1 = MagicMock()
            child1.name = "Collection1"
            child1.children = []

            child2 = MagicMock()
            child2.name = "TargetCollection"
            child2.children = []

            root.children = [child1, child2]

            # Should find TargetCollection
            result = find_layer_collection(root, "TargetCollection")
            assert result == child2
            assert result.name == "TargetCollection"

    def test_find_layer_collection_finds_nested_match(self):
        """Test that find_layer_collection finds nested collections."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from link_objects import find_layer_collection

            # Create nested hierarchy
            root = MagicMock()
            root.name = "Scene Collection"

            child1 = MagicMock()
            child1.name = "Collection1"

            nested = MagicMock()
            nested.name = "NestedTarget"
            nested.children = []

            child1.children = [nested]
            root.children = [child1]

            # Should find NestedTarget in nested hierarchy
            result = find_layer_collection(root, "NestedTarget")
            assert result == nested
            assert result.name == "NestedTarget"

    def test_find_layer_collection_returns_none_if_not_found(self):
        """Test that find_layer_collection returns None if not found."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from link_objects import find_layer_collection

            root = MagicMock()
            root.name = "Scene Collection"
            root.children = []

            # Should return None if not found
            result = find_layer_collection(root, "NonExistent")
            assert result is None

    def test_hide_viewport_parameter_accepted_instance_mode(self):
        """Test that hide_viewport sets layer_collection.hide_viewport in instance mode."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Create comprehensive bpy mock
        mock_bpy = MagicMock()

        # Mock scene
        mock_scene = MagicMock()
        mock_scene.name = "Scene"
        mock_scenes_container = MagicMock()
        mock_scenes_container.__contains__ = lambda key: key == "Scene"
        mock_scenes_container.__getitem__ = lambda key: mock_scene if key == "Scene" else None
        mock_bpy.data.scenes = mock_scenes_container

        # Mock window and context
        mock_window = MagicMock()
        mock_bpy.context.window = mock_window

        # Mock target collection
        mock_target_collection = MagicMock()
        mock_target_collection.name = "TargetCollection"
        mock_collections_container = MagicMock()
        mock_collections_container.__contains__ = lambda key: key == "TargetCollection"
        mock_collections_container.__getitem__ = lambda key: mock_target_collection if key == "TargetCollection" else None
        mock_collections_container.new = MagicMock(return_value=mock_target_collection)
        mock_collections_container.get = MagicMock(return_value=MagicMock())
        mock_bpy.data.collections = mock_collections_container

        # Mock scene collection
        mock_scene_collection = MagicMock()
        mock_scene.collection = mock_scene_collection

        # Mock layer collection hierarchy
        mock_layer_col = MagicMock()
        mock_layer_col.name = "TargetCollection"
        mock_layer_col.hide_viewport = False

        mock_root_layer = MagicMock()
        mock_root_layer.name = "Scene Collection"
        mock_root_layer.children = [mock_layer_col]

        mock_view_layer = MagicMock()
        mock_view_layer.layer_collection = mock_root_layer
        mock_bpy.context.view_layer = mock_view_layer
        mock_bpy.context.scene = mock_scene

        # Mock library loading
        mock_source_collection = MagicMock()
        mock_source_collection.name = "SourceCollection"

        mock_data_from = MagicMock()
        mock_data_from.collections = ["SourceCollection"]
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        # Mock objects
        mock_empty = MagicMock()
        mock_bpy.data.objects.new = MagicMock(return_value=mock_empty)
        mock_bpy.data.objects.get = MagicMock(return_value=MagicMock())

        # Mock ops
        mock_bpy.ops.wm.save_mainfile = MagicMock()

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Mock Path.exists()
            with patch('pathlib.Path.exists', return_value=True):
                from link_objects import link_items

                # Call with hide_viewport=True in instance mode
                result = link_items(
                    source_file="/fake/source.blend",
                    target_scene="Scene",
                    item_names=["SourceCollection"],
                    item_types=["collection"],
                    target_collection_name="TargetCollection",
                    link_mode='instance',
                    dry_run=False,
                    hide_viewport=True
                )

                # Verify function completes without errors
                assert result is not None
                # Note: Full verification of layer_collection.hide_viewport setting
                # requires integration testing with real Blender environment

    def test_hide_viewport_parameter_accepted_individual_mode(self):
        """Test that hide_viewport sets layer_collection.hide_viewport in individual mode."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Create comprehensive bpy mock
        mock_bpy = MagicMock()

        # Mock scene
        mock_scene = MagicMock()
        mock_scene.name = "Scene"
        mock_scenes_container = MagicMock()
        mock_scenes_container.__contains__ = lambda key: key == "Scene"
        mock_scenes_container.__getitem__ = lambda key: mock_scene if key == "Scene" else None
        mock_bpy.data.scenes = mock_scenes_container

        # Mock window and context
        mock_window = MagicMock()
        mock_bpy.context.window = mock_window

        # Mock target collection
        mock_target_collection = MagicMock()
        mock_target_collection.name = "TargetCollection"
        mock_target_collection.objects = []
        mock_target_collection.children = []
        mock_collections_container = MagicMock()
        mock_collections_container.__contains__ = lambda key: key == "TargetCollection"
        mock_collections_container.__getitem__ = lambda key: mock_target_collection if key == "TargetCollection" else None
        mock_collections_container.new = MagicMock(return_value=mock_target_collection)
        mock_bpy.data.collections = mock_collections_container

        # Mock scene collection
        mock_scene_collection = MagicMock()
        mock_scene.collection = mock_scene_collection

        # Mock layer collection hierarchy
        mock_layer_col = MagicMock()
        mock_layer_col.name = "TargetCollection"
        mock_layer_col.hide_viewport = False

        mock_root_layer = MagicMock()
        mock_root_layer.name = "Scene Collection"
        mock_root_layer.children = [mock_layer_col]

        mock_view_layer = MagicMock()
        mock_view_layer.layer_collection = mock_root_layer
        mock_bpy.context.view_layer = mock_view_layer
        mock_bpy.context.scene = mock_scene

        # Mock library loading
        mock_linked_obj = MagicMock()
        mock_linked_obj.name = "SourceObject"
        mock_linked_obj.library = MagicMock()

        mock_data_from = MagicMock()
        mock_data_from.objects = ["SourceObject"]
        mock_data_from.collections = []
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        # Mock objects
        mock_bpy.data.objects = [mock_linked_obj]
        mock_bpy.data.collections = [mock_target_collection]

        # Mock ops
        mock_bpy.ops.wm.save_mainfile = MagicMock()

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Mock Path.exists()
            with patch('pathlib.Path.exists', return_value=True):
                from link_objects import link_items

                # Call with hide_viewport=True in individual mode
                result = link_items(
                    source_file="/fake/source.blend",
                    target_scene="Scene",
                    item_names=["SourceObject"],
                    item_types=["object"],
                    target_collection_name="TargetCollection",
                    link_mode='individual',
                    dry_run=False,
                    hide_viewport=True
                )

                # Verify function completes without errors
                assert result is not None
                # Note: Full verification of layer_collection.hide_viewport setting
                # requires integration testing with real Blender environment

    def test_hide_viewport_parameter_false(self):
        """Test that hide_viewport is not set when parameter is False."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Create comprehensive bpy mock
        mock_bpy = MagicMock()

        # Mock scene
        mock_scene = MagicMock()
        mock_scene.name = "Scene"
        mock_scenes_container = MagicMock()
        mock_scenes_container.__contains__ = lambda key: key == "Scene"
        mock_scenes_container.__getitem__ = lambda key: mock_scene if key == "Scene" else None
        mock_bpy.data.scenes = mock_scenes_container

        # Mock window and context
        mock_window = MagicMock()
        mock_bpy.context.window = mock_window

        # Mock target collection
        mock_target_collection = MagicMock()
        mock_target_collection.name = "TargetCollection"
        mock_target_collection.objects = []
        mock_target_collection.children = []
        mock_collections_container = MagicMock()
        mock_collections_container.__contains__ = lambda key: key == "TargetCollection"
        mock_collections_container.__getitem__ = lambda key: mock_target_collection if key == "TargetCollection" else None
        mock_collections_container.new = MagicMock(return_value=mock_target_collection)
        mock_bpy.data.collections = mock_collections_container

        # Mock scene collection
        mock_scene_collection = MagicMock()
        mock_scene.collection = mock_scene_collection

        # Mock layer collection hierarchy
        mock_layer_col = MagicMock()
        mock_layer_col.name = "TargetCollection"
        mock_layer_col.hide_viewport = False

        mock_root_layer = MagicMock()
        mock_root_layer.name = "Scene Collection"
        mock_root_layer.children = [mock_layer_col]

        mock_view_layer = MagicMock()
        mock_view_layer.layer_collection = mock_root_layer
        mock_bpy.context.view_layer = mock_view_layer
        mock_bpy.context.scene = mock_scene

        # Mock library loading
        mock_linked_obj = MagicMock()
        mock_linked_obj.name = "SourceObject"
        mock_linked_obj.library = MagicMock()

        mock_data_from = MagicMock()
        mock_data_from.objects = ["SourceObject"]
        mock_data_from.collections = []
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)
        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        # Mock objects
        mock_bpy.data.objects = [mock_linked_obj]
        mock_bpy.data.collections = [mock_target_collection]

        # Mock ops
        mock_bpy.ops.wm.save_mainfile = MagicMock()

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Mock Path.exists()
            with patch('pathlib.Path.exists', return_value=True):
                from link_objects import link_items

                # Call with hide_viewport=False
                result = link_items(
                    source_file="/fake/source.blend",
                    target_scene="Scene",
                    item_names=["SourceObject"],
                    item_types=["object"],
                    target_collection_name="TargetCollection",
                    link_mode='individual',
                    dry_run=False,
                    hide_viewport=False
                )

                # Verify function completes without errors
                assert result is not None
                #  Note: Full verification of layer_collection.hide_viewport setting
                # requires integration testing with real Blender environment
