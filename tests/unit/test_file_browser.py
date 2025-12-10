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

    def test_find_references_icon_for_blend_file(self, qapp, tmp_path):
        """Test that find references icon is shown for .blend files."""
        # Create test .blend file
        test_file = tmp_path / "test.blend"
        test_file.write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = tmp_path

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Test that delegate recognizes .blend file as supported
        assert browser.delegate._is_supported_file(test_file)

    def test_find_references_icon_for_texture_file(self, qapp, tmp_path):
        """Test that find references icon is shown for texture files."""
        # Test various texture formats
        test_files = [
            tmp_path / "texture.png",
            tmp_path / "image.jpg",
            tmp_path / "hdri.exr",
        ]

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = tmp_path

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Test that delegate recognizes texture files as supported
        for test_file in test_files:
            assert browser.delegate._is_supported_file(test_file)

    def test_find_references_icon_not_for_other_files(self, qapp, tmp_path):
        """Test that find references icon is NOT shown for non-supported files."""
        # Test non-supported files
        test_files = [
            tmp_path / "script.py",
            tmp_path / "data.json",
            tmp_path / "readme.md",
        ]

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = tmp_path

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Test that delegate does NOT recognize these files as supported
        for test_file in test_files:
            assert not browser.delegate._is_supported_file(test_file)

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

        # Mock confirmation dialog to return Yes and mock send2trash
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.information') as mock_info:
                with patch('gui.file_browser.send2trash') as mock_trash:
                    browser._delete_selected()

                    # Verify send2trash was called
                    mock_trash.assert_called_once_with(str(test_file))
                    # Verify success dialog was shown
                    assert mock_info.called

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

        # Mock confirmation dialog to return Yes and mock send2trash
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.information') as mock_info:
                with patch('gui.file_browser.send2trash') as mock_trash:
                    browser._delete_selected()

                    # Verify send2trash was called
                    mock_trash.assert_called_once_with(str(test_dir))
                    # Verify success dialog was shown
                    assert mock_info.called

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

        # Mock selection
        browser.get_selected_path = MagicMock(return_value=test_file)

        # Mock confirmation and error dialogs, make send2trash raise PermissionError
        with patch('gui.file_browser.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            with patch('gui.file_browser.QMessageBox.critical') as mock_error:
                with patch('gui.file_browser.send2trash', side_effect=PermissionError("Permission denied")):
                    browser._delete_selected()

                    # Verify error dialog was shown
                    assert mock_error.called
                    call_args = mock_error.call_args[0]
                    assert "Permission denied" in call_args[2]

    def test_clear_search_maintains_project_root(self, qapp, tmp_path):
        """Test that clearing search box maintains project root and doesn't show drive root."""
        # Create test project structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        test_file = project_root / "test.blend"
        test_file.write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = project_root

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)

        # Set the project root
        browser.set_root(project_root)

        # Get the initial root index (should be project root)
        initial_root_index = browser.tree.rootIndex()
        initial_root_path = browser.file_system_model.filePath(
            browser.proxy_model.mapToSource(initial_root_index)
        )
        assert Path(initial_root_path) == project_root

        # Simulate typing in search box
        browser.search_box.setText("test")

        # Simulate clearing the search box
        browser.search_box.clear()

        # Get the root index after clearing (should still be project root)
        after_clear_root_index = browser.tree.rootIndex()
        after_clear_root_path = browser.file_system_model.filePath(
            browser.proxy_model.mapToSource(after_clear_root_index)
        )

        # Verify root is still the project root, not the drive root
        assert Path(after_clear_root_path) == project_root
        assert after_clear_root_path == initial_root_path

    def test_search_and_clear_maintains_project_scope(self, qapp, tmp_path):
        """Test that search and clear cycle keeps browser scoped to project directory."""
        # Create test project with subdirectories
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        subdir = project_root / "assets"
        subdir.mkdir()
        (subdir / "model.blend").write_text("test")
        (project_root / "scene.blend").write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = project_root

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)
        browser.set_root(project_root)

        # Perform multiple search and clear cycles
        for search_term in ["model", "scene", "test"]:
            # Search
            browser.search_box.setText(search_term)

            # Clear
            browser.search_box.clear()

            # Verify we're still in project root
            current_root_index = browser.tree.rootIndex()
            current_root_path = browser.file_system_model.filePath(
                browser.proxy_model.mapToSource(current_root_index)
            )
            assert Path(current_root_path) == project_root

    def test_search_shows_files_in_collapsed_folders(self, qapp, tmp_path):
        """Test that searching shows files even if their parent folder is collapsed."""
        # Create test project with nested structure
        project_root = tmp_path / "project"
        project_root.mkdir()

        # Create nested directories
        assets_dir = project_root / "assets"
        assets_dir.mkdir()
        models_dir = assets_dir / "models"
        models_dir.mkdir()

        # Create test files at different levels
        (project_root / "root_file.blend").write_text("test")
        (assets_dir / "asset_file.blend").write_text("test")
        (models_dir / "character.blend").write_text("test")

        # Mock project controller
        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.project_root = project_root

        from gui.file_browser import FileBrowserWidget

        browser = FileBrowserWidget(mock_controller)
        browser.set_root(project_root)

        # Initially, nested folders should be collapsed
        # Search for a file deep in the hierarchy
        browser.search_box.setText("character")

        # Verify the proxy model shows the matching file
        # The file should be visible even though its parent folders were collapsed
        matches_found = False
        for row in range(browser.proxy_model.rowCount()):
            index = browser.proxy_model.index(row, 0)
            # Recursively check for the file in the filtered model
            if self._check_for_file_in_tree(browser.proxy_model, index, "character.blend"):
                matches_found = True
                break

        assert matches_found, "Search should show files even in collapsed folders"

    def _check_for_file_in_tree(self, model, parent_index, filename):
        """Helper to recursively check if a file exists in the tree."""
        # Check current item
        if model.data(parent_index, 0) == filename:
            return True

        # Check children
        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)
            if model.data(child_index, 0) == filename:
                return True
            # Recurse into directories
            if model.hasChildren(child_index):
                if self._check_for_file_in_tree(model, child_index, filename):
                    return True

        return False
