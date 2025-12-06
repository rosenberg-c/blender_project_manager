"""Unit tests for validation logic."""

import pytest
from pathlib import Path

from core.validation import (
    validate_move_operation,
    validate_rename_operation,
    validate_link_operation,
    check_name_conflict
)


class TestValidateMoveOperation:
    """Tests for validate_move_operation function."""

    def test_valid_move(self, tmp_path):
        """Test validation of valid move operation."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        dest = tmp_path / "dest.blend"

        errors, warnings = validate_move_operation(source, dest)

        assert len(errors) == 0

    def test_source_not_exists(self, tmp_path):
        """Test validation when source doesn't exist."""
        source = tmp_path / "nonexistent.blend"
        dest = tmp_path / "dest.blend"

        errors, warnings = validate_move_operation(source, dest)

        assert len(errors) > 0
        assert any("not exist" in err.lower() for err in errors)

    def test_destination_exists(self, tmp_path):
        """Test validation when destination already exists."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        dest = tmp_path / "dest.blend"
        dest.write_text("existing")

        errors, warnings = validate_move_operation(source, dest)

        assert len(errors) > 0
        assert any("already exists" in err.lower() for err in errors)

    def test_destination_parent_not_exists(self, tmp_path):
        """Test validation when destination parent doesn't exist."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        dest = tmp_path / "nonexistent" / "dest.blend"

        errors, warnings = validate_move_operation(source, dest)

        assert len(errors) > 0

    def test_source_and_dest_same(self, tmp_path):
        """Test validation when source and dest are the same."""
        source = tmp_path / "file.blend"
        source.write_text("test")

        errors, warnings = validate_move_operation(source, source)

        assert len(errors) > 0
        assert any("same" in err.lower() for err in errors)


class TestValidateRenameOperation:
    """Tests for validate_rename_operation function."""

    def test_valid_rename(self):
        """Test validation of valid rename operation."""
        errors, warnings = validate_rename_operation(
            find_text="Cube",
            replace_text="Box",
            item_names=["Cube.001", "Cube.002"]
        )

        assert len(errors) == 0

    def test_empty_find_text(self):
        """Test validation with empty find text."""
        errors, warnings = validate_rename_operation(
            find_text="",
            replace_text="Box",
            item_names=["Cube"]
        )

        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)

    def test_find_text_not_in_items(self):
        """Test validation when find text not in any items."""
        errors, warnings = validate_rename_operation(
            find_text="NotFound",
            replace_text="Box",
            item_names=["Cube", "Sphere"]
        )

        assert len(warnings) > 0
        assert any("not found" in warn.lower() for warn in warnings)

    def test_creates_duplicate_names(self):
        """Test validation when rename creates duplicates."""
        errors, warnings = validate_rename_operation(
            find_text=".001",
            replace_text="",
            item_names=["Cube.001", "Cube.002", "Cube"]
        )

        # "Cube.001" → "Cube", "Cube.002" → "Cube", "Cube" → "Cube"
        # This creates duplicates
        assert len(warnings) > 0
        assert any("duplicate" in warn.lower() for warn in warnings)

    def test_empty_item_names(self):
        """Test validation with empty item names list."""
        errors, warnings = validate_rename_operation(
            find_text="Cube",
            replace_text="Box",
            item_names=[]
        )

        # No error, but should warn that nothing matches
        assert len(warnings) > 0


class TestValidateLinkOperation:
    """Tests for validate_link_operation function."""

    def test_valid_link_instance_mode(self, tmp_path):
        """Test validation of valid instance mode link."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="LinkedAssets",
            link_mode="instance"
        )

        assert len(errors) == 0

    def test_valid_link_individual_mode(self, tmp_path):
        """Test validation of valid individual mode link."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["Object1", "Collection1"],
            item_types=["object", "collection"],
            target_collection="LinkedAssets",
            link_mode="individual"
        )

        assert len(errors) == 0

    def test_source_not_exists(self, tmp_path):
        """Test validation when source file doesn't exist."""
        source = tmp_path / "nonexistent.blend"
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="LinkedAssets",
            link_mode="instance"
        )

        assert len(errors) > 0
        assert any("source" in err.lower() and "not exist" in err.lower() for err in errors)

    def test_target_not_exists(self, tmp_path):
        """Test validation when target file doesn't exist."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "nonexistent.blend"

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="LinkedAssets",
            link_mode="instance"
        )

        assert len(errors) > 0
        assert any("target" in err.lower() and "not exist" in err.lower() for err in errors)

    def test_mismatched_names_and_types(self, tmp_path):
        """Test validation when item names and types don't match."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["Item1", "Item2"],
            item_types=["object"],  # Only one type for two names
            target_collection="LinkedAssets",
            link_mode="individual"
        )

        assert len(errors) > 0
        assert any("match" in err.lower() for err in errors)

    def test_invalid_item_type(self, tmp_path):
        """Test validation with invalid item type."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["Item1"],
            item_types=["invalid_type"],
            target_collection="LinkedAssets",
            link_mode="individual"
        )

        assert len(errors) > 0
        assert any("invalid" in err.lower() for err in errors)

    def test_invalid_link_mode(self, tmp_path):
        """Test validation with invalid link mode."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="LinkedAssets",
            link_mode="invalid_mode"
        )

        assert len(errors) > 0
        assert any("link mode" in err.lower() for err in errors)

    def test_instance_mode_requires_one_collection(self, tmp_path):
        """Test that instance mode requires exactly one collection."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        # Multiple collections
        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["Col1", "Col2"],
            item_types=["collection", "collection"],
            target_collection="LinkedAssets",
            link_mode="instance"
        )

        assert len(errors) > 0
        assert any("one collection" in err.lower() for err in errors)

        # Objects not allowed
        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["Obj1"],
            item_types=["object"],
            target_collection="LinkedAssets",
            link_mode="instance"
        )

        assert len(errors) > 0

    def test_target_collection_name_conflict(self, tmp_path):
        """Test validation when target collection name conflicts with item."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="MyCollection",  # Same as item name!
            link_mode="instance"
        )

        assert len(errors) > 0
        assert any("conflicts" in err.lower() for err in errors)

    def test_empty_target_collection_name(self, tmp_path):
        """Test validation with empty target collection name."""
        source = tmp_path / "source.blend"
        source.write_text("test")
        target = tmp_path / "target.blend"
        target.write_text("test")

        errors, warnings = validate_link_operation(
            source_file=source,
            target_file=target,
            item_names=["MyCollection"],
            item_types=["collection"],
            target_collection="",
            link_mode="instance"
        )

        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)


class TestCheckNameConflict:
    """Tests for check_name_conflict function."""

    def test_conflict_exists(self):
        """Test when name conflict exists."""
        result = check_name_conflict("Cube", ["Cube", "Sphere", "Light"])
        assert result is True

    def test_no_conflict(self):
        """Test when no conflict exists."""
        result = check_name_conflict("Box", ["Cube", "Sphere", "Light"])
        assert result is False

    def test_empty_existing_names(self):
        """Test with empty existing names list."""
        result = check_name_conflict("Cube", [])
        assert result is False

    def test_case_sensitive(self):
        """Test that check is case-sensitive."""
        result = check_name_conflict("Cube", ["cube", "CUBE"])
        assert result is False
