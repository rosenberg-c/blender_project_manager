"""Dialog for remapping broken collection name references."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QComboBox,
    QGroupBox, QButtonGroup, QScrollArea, QWidget
)


class CollectionRemapDialog(QDialog):
    """Dialog for selecting new collection names for broken references."""

    def __init__(self, collection_refs: list, parent=None):
        """Initialize collection remap dialog.

        Args:
            collection_refs: List of broken collection reference dictionaries
            parent: Parent widget
        """
        super().__init__(parent)
        self.collection_refs = collection_refs
        self.remapping_choices = {}

        self.setWindowTitle("Remap Collection References")
        self.resize(700, 500)

        self.setup_ui()

    def setup_ui(self):
        """Create UI layout."""
        main_layout = QVBoxLayout(self)

        # Header
        if len(self.collection_refs) == 1:
            header_text = "<h2>Remap Collection Reference</h2>"
        else:
            header_text = f"<h2>Remap {len(self.collection_refs)} Collection References</h2>"

        header = QLabel(header_text)
        main_layout.addWidget(header)

        desc = QLabel(
            "Select new collection names for the broken references. "
            "The system has suggested possible matches based on similarity."
        )
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # Scrollable area for multiple collections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Create a section for each collection reference
        for i, col_ref in enumerate(self.collection_refs):
            group_box = self._create_collection_group(col_ref, i)
            scroll_layout.addWidget(group_box)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.remap_btn = QPushButton("Remap Collection(s)")
        self.remap_btn.setProperty("class", "primary")
        self.remap_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.remap_btn)

        main_layout.addLayout(btn_layout)

    def _create_collection_group(self, col_ref: dict, index: int) -> QGroupBox:
        """Create a group box for one collection reference.

        Args:
            col_ref: Collection reference dictionary
            index: Index of this reference

        Returns:
            QGroupBox widget with selection options
        """
        old_name = col_ref.get("collection_name", "Unknown")
        lib_name = col_ref.get("library_name", "Unknown")
        link_mode = col_ref.get("link_mode", "unknown")
        suggested_matches = col_ref.get("suggested_matches", [])
        available_collections = col_ref.get("available_collections", [])
        file_name = col_ref.get("file_name", "Unknown")

        group_box = QGroupBox(f"Collection: {old_name}")
        layout = QVBoxLayout()

        # Info labels
        info_text = f"<b>File:</b> {file_name}<br>"
        info_text += f"<b>Library:</b> {lib_name}<br>"
        info_text += f"<b>Link Mode:</b> {link_mode}<br>"
        info_text += f"<b>Current reference:</b> '{old_name}' (not found)"

        info_label = QLabel(info_text)
        layout.addWidget(info_label)

        # Selection options
        select_label = QLabel("<b>Select new collection:</b>")
        layout.addWidget(select_label)

        # Create button group for radio buttons
        button_group = QButtonGroup(self)
        button_group.setExclusive(True)

        # Radio buttons for suggestions
        if suggested_matches:
            for match in suggested_matches[:5]:
                name = match.get("name", "Unknown")
                similarity = match.get("similarity", 0)
                similarity_pct = int(similarity * 100)

                radio = QRadioButton(f"{name} ({similarity_pct}% match)")
                radio.setProperty("collection_name", name)
                radio.setProperty("ref_index", index)
                button_group.addButton(radio)
                layout.addWidget(radio)

                # Select best match by default
                if match == suggested_matches[0]:
                    radio.setChecked(True)
                    self.remapping_choices[index] = name
        else:
            no_suggestions_label = QLabel("<i>No similar collection names found</i>")
            layout.addWidget(no_suggestions_label)

        # Separator
        layout.addSpacing(10)

        # Manual selection option
        other_layout = QHBoxLayout()
        other_radio = QRadioButton("Other (select from dropdown):")
        other_radio.setProperty("ref_index", index)
        button_group.addButton(other_radio)
        other_layout.addWidget(other_radio)

        other_combo = QComboBox()
        other_combo.setProperty("ref_index", index)

        # Add all available collections to dropdown
        if available_collections:
            for col_name in sorted(available_collections):
                other_combo.addItem(col_name)
        else:
            other_combo.addItem("(No collections available)")
            other_combo.setEnabled(False)

        other_layout.addWidget(other_combo, stretch=1)
        layout.addLayout(other_layout)

        # Connect signals
        for button in button_group.buttons():
            button.toggled.connect(lambda checked, btn=button, combo=other_combo:
                                    self._on_selection_changed(checked, btn, combo))

        other_combo.currentTextChanged.connect(lambda text, idx=index:
                                                 self._on_combo_changed(text, idx))

        group_box.setLayout(layout)
        return group_box

    def _on_selection_changed(self, checked: bool, button: QRadioButton, combo: QComboBox):
        """Handle radio button selection change.

        Args:
            checked: Whether button is checked
            button: The radio button
            combo: The combo box for "Other" option
        """
        if not checked:
            return

        ref_index = button.property("ref_index")
        collection_name = button.property("collection_name")

        if collection_name:
            # One of the suggested matches
            self.remapping_choices[ref_index] = collection_name
        else:
            # "Other" option - use combo box value
            combo_index = combo.property("ref_index")
            if combo_index == ref_index and combo.currentText() and combo.currentText() != "(No collections available)":
                self.remapping_choices[ref_index] = combo.currentText()

    def _on_combo_changed(self, text: str, index: int):
        """Handle combo box selection change.

        Args:
            text: Selected text
            index: Reference index
        """
        if text and text != "(No collections available)":
            self.remapping_choices[index] = text

    def get_remappings(self) -> list:
        """Get the selected remappings.

        Returns:
            List of remapping dictionaries with old name, new name, and metadata
        """
        remappings = []

        for i, col_ref in enumerate(self.collection_refs):
            new_name = self.remapping_choices.get(i)

            if new_name:
                remappings.append({
                    "file": col_ref.get("file"),
                    "file_name": col_ref.get("file_name"),
                    "library_name": col_ref.get("library_name"),
                    "library_filepath": col_ref.get("library_filepath"),
                    "old_collection_name": col_ref.get("collection_name"),
                    "new_collection_name": new_name,
                    "link_mode": col_ref.get("link_mode"),
                    "instance_object_name": col_ref.get("instance_object_name")
                })

        return remappings
