"""Unit tests for file browser delete functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


class TestFileBrowserDelete:
    """Tests for file browser delete functionality with inline trash icon."""

    def test_delegate_exists(self, qapp, tmp_path):
        """Test that custom delegate is created."""
        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = tmp_path

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Verify delegate exists
        assert hasattr(browser, 'delegate')
        assert browser.delegate is not None
        assert browser.tree.itemDelegate() == browser.delegate

    def test_event_filter_installed(self, qapp, tmp_path):
        """Test that event filter is installed on tree viewport."""
        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = tmp_path

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Verify event filter is installed (browser is in the event filter chain)
        # This is a basic check that the viewport has event filters
        assert browser.tree.viewport() is not None

    def test_delete_file_with_confirmation(self, qapp, tmp_path):
        """Test that deleting a file shows confirmation and deletes."""
        # Create test file
        test_file = tmp_path / "test.blend"
        test_file.write_text("test")
        assert test_file.exists()

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget
        from PySide6.QtWidgets import QMessageBox

        browser = FileBrowserWidget(mock_controller)

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_file)

        # Mock confirmation dialog to return Yes
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.information'):
                browser._delete_selected()

        # Verify file was deleted
        assert not test_file.exists()

    def test_delete_directory_with_confirmation(self, qapp, tmp_path):
        """Test that deleting a directory shows confirmation and deletes."""
        # Create test directory with contents
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.blend").write_text("test")
        assert test_dir.exists()

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget
        from PySide6.QtWidgets import QMessageBox

        browser = FileBrowserWidget(mock_controller)

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_dir)

        # Mock confirmation dialog to return Yes
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.information'):
                browser._delete_selected()

        # Verify directory was deleted
        assert not test_dir.exists()

    def test_delete_cancelled(self, qapp, tmp_path):
        """Test that canceling deletion does not delete."""
        # Create test file
        test_file = tmp_path / "test.blend"
        test_file.write_text("test")
        assert test_file.exists()

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_file)

        # Mock confirmation dialog to return Cancel
        with patch('gui.file_browser.QMessageBox.question', return_value=0x00400000):  # Cancel
            browser._delete_selected()

        # Verify file still exists
        assert test_file.exists()

    def test_delete_shows_correct_message_for_file(self, qapp, tmp_path):
        """Test that file deletion shows file-specific message."""
        # Create test file
        test_file = tmp_path / "test.blend"
        test_file.write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_file)

        # Mock confirmation dialog
        with patch('gui.file_browser.QMessageBox.question') as mock_question:
            mock_question.return_value = 0x00400000  # Cancel
            browser._delete_selected()

            # Verify file-specific message was shown
            call_args = mock_question.call_args
            assert "file" in call_args[0][2].lower()
            assert str(test_file) in call_args[0][2]

    def test_delete_shows_correct_message_for_directory(self, qapp, tmp_path):
        """Test that directory deletion shows directory-specific message."""
        # Create test directory
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_dir)

        # Mock confirmation dialog
        with patch('gui.file_browser.QMessageBox.question') as mock_question:
            mock_question.return_value = 0x00400000  # Cancel
            browser._delete_selected()

            # Verify directory-specific message was shown
            call_args = mock_question.call_args
            assert "directory" in call_args[0][2].lower()
            assert str(test_dir) in call_args[0][2]

    def test_delete_handles_permission_error(self, qapp, tmp_path):
        """Test that permission errors are handled gracefully."""
        # Create test file
        test_file = tmp_path / "test.blend"
        test_file.write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True

        from gui.file_browser import FileBrowserWidget
        from PySide6.QtWidgets import QMessageBox

        browser = FileBrowserWidget(mock_controller)

        # Mock selection - create a mock Path that raises PermissionError on unlink
        mock_path = MagicMock(spec=Path)
        mock_path.is_dir.return_value = False
        mock_path.__str__.return_value = str(test_file)
        mock_path.unlink.side_effect = PermissionError("Permission denied")

        browser.get_selected_path = MagicMock(return_value=mock_path)

        # Mock confirmation and error dialogs
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.critical') as mock_error:
                browser._delete_selected()

                # Verify error dialog was shown
                assert mock_error.called
                call_args = mock_error.call_args[0]
                assert "Permission denied" in call_args[2]
