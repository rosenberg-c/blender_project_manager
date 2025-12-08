"""Unit tests for data models."""

from pathlib import Path
from datetime import datetime
import pytest


class TestImageReference:
    """Tests for ImageReference dataclass."""

    def test_create_basic_image_reference(self):
        """Test creating basic ImageReference."""
        from blender_lib.models import ImageReference

        img_ref = ImageReference(
            name="texture.png",
            filepath="//textures/texture.png",
            is_relative=True
        )

        assert img_ref.name == "texture.png"
        assert img_ref.filepath == "//textures/texture.png"
        assert img_ref.is_relative is True
        assert img_ref.resolved_path is None
        assert img_ref.exists is False

    def test_create_image_reference_with_resolved_path(self):
        """Test ImageReference with resolved path."""
        from blender_lib.models import ImageReference

        img_ref = ImageReference(
            name="texture.png",
            filepath="//textures/texture.png",
            is_relative=True,
            resolved_path=Path("/project/textures/texture.png"),
            exists=True
        )

        assert img_ref.resolved_path == Path("/project/textures/texture.png")
        assert img_ref.exists is True

    def test_absolute_path_image_reference(self):
        """Test ImageReference with absolute path."""
        from blender_lib.models import ImageReference

        img_ref = ImageReference(
            name="texture.png",
            filepath="/absolute/path/texture.png",
            is_relative=False
        )

        assert img_ref.is_relative is False
        assert img_ref.filepath == "/absolute/path/texture.png"


class TestLibraryReference:
    """Tests for LibraryReference dataclass."""

    def test_create_basic_library_reference(self):
        """Test creating basic LibraryReference."""
        from blender_lib.models import LibraryReference

        lib_ref = LibraryReference(
            name="assets.blend",
            filepath="//assets/assets.blend",
            is_relative=True
        )

        assert lib_ref.name == "assets.blend"
        assert lib_ref.filepath == "//assets/assets.blend"
        assert lib_ref.is_relative is True
        assert lib_ref.resolved_path is None
        assert lib_ref.exists is False
        assert lib_ref.linked_objects == []
        assert lib_ref.linked_collections == []

    def test_library_reference_with_linked_items(self):
        """Test LibraryReference with linked objects and collections."""
        from blender_lib.models import LibraryReference

        lib_ref = LibraryReference(
            name="assets.blend",
            filepath="//assets/assets.blend",
            is_relative=True,
            linked_objects=["Cube", "Camera"],
            linked_collections=["Collection 1"]
        )

        assert len(lib_ref.linked_objects) == 2
        assert "Cube" in lib_ref.linked_objects
        assert "Camera" in lib_ref.linked_objects
        assert len(lib_ref.linked_collections) == 1
        assert "Collection 1" in lib_ref.linked_collections

    def test_library_reference_default_factory(self):
        """Test that default factory creates new lists for each instance."""
        from blender_lib.models import LibraryReference

        lib_ref1 = LibraryReference(
            name="lib1.blend",
            filepath="//lib1.blend",
            is_relative=True
        )
        lib_ref2 = LibraryReference(
            name="lib2.blend",
            filepath="//lib2.blend",
            is_relative=True
        )

        lib_ref1.linked_objects.append("Object1")

        # Verify that lib_ref2's list is not affected
        assert len(lib_ref1.linked_objects) == 1
        assert len(lib_ref2.linked_objects) == 0


class TestBlendReferences:
    """Tests for BlendReferences dataclass."""

    def test_create_basic_blend_references(self):
        """Test creating basic BlendReferences."""
        from blender_lib.models import BlendReferences

        blend_refs = BlendReferences(
            blend_path=Path("/project/scene.blend")
        )

        assert blend_refs.blend_path == Path("/project/scene.blend")
        assert blend_refs.images == []
        assert blend_refs.libraries == []
        assert blend_refs.scan_date is None

    def test_blend_references_with_items(self):
        """Test BlendReferences with images and libraries."""
        from blender_lib.models import BlendReferences, ImageReference, LibraryReference

        img_ref = ImageReference(
            name="texture.png",
            filepath="//texture.png",
            is_relative=True
        )

        lib_ref = LibraryReference(
            name="lib.blend",
            filepath="//lib.blend",
            is_relative=True
        )

        blend_refs = BlendReferences(
            blend_path=Path("/project/scene.blend"),
            images=[img_ref],
            libraries=[lib_ref],
            scan_date=datetime(2025, 12, 8, 10, 30)
        )

        assert len(blend_refs.images) == 1
        assert blend_refs.images[0].name == "texture.png"
        assert len(blend_refs.libraries) == 1
        assert blend_refs.libraries[0].name == "lib.blend"
        assert blend_refs.scan_date == datetime(2025, 12, 8, 10, 30)


class TestPathChange:
    """Tests for PathChange dataclass."""

    def test_create_basic_path_change(self):
        """Test creating basic PathChange."""
        from blender_lib.models import PathChange

        change = PathChange(
            file_path=Path("/project/scene.blend"),
            item_type="image",
            item_name="texture.png",
            old_path="//old/texture.png",
            new_path="//new/texture.png"
        )

        assert change.file_path == Path("/project/scene.blend")
        assert change.item_type == "image"
        assert change.item_name == "texture.png"
        assert change.old_path == "//old/texture.png"
        assert change.new_path == "//new/texture.png"
        assert change.status == "ok"

    def test_path_change_with_status(self):
        """Test PathChange with different status values."""
        from blender_lib.models import PathChange

        change_ok = PathChange(
            file_path=Path("/project/scene.blend"),
            item_type="library",
            item_name="lib.blend",
            old_path="//old/lib.blend",
            new_path="//new/lib.blend",
            status="ok"
        )

        change_warning = PathChange(
            file_path=Path("/project/scene.blend"),
            item_type="image",
            item_name="texture.png",
            old_path="//texture.png",
            new_path="//new/texture.png",
            status="warning"
        )

        change_error = PathChange(
            file_path=Path("/project/scene.blend"),
            item_type="image",
            item_name="missing.png",
            old_path="//missing.png",
            new_path="//missing.png",
            status="error"
        )

        assert change_ok.status == "ok"
        assert change_warning.status == "warning"
        assert change_error.status == "error"


class TestOperationPreview:
    """Tests for OperationPreview dataclass."""

    def test_create_basic_operation_preview(self):
        """Test creating basic OperationPreview."""
        from blender_lib.models import OperationPreview

        preview = OperationPreview(
            operation_name="Move Files"
        )

        assert preview.operation_name == "Move Files"
        assert preview.changes == []
        assert preview.warnings == []
        assert preview.errors == []

    def test_operation_preview_is_valid_no_errors(self):
        """Test is_valid returns True when no errors."""
        from blender_lib.models import OperationPreview

        preview = OperationPreview(
            operation_name="Test",
            warnings=["Warning 1"]
        )

        assert preview.is_valid is True

    def test_operation_preview_is_valid_with_errors(self):
        """Test is_valid returns False when errors exist."""
        from blender_lib.models import OperationPreview

        preview = OperationPreview(
            operation_name="Test",
            errors=["Error 1", "Error 2"]
        )

        assert preview.is_valid is False

    def test_operation_preview_total_changes(self):
        """Test total_changes property."""
        from blender_lib.models import OperationPreview, PathChange

        change1 = PathChange(
            file_path=Path("/project/scene1.blend"),
            item_type="image",
            item_name="tex1.png",
            old_path="//old1.png",
            new_path="//new1.png"
        )

        change2 = PathChange(
            file_path=Path("/project/scene2.blend"),
            item_type="image",
            item_name="tex2.png",
            old_path="//old2.png",
            new_path="//new2.png"
        )

        preview = OperationPreview(
            operation_name="Test",
            changes=[change1, change2]
        )

        assert preview.total_changes == 2

    def test_operation_preview_with_all_fields(self):
        """Test OperationPreview with all fields populated."""
        from blender_lib.models import OperationPreview, PathChange

        change = PathChange(
            file_path=Path("/project/scene.blend"),
            item_type="library",
            item_name="lib.blend",
            old_path="//old/lib.blend",
            new_path="//new/lib.blend"
        )

        preview = OperationPreview(
            operation_name="Rebase Paths",
            changes=[change],
            warnings=["Warning: path will change"],
            errors=["Error: file not found"]
        )

        assert preview.operation_name == "Rebase Paths"
        assert len(preview.changes) == 1
        assert len(preview.warnings) == 1
        assert len(preview.errors) == 1
        assert preview.is_valid is False


class TestOperationResult:
    """Tests for OperationResult dataclass."""

    def test_create_success_result(self):
        """Test creating successful OperationResult."""
        from blender_lib.models import OperationResult

        result = OperationResult(
            success=True,
            message="Operation completed successfully",
            changes_made=5
        )

        assert result.success is True
        assert result.message == "Operation completed successfully"
        assert result.errors == []
        assert result.changes_made == 5

    def test_create_failure_result(self):
        """Test creating failed OperationResult."""
        from blender_lib.models import OperationResult

        result = OperationResult(
            success=False,
            message="Operation failed",
            errors=["Error 1", "Error 2"],
            changes_made=0
        )

        assert result.success is False
        assert result.message == "Operation failed"
        assert len(result.errors) == 2
        assert result.changes_made == 0

    def test_operation_result_defaults(self):
        """Test OperationResult default values."""
        from blender_lib.models import OperationResult

        result = OperationResult(success=True)

        assert result.success is True
        assert result.message == ""
        assert result.errors == []
        assert result.changes_made == 0


class TestLinkOperationParams:
    """Tests for LinkOperationParams dataclass."""

    def test_create_basic_link_operation_params(self):
        """Test creating basic LinkOperationParams."""
        from blender_lib.models import LinkOperationParams

        params = LinkOperationParams(
            target_file=Path("/project/target.blend"),
            target_scene="Scene",
            source_file=Path("/project/source.blend"),
            item_names=["Cube", "Camera"],
            item_types=["object", "object"],
            target_collection="Linked Assets"
        )

        assert params.target_file == Path("/project/target.blend")
        assert params.target_scene == "Scene"
        assert params.source_file == Path("/project/source.blend")
        assert params.item_names == ["Cube", "Camera"]
        assert params.item_types == ["object", "object"]
        assert params.target_collection == "Linked Assets"
        assert params.link_mode == "instance"

    def test_link_operation_params_custom_mode(self):
        """Test LinkOperationParams with custom link mode."""
        from blender_lib.models import LinkOperationParams

        params = LinkOperationParams(
            target_file=Path("/project/target.blend"),
            target_scene="Scene",
            source_file=Path("/project/source.blend"),
            item_names=["Collection"],
            item_types=["collection"],
            target_collection="Linked Assets",
            link_mode="individual"
        )

        assert params.link_mode == "individual"

    def test_link_operation_params_mixed_types(self):
        """Test LinkOperationParams with mixed object and collection types."""
        from blender_lib.models import LinkOperationParams

        params = LinkOperationParams(
            target_file=Path("/project/target.blend"),
            target_scene="Scene",
            source_file=Path("/project/source.blend"),
            item_names=["Cube", "Collection 1", "Camera"],
            item_types=["object", "collection", "object"],
            target_collection="Assets"
        )

        assert len(params.item_names) == 3
        assert len(params.item_types) == 3
        assert params.item_types[0] == "object"
        assert params.item_types[1] == "collection"
        assert params.item_types[2] == "object"
