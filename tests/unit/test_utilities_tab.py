"""Unit tests for utilities_tab functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestRemoveEmptyDirectories:
    """Tests for removing empty directories functionality."""

    def test_finds_empty_directories(self, tmp_path):
        """Test that empty directories are correctly identified."""
        # Setup: Create directory structure with empty and non-empty dirs
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create empty directories
        empty1 = project_root / "empty1"
        empty1.mkdir()

        empty2 = project_root / "subdir" / "empty2"
        empty2.parent.mkdir()
        empty2.mkdir()

        # Create non-empty directory
        non_empty = project_root / "non_empty"
        non_empty.mkdir()
        (non_empty / "file.txt").write_text("content")

        # Mock the GUI components
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.utilities_tab import UtilitiesTab

        # Create a minimal tab instance
        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        # Mock GUI methods
        tab.get_project_root = MagicMock(return_value=project_root)
        tab.show_warning = MagicMock()
        tab.show_info = MagicMock()
        tab.show_error = MagicMock()
        tab.confirm = MagicMock(return_value=True)
        tab.with_loading_cursor = lambda func: func()

        # Execute
        tab._remove_empty_directories()

        # Verify: confirm was called with correct count
        assert tab.confirm.called
        confirm_args = tab.confirm.call_args[0]
        assert "2 empty directories" in confirm_args[1]

        # Verify: Both empty directories were removed
        assert not empty1.exists(), "empty1 should be removed"
        assert not empty2.exists(), "empty2 should be removed"

        # Verify: Non-empty directory still exists
        assert non_empty.exists(), "non_empty should still exist"

        # Verify: Success message was shown
        assert tab.show_info.called
        info_args = tab.show_info.call_args[0]
        assert "Successfully removed 2 empty directories" in info_args[1]

    def test_handles_nested_empty_directories(self, tmp_path):
        """Test that nested empty directories are all removed."""
        # Setup: Create nested empty directories
        project_root = tmp_path / "project"
        project_root.mkdir()

        nested = project_root / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)

        # Mock components
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.utilities_tab import UtilitiesTab

        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        tab.get_project_root = MagicMock(return_value=project_root)
        tab.show_info = MagicMock()
        tab.confirm = MagicMock(return_value=True)
        tab.with_loading_cursor = lambda func: func()

        # Execute
        tab._remove_empty_directories()

        # Verify: All nested directories were removed
        assert not (project_root / "level1").exists(), "All nested empty dirs should be removed"

        # Verify: Success message shows all 3 were removed
        info_args = tab.show_info.call_args[0]
        assert "Successfully removed 3 empty directories" in info_args[1]

    def test_no_empty_directories_found(self, tmp_path):
        """Test behavior when no empty directories exist."""
        # Setup: Project with only non-empty directories
        project_root = tmp_path / "project"
        project_root.mkdir()

        dir1 = project_root / "dir1"
        dir1.mkdir()
        (dir1 / "file.txt").write_text("content")

        # Mock components
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.utilities_tab import UtilitiesTab

        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        tab.get_project_root = MagicMock(return_value=project_root)
        tab.show_info = MagicMock()
        tab.confirm = MagicMock()

        # Execute
        tab._remove_empty_directories()

        # Verify: Info message shown (not confirm)
        assert tab.show_info.called
        info_args = tab.show_info.call_args[0]
        assert "No empty directories found" in info_args[1]

        # Verify: Confirm was NOT called (nothing to remove)
        assert not tab.confirm.called

    def test_user_cancels_removal(self, tmp_path):
        """Test that directories are not removed when user cancels."""
        # Setup: Create empty directory
        project_root = tmp_path / "project"
        project_root.mkdir()

        empty_dir = project_root / "empty"
        empty_dir.mkdir()

        # Mock components
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.utilities_tab import UtilitiesTab

        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        tab.get_project_root = MagicMock(return_value=project_root)
        tab.show_info = MagicMock()
        tab.confirm = MagicMock(return_value=False)  # User cancels

        # Execute
        tab._remove_empty_directories()

        # Verify: Directory still exists
        assert empty_dir.exists(), "Directory should not be removed when user cancels"

        # Verify: No success message shown
        assert not tab.show_info.called

    def test_handles_permission_errors(self, tmp_path):
        """Test that permission errors are handled gracefully."""
        # Setup: Create directory structure
        project_root = tmp_path / "project"
        project_root.mkdir()

        removable = project_root / "removable"
        removable.mkdir()

        # Mock components
        mock_controller = MagicMock()
        mock_controller.project.is_open = True

        from gui.operations.utilities_tab import UtilitiesTab

        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        tab.get_project_root = MagicMock(return_value=project_root)
        tab.show_info = MagicMock()
        tab.confirm = MagicMock(return_value=True)

        # Mock rmdir to raise PermissionError for one directory
        original_rmdir = Path.rmdir

        def mock_rmdir(self):
            if self.name == "removable":
                raise PermissionError("Permission denied")
            original_rmdir(self)

        with patch.object(Path, 'rmdir', mock_rmdir):
            tab.with_loading_cursor = lambda func: func()
            tab._remove_empty_directories()

        # Verify: Error is shown in results
        info_args = tab.show_info.call_args[0]
        assert "Failed to remove 1 directory" in info_args[1]
        assert "Permission denied" in info_args[1]

    def test_requires_open_project(self):
        """Test that operation requires an open project."""
        # Mock components
        mock_controller = MagicMock()
        mock_controller.project.is_open = False  # No project open

        from gui.operations.utilities_tab import UtilitiesTab

        with patch.object(UtilitiesTab, 'setup_ui'):
            tab = UtilitiesTab(mock_controller)

        tab.show_warning = MagicMock()

        # Execute
        tab._remove_empty_directories()

        # Verify: Warning shown
        assert tab.show_warning.called
        warning_args = tab.show_warning.call_args[0]
        assert "No Project" in warning_args[0]
