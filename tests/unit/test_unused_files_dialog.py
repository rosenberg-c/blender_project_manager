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

    def test_hide_file_functionality(self, qapp, tmp_path):
        """Test that files can be hidden and unhidden."""
        from gui.unused_files_dialog import UnusedFilesDialog
        from PySide6.QtWidgets import QPushButton

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
                }
            ],
            "total_unused_size": 3072,
            "unused_by_type": {
                "texture": 1,
                "blend": 1
            },
            "errors": [],
            "warnings": []
        }

        project_root = tmp_path / "project"
        project_root.mkdir()

        dialog = UnusedFilesDialog(results, project_root, None)

        # Initially no files are hidden
        assert len(dialog.hidden_files) == 0
        assert dialog.table.isRowHidden(0) == False

        # Get hide button for first row
        hide_btn = dialog.table.cellWidget(0, 5)
        assert isinstance(hide_btn, QPushButton)
        assert hide_btn.text() == "Hide"

        # Click hide button
        hide_btn.click()

        # File should now be hidden
        assert "/test/texture.png" in dialog.hidden_files
        assert hide_btn.text() == "Unhide"
        assert dialog.table.isRowHidden(0) == True  # Hidden by default

        # Enable show hidden files
        dialog.show_hidden_check.setChecked(True)
        assert dialog.table.isRowHidden(0) == False  # Visible when show_hidden is checked

        # Disable show hidden files again
        dialog.show_hidden_check.setChecked(False)
        assert dialog.table.isRowHidden(0) == True  # Hidden again

        # Click unhide button
        hide_btn.click()

        # File should no longer be hidden
        assert "/test/texture.png" not in dialog.hidden_files
        assert hide_btn.text() == "Hide"
        assert dialog.table.isRowHidden(0) == False

    def test_hidden_files_persistence(self, qapp, tmp_path):
        """Test that hidden files are persisted to config file."""
        from gui.unused_files_dialog import UnusedFilesDialog

        config_file = tmp_path / "config.json"

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
                }
            ],
            "total_unused_size": 3072,
            "unused_by_type": {
                "texture": 1,
                "blend": 1
            },
            "errors": [],
            "warnings": []
        }

        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create first dialog and hide a file
        dialog1 = UnusedFilesDialog(results, project_root, config_file)
        hide_btn = dialog1.table.cellWidget(0, 5)
        hide_btn.click()

        # Verify config file contains hidden files
        assert config_file.exists()

        with open(config_file, 'r') as f:
            config_data = json.load(f)

        assert 'unused_files_dialog' in config_data
        assert '/test/texture.png' in config_data['unused_files_dialog']['hidden_files']

        # Create second dialog and verify hidden files are restored
        dialog2 = UnusedFilesDialog(results, project_root, config_file)

        assert "/test/texture.png" in dialog2.hidden_files
        hide_btn2 = dialog2.table.cellWidget(0, 5)
        assert hide_btn2.text() == "Unhide"
        assert dialog2.table.isRowHidden(0) == True

    def test_show_hidden_checkbox_persistence(self, qapp, tmp_path):
        """Test that show hidden checkbox state is persisted."""
        from gui.unused_files_dialog import UnusedFilesDialog

        config_file = tmp_path / "config.json"

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

        # Create dialog and check show_hidden
        dialog1 = UnusedFilesDialog(results, project_root, config_file)
        dialog1.show_hidden_check.setChecked(True)

        # Verify it was saved
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        assert config_data['unused_files_dialog']['show_hidden'] == True

        # Create new dialog and verify state is restored
        dialog2 = UnusedFilesDialog(results, project_root, config_file)
        assert dialog2.show_hidden_check.isChecked() == True
