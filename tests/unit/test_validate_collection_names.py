"""Unit tests for validate_collection_names Blender script."""

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest


class TestValidateCollectionNames:
    """Tests for collection name validation functionality."""

    def test_similarity_ratio_identical(self):
        """Test similarity ratio returns 1.0 for identical strings."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy to allow import
        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import similarity_ratio

            assert similarity_ratio("Tree", "Tree") == 1.0
            assert similarity_ratio("tree", "TREE") == 1.0  # Case insensitive

    def test_similarity_ratio_partial_match(self):
        """Test similarity ratio for partial matches."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import similarity_ratio

            # Tree and Tree_v2 should have high similarity
            ratio = similarity_ratio("Tree", "Tree_v2")
            assert ratio > 0.7

            # Tree and Oak should have low similarity
            ratio = similarity_ratio("Tree", "Oak")
            assert ratio < 0.5

    def test_find_similar_collection_names(self):
        """Test fuzzy matching finds similar collection names."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import find_similar_collection_names

            available = ["Tree_v2", "Tree_Oak", "Oak", "TreeLarge", "Bush"]
            matches = find_similar_collection_names("Tree", available, threshold=0.6)

            # Should return matches sorted by similarity
            assert len(matches) > 0
            assert matches[0]["name"] in ["Tree_v2", "TreeLarge", "Tree_Oak"]
            assert matches[0]["similarity"] > 0.6

            # Should not include "Oak" or "Bush" as they're too different
            match_names = [m["name"] for m in matches]
            assert "Bush" not in match_names

    def test_find_similar_no_matches_above_threshold(self):
        """Test fuzzy matching returns empty when no matches above threshold."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        mock_bpy = MagicMock()
        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import find_similar_collection_names

            available = ["Oak", "Bush", "Rock", "Grass"]
            matches = find_similar_collection_names("Tree", available, threshold=0.9)

            # No matches should be above 90% similarity
            assert len(matches) == 0

    def test_get_collections_from_library(self):
        """Test reading collection names from a library file."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Mock bpy.data.libraries.load context manager
        mock_bpy = MagicMock()
        mock_data_from = MagicMock()
        mock_data_from.collections = ["Tree_v2", "Oak", "Bush"]
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import get_collections_from_library

            library_path = Path("/fake/path/assets.blend")
            collections = get_collections_from_library(library_path)

            # Should return the list of collections
            assert collections == ["Tree_v2", "Oak", "Bush"]
            mock_bpy.data.libraries.load.assert_called_once_with(str(library_path), link=False)

    def test_detect_link_mode_instance(self):
        """Test detecting instance mode collection linking."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Create mock Empty object with collection instance
        mock_bpy = MagicMock()
        mock_library = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "Tree"
        mock_collection.library = mock_library

        mock_empty = MagicMock()
        mock_empty.name = "Tree_Instance"
        mock_empty.instance_type = 'COLLECTION'
        mock_empty.instance_collection = mock_collection

        mock_bpy.data.objects = [mock_empty]

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import detect_link_mode

            result = detect_link_mode("Tree", mock_library)

            assert result["mode"] == "instance"
            assert result["instance_object_name"] == "Tree_Instance"

    def test_detect_link_mode_individual(self):
        """Test detecting individual mode collection linking."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # No Empty objects with collection instance
        mock_bpy = MagicMock()
        mock_library = MagicMock()
        mock_bpy.data.objects = []

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            from validate_collection_names import detect_link_mode

            result = detect_link_mode("Tree", mock_library)

            assert result["mode"] == "individual"
            assert result["instance_object_name"] is None

    def test_validate_detects_renamed_collection(self, tmp_path):
        """Test that validation detects when a collection name doesn't exist in library."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        # Setup paths
        blend_file = tmp_path / "scene.blend"
        library_path = tmp_path / "assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.path.abspath = lambda p: str(library_path)

        # Mock library with broken collection reference
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//assets.blend"

        # Mock collection that's linked but doesn't exist in source
        mock_collection = MagicMock()
        mock_collection.name = "Tree"
        mock_collection.library = mock_library

        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.collections = [mock_collection]
        mock_bpy.data.objects = []

        # Mock library loading to return different collection names
        mock_data_from = MagicMock()
        mock_data_from.collections = ["Tree_v2", "Oak"]  # Tree doesn't exist, Tree_v2 does
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            # Need to mock os.path.exists as well
            with patch('os.path.exists', return_value=True):
                from validate_collection_names import validate_collection_names_in_file

                result = validate_collection_names_in_file(blend_file)

                # Should detect broken reference
                assert result["total_broken"] == 1
                assert len(result["broken_collection_refs"]) == 1

                broken_ref = result["broken_collection_refs"][0]
                assert broken_ref["collection_name"] == "Tree"
                assert broken_ref["library_name"] == "assets.blend"

                # Should suggest Tree_v2
                assert len(broken_ref["suggested_matches"]) > 0
                assert broken_ref["suggested_matches"][0]["name"] == "Tree_v2"

    def test_validate_handles_valid_collections(self, tmp_path):
        """Test that validation doesn't flag valid collection references."""
        import sys
        blender_lib_path = str(Path(__file__).parent.parent.parent / "blender_lib")
        if blender_lib_path not in sys.path:
            sys.path.insert(0, blender_lib_path)

        blend_file = tmp_path / "scene.blend"
        library_path = tmp_path / "assets.blend"

        # Mock bpy
        mock_bpy = MagicMock()
        mock_bpy.ops.wm.open_mainfile = MagicMock()
        mock_bpy.path.abspath = lambda p: str(library_path)

        # Mock library
        mock_library = MagicMock()
        mock_library.name = "assets.blend"
        mock_library.filepath = "//assets.blend"

        # Mock collection that exists in source
        mock_collection = MagicMock()
        mock_collection.name = "Tree"
        mock_collection.library = mock_library

        mock_bpy.data.libraries = [mock_library]
        mock_bpy.data.collections = [mock_collection]
        mock_bpy.data.objects = []

        # Mock library loading - Tree exists
        mock_data_from = MagicMock()
        mock_data_from.collections = ["Tree", "Oak", "Bush"]
        mock_data_to = MagicMock()

        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=(mock_data_from, mock_data_to))
        mock_context.__exit__ = MagicMock(return_value=False)

        mock_bpy.data.libraries.load = MagicMock(return_value=mock_context)

        with patch.dict('sys.modules', {'bpy': mock_bpy}):
            with patch('os.path.exists', return_value=True):
                from validate_collection_names import validate_collection_names_in_file

                result = validate_collection_names_in_file(blend_file)

                # Should not detect any broken references
                assert result["total_broken"] == 0
                assert len(result["broken_collection_refs"]) == 0
