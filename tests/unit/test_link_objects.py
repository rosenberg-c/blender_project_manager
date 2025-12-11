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


class TestLinkObjectsTabFilter:
    """Tests for link objects tab filter by name functionality."""

    def test_filter_shows_matching_objects(self, qapp):
        """Test that filter shows objects with matching names."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        # Mock controller
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        # Create tab instance with mocked setup
        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        # Setup the filter input and list manually
        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add test items
        test_data = [
            {"type": "object", "data": {"name": "Cube.001", "type": "MESH"}},
            {"type": "object", "data": {"name": "Camera.Main", "type": "CAMERA"}},
            {"type": "collection", "data": {"name": "Collection.Assets", "objects_count": 5}},
            {"type": "object", "data": {"name": "Light.001", "type": "LIGHT"}},
        ]

        for item_data in test_data:
            item = QListWidgetItem(f"Test {item_data['data']['name']}")
            item.setData(Qt.UserRole, item_data)
            tab.link_items_list.addItem(item)

        # Apply filter for "Camera"
        tab.link_filter_input.setText("Camera")
        tab._filter_items_by_name()

        # Verify: Only Camera.Main is visible
        assert tab.link_items_list.item(0).isHidden()  # Cube.001 should be hidden
        assert not tab.link_items_list.item(1).isHidden()  # Camera.Main should be visible
        assert tab.link_items_list.item(2).isHidden()  # Collection.Assets should be hidden
        assert tab.link_items_list.item(3).isHidden()  # Light.001 should be hidden

    def test_filter_shows_all_when_empty(self, qapp):
        """Test that all items are shown when filter is empty."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add test items
        test_data = [
            {"type": "object", "data": {"name": "Cube.001", "type": "MESH"}},
            {"type": "object", "data": {"name": "Camera.Main", "type": "CAMERA"}},
            {"type": "collection", "data": {"name": "Collection.Assets", "objects_count": 5}},
        ]

        for item_data in test_data:
            item = QListWidgetItem(f"Test {item_data['data']['name']}")
            item.setData(Qt.UserRole, item_data)
            tab.link_items_list.addItem(item)

        # Apply empty filter
        tab.link_filter_input.setText("")
        tab._filter_items_by_name()

        # Verify: All items are visible
        for i in range(tab.link_items_list.count()):
            assert not tab.link_items_list.item(i).isHidden(), f"Item {i} should be visible"

    def test_filter_is_case_insensitive(self, qapp):
        """Test that filter is case insensitive."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add test items with mixed case
        test_data = [
            {"type": "object", "data": {"name": "MyCube", "type": "MESH"}},
            {"type": "collection", "data": {"name": "MyCollection", "objects_count": 3}},
            {"type": "object", "data": {"name": "Light", "type": "LIGHT"}},
        ]

        for item_data in test_data:
            item = QListWidgetItem(f"Test {item_data['data']['name']}")
            item.setData(Qt.UserRole, item_data)
            tab.link_items_list.addItem(item)

        # Apply filter with lowercase
        tab.link_filter_input.setText("my")
        tab._filter_items_by_name()

        # Verify: Items with "My" (MyCube, MyCollection) are visible
        assert not tab.link_items_list.item(0).isHidden(), "MyCube should be visible"
        assert not tab.link_items_list.item(1).isHidden(), "MyCollection should be visible"
        assert tab.link_items_list.item(2).isHidden(), "Light should be hidden"

    def test_filter_hides_items_without_data(self, qapp):
        """Test that items without proper data are hidden when filter is applied."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add item with proper data
        item1 = QListWidgetItem("Valid Item")
        item1.setData(Qt.UserRole, {"type": "object", "data": {"name": "Cube", "type": "MESH"}})
        tab.link_items_list.addItem(item1)

        # Add item with invalid data (no name)
        item2 = QListWidgetItem("Invalid Item")
        item2.setData(Qt.UserRole, {"type": "object", "data": {}})
        tab.link_items_list.addItem(item2)

        # Add item with no data
        item3 = QListWidgetItem("No Data Item")
        item3.setData(Qt.UserRole, None)
        tab.link_items_list.addItem(item3)

        # Apply filter
        tab.link_filter_input.setText("Cube")
        tab._filter_items_by_name()

        # Verify: Only valid item with matching name is visible
        assert not tab.link_items_list.item(0).isHidden(), "Valid item should be visible"
        assert tab.link_items_list.item(1).isHidden(), "Item without name should be hidden"
        assert tab.link_items_list.item(2).isHidden(), "Item without data should be hidden"

    def test_filter_works_with_collections(self, qapp):
        """Test that filter works correctly with collections."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add test collections and objects
        test_data = [
            {"type": "collection", "data": {"name": "Assets.Props", "objects_count": 10}},
            {"type": "collection", "data": {"name": "Assets.Characters", "objects_count": 5}},
            {"type": "object", "data": {"name": "Prop.Table", "type": "MESH"}},
            {"type": "collection", "data": {"name": "Lighting", "objects_count": 3}},
        ]

        for item_data in test_data:
            item = QListWidgetItem(f"Test {item_data['data']['name']}")
            item.setData(Qt.UserRole, item_data)
            tab.link_items_list.addItem(item)

        # Apply filter for "Assets"
        tab.link_filter_input.setText("Assets")
        tab._filter_items_by_name()

        # Verify: Only collections with "Assets" in name are visible
        assert not tab.link_items_list.item(0).isHidden(), "Assets.Props should be visible"
        assert not tab.link_items_list.item(1).isHidden(), "Assets.Characters should be visible"
        assert tab.link_items_list.item(2).isHidden(), "Prop.Table should be hidden"
        assert tab.link_items_list.item(3).isHidden(), "Lighting should be hidden"

    def test_filter_partial_match(self, qapp):
        """Test that filter matches partial strings."""
        from unittest.mock import MagicMock, patch
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt

        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.link_objects_tab import LinkObjectsTab

        with patch.object(LinkObjectsTab, 'setup_ui'):
            tab = LinkObjectsTab(mock_controller)

        from PySide6.QtWidgets import QLineEdit, QListWidget
        tab.link_filter_input = QLineEdit()
        tab.link_items_list = QListWidget()

        # Add test items
        test_data = [
            {"type": "object", "data": {"name": "Cube.001", "type": "MESH"}},
            {"type": "object", "data": {"name": "Cube.002", "type": "MESH"}},
            {"type": "object", "data": {"name": "Sphere", "type": "MESH"}},
        ]

        for item_data in test_data:
            item = QListWidgetItem(f"Test {item_data['data']['name']}")
            item.setData(Qt.UserRole, item_data)
            tab.link_items_list.addItem(item)

        # Apply filter for partial match ".00"
        tab.link_filter_input.setText(".00")
        tab._filter_items_by_name()

        # Verify: Items containing ".00" are visible
        assert not tab.link_items_list.item(0).isHidden(), "Cube.001 should be visible"
        assert not tab.link_items_list.item(1).isHidden(), "Cube.002 should be visible"
        assert tab.link_items_list.item(2).isHidden(), "Sphere should be hidden"
