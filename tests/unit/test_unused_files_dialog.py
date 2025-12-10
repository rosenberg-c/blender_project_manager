"""Tests for unused files dialog."""

import json
from pathlib import Path
import pytest


class TestUnusedFilesDialog:
    """Test cases for UnusedFilesDialog."""

    def test_checkbox_state_persistence(self, qapp, tmp_path):
        """Test that checkbox states are persisted to config file."""
        from gui.unused_files_dialog import UnusedFilesDialog

        # Create config file
        config_file = tmp_path / "config.json"

        # Create test results
        results = {
            "success": True,
            "unused_files": [
                {
                    "path": "/test/texture.png",
                    "name": "texture.png",
                    "type": "texture",
                    "size": 1024,
                    "relative_path": "texture.png"
                },
                {
                    "path": "/test/file.blend",
                    "name": "file.blend",
                    "type": "blend",
                    "size": 2048,
                    "relative_path": "file.blend"
                },
                {
                    "path": "/test/backup.blend1",
                    "name": "backup.blend1",
                    "type": "backup",
                    "size": 512,
                    "relative_path": "backup.blend1"
                }
            ],
            "total_unused_size": 3584,
            "unused_by_type": {
                "texture": 1,
                "blend": 1,
                "backup": 1
            },
            "errors": [],
            "warnings": []
        }

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create first dialog and change checkbox states
        dialog1 = UnusedFilesDialog(results, project_root, config_file)
        dialog1.show_textures_check.setChecked(False)
        dialog1.show_blends_check.setChecked(True)
        dialog1.show_backups_check.setChecked(False)

        # Verify config file was created and contains correct states
        assert config_file.exists()

        with open(config_file, 'r') as f:
            config_data = json.load(f)

        assert 'unused_files_dialog' in config_data
        assert config_data['unused_files_dialog']['show_textures'] == False
        assert config_data['unused_files_dialog']['show_blends'] == True
        assert config_data['unused_files_dialog']['show_backups'] == False

        # Create second dialog and verify states are restored
        dialog2 = UnusedFilesDialog(results, project_root, config_file)

        assert dialog2.show_textures_check.isChecked() == False
        assert dialog2.show_blends_check.isChecked() == True
        assert dialog2.show_backups_check.isChecked() == False

    def test_checkbox_default_states_without_config(self, qapp, tmp_path):
        """Test that checkboxes default to checked when no config exists."""
        from gui.unused_files_dialog import UnusedFilesDialog

        results = {
            "success": True,
            "unused_files": [
                {
                    "path": "/test/texture.png",
                    "name": "texture.png",
                    "type": "texture",
                    "size": 1024,
                    "relative_path": "texture.png"
                }
            ],
            "total_unused_size": 1024,
            "unused_by_type": {"texture": 1},
            "errors": [],
            "warnings": []
        }

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create dialog without config file
        dialog = UnusedFilesDialog(results, project_root, None)

        # All checkboxes should default to checked
        assert dialog.show_textures_check.isChecked() == True
        assert dialog.show_blends_check.isChecked() == True
        assert dialog.show_backups_check.isChecked() == True

    def test_checkbox_filters_work(self, qapp, tmp_path):
        """Test that checkbox filters correctly show/hide rows."""
        from gui.unused_files_dialog import UnusedFilesDialog

        results = {
            "success": True,
            "unused_files": [
                {
                    "path": "/test/texture.png",
                    "name": "texture.png",
                    "type": "texture",
                    "size": 1024,
                    "relative_path": "texture.png"
                },
                {
                    "path": "/test/file.blend",
                    "name": "file.blend",
                    "type": "blend",
                    "size": 2048,
                    "relative_path": "file.blend"
                },
                {
                    "path": "/test/backup.blend1",
                    "name": "backup.blend1",
                    "type": "backup",
                    "size": 512,
                    "relative_path": "backup.blend1"
                }
            ],
            "total_unused_size": 3584,
            "unused_by_type": {
                "texture": 1,
                "blend": 1,
                "backup": 1
            },
            "errors": [],
            "warnings": []
        }

        project_root = tmp_path / "project"
        project_root.mkdir()

        dialog = UnusedFilesDialog(results, project_root, None)

        # Initially all rows should be visible
        assert dialog.table.isRowHidden(0) == False  # texture
        assert dialog.table.isRowHidden(1) == False  # blend
        assert dialog.table.isRowHidden(2) == False  # backup

        # Uncheck textures
        dialog.show_textures_check.setChecked(False)

        assert dialog.table.isRowHidden(0) == True   # texture hidden
        assert dialog.table.isRowHidden(1) == False  # blend visible
        assert dialog.table.isRowHidden(2) == False  # backup visible

        # Uncheck blends
        dialog.show_blends_check.setChecked(False)

        assert dialog.table.isRowHidden(0) == True   # texture hidden
        assert dialog.table.isRowHidden(1) == True   # blend hidden
        assert dialog.table.isRowHidden(2) == False  # backup visible

        # Uncheck backups (all hidden)
        dialog.show_backups_check.setChecked(False)

        assert dialog.table.isRowHidden(0) == True   # texture hidden
        assert dialog.table.isRowHidden(1) == True   # blend hidden
        assert dialog.table.isRowHidden(2) == True   # backup hidden

        # Re-check all
        dialog.show_textures_check.setChecked(True)
        dialog.show_blends_check.setChecked(True)
        dialog.show_backups_check.setChecked(True)

        assert dialog.table.isRowHidden(0) == False  # texture visible
        assert dialog.table.isRowHidden(1) == False  # blend visible
        assert dialog.table.isRowHidden(2) == False  # backup visible
