"""Dialog for selecting similar file matches."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QAbstractItemView, QComboBox
)
from PySide6.QtGui import QColor

from gui.ui_strings import TITLE_SELECT_SIMILAR_FILES, MSG_SELECT_SIMILAR_FILES


class SimilarFilesDialog(QDialog):
    """Dialog for selecting similar file matches for broken links."""

    def __init__(self, similar_files: list, project_root: Path, parent=None):
        """Initialize similar files dialog.

        Args:
            similar_files: List of similar file matches from find_and_relink.py
            project_root: Project root directory for display purposes
            parent: Parent widget
        """
        super().__init__(parent)
        self.similar_files = similar_files
        self.project_root = project_root
        self.selected_matches = {}

        self.setWindowTitle(TITLE_SELECT_SIMILAR_FILES)
        self.resize(900, 600)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        layout = QVBoxLayout(self)

        info_label = QLabel(MSG_SELECT_SIMILAR_FILES)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Missing File", "Similarity", "Similar File Found", "Action"
        ])

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.table.setRowCount(len(self.similar_files))

        for i, similar_info in enumerate(self.similar_files):
            missing_filename = similar_info.get("missing_filename", "Unknown")
            similar_matches = similar_info.get("similar_matches", [])

            missing_item = QTableWidgetItem(missing_filename)
            self.table.setItem(i, 0, missing_item)

            if similar_matches:
                best_match = similar_matches[0]
                similarity = best_match.get("similarity", 0)
                found_path = Path(best_match.get("path", ""))

                similarity_item = QTableWidgetItem(f"{similarity}%")
                self.table.setItem(i, 1, similarity_item)

                try:
                    relative_path = found_path.relative_to(self.project_root)
                    found_item = QTableWidgetItem(str(relative_path))
                except ValueError:
                    found_item = QTableWidgetItem(found_path.name)
                self.table.setItem(i, 2, found_item)

                combo = QComboBox()
                combo.addItem("Skip", None)

                for match in similar_matches:
                    match_path = Path(match.get("path", ""))
                    match_similarity = match.get("similarity", 0)
                    try:
                        rel_path = match_path.relative_to(self.project_root)
                        combo.addItem(f"{match_path.name} ({match_similarity}%) - {rel_path}", str(match_path))
                    except ValueError:
                        combo.addItem(f"{match_path.name} ({match_similarity}%)", str(match_path))

                combo.setCurrentIndex(1)
                combo.currentIndexChanged.connect(lambda idx, row=i: self._on_selection_changed(row, idx))

                self.table.setCellWidget(i, 3, combo)

                self._on_selection_changed(i, 1)

                if similarity >= 80:
                    for col in range(3):
                        self.table.item(i, col).setBackground(QColor(230, 255, 230))
                        self.table.item(i, col).setForeground(QColor(0, 100, 0))
                elif similarity >= 60:
                    for col in range(3):
                        self.table.item(i, col).setBackground(QColor(255, 250, 205))
                        self.table.item(i, col).setForeground(QColor(139, 69, 19))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        summary_label = QLabel(f"<i>Tip: Green rows have high similarity (≥80%), yellow rows are moderate (60-79%)</i>")
        layout.addWidget(summary_label)

        btn_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All Best Matches")
        select_all_btn.setToolTip("Use the best match for all files")
        select_all_btn.clicked.connect(self._select_all_best)
        btn_layout.addWidget(select_all_btn)

        skip_all_btn = QPushButton("Skip All")
        skip_all_btn.setToolTip("Skip all similar matches")
        skip_all_btn.clicked.connect(self._skip_all)
        btn_layout.addWidget(skip_all_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Apply Selected")
        ok_btn.setProperty("class", "primary")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _on_selection_changed(self, row: int, combo_index: int):
        """Handle combo box selection change.

        Args:
            row: Row index
            combo_index: Combo box index
        """
        combo = self.table.cellWidget(row, 3)
        selected_path = combo.itemData(combo_index)

        if selected_path:
            missing_path = self.similar_files[row].get("missing_path", "")
            self.selected_matches[missing_path] = selected_path
        else:
            missing_path = self.similar_files[row].get("missing_path", "")
            if missing_path in self.selected_matches:
                del self.selected_matches[missing_path]

    def _select_all_best(self):
        """Select the best match for all files."""
        for i in range(self.table.rowCount()):
            combo = self.table.cellWidget(i, 3)
            if combo.count() > 1:
                combo.setCurrentIndex(1)

    def _skip_all(self):
        """Skip all similar matches."""
        for i in range(self.table.rowCount()):
            combo = self.table.cellWidget(i, 3)
            combo.setCurrentIndex(0)

    def get_selected_matches(self) -> dict:
        """Get the selected file matches.

        Returns:
            Dictionary mapping old paths to new paths
        """
        return self.selected_matches
