"""Application theme and styling."""


class Theme:
    """Centralized theme configuration for the application."""

    # Current theme mode
    current_theme = 'light'

    # Light theme color palette
    COLORS_LIGHT = {
        # Background colors
        'bg_main': '#ffffff',
        'bg_secondary': '#f5f5f5',
        'bg_tertiary': '#e8e8e8',
        'bg_dark': '#2c3e50',

        # Text colors
        'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'text_light': '#95a5a6',
        'text_inverse': '#ffffff',

        # Border colors
        'border_light': '#dcdcdc',
        'border_medium': '#cccccc',
        'border_dark': '#999999',

        # Status colors
        'success': '#27ae60',
        'success_hover': '#229954',
        'warning': '#f39c12',
        'warning_hover': '#d68910',
        'error': '#c0392b',
        'error_hover': '#a93226',
        'info': '#3498db',
        'info_hover': '#2980b9',

        # Semantic colors
        'primary': '#2ecc71',
        'primary_hover': '#27ae60',
        'accent': '#3498db',
        'accent_hover': '#2980b9',

        # Table row colors
        'row_ok': '#e8f8f5',
        'row_warning': '#fef5e7',
        'row_error': '#fadbd8',
    }

    # Dark theme color palette
    COLORS_DARK = {
        # Background colors
        'bg_main': '#1e1e1e',
        'bg_secondary': '#2d2d2d',
        'bg_tertiary': '#3d3d3d',
        'bg_dark': '#0d0d0d',

        # Text colors
        'text_primary': '#e0e0e0',
        'text_secondary': '#b0b0b0',
        'text_light': '#808080',
        'text_inverse': '#1e1e1e',

        # Border colors
        'border_light': '#3d3d3d',
        'border_medium': '#505050',
        'border_dark': '#707070',

        # Status colors
        'success': '#27ae60',
        'success_hover': '#2ecc71',
        'warning': '#f39c12',
        'warning_hover': '#f5b041',
        'error': '#c0392b',
        'error_hover': '#e74c3c',
        'info': '#3498db',
        'info_hover': '#5dade2',

        # Semantic colors
        'primary': '#2ecc71',
        'primary_hover': '#27ae60',
        'accent': '#3498db',
        'accent_hover': '#5dade2',

        # Table row colors
        'row_ok': '#1a3329',
        'row_warning': '#3d3319',
        'row_error': '#3d1f1f',
    }

    @classmethod
    def get_colors(cls) -> dict:
        """Get the current theme's color palette.

        Returns:
            Color palette dictionary
        """
        if cls.current_theme == 'dark':
            return cls.COLORS_DARK
        return cls.COLORS_LIGHT

    @classmethod
    def set_theme(cls, theme: str):
        """Set the current theme.

        Args:
            theme: 'light' or 'dark'
        """
        if theme in ('light', 'dark'):
            cls.current_theme = theme

    @classmethod
    def toggle_theme(cls) -> str:
        """Toggle between light and dark themes.

        Returns:
            New theme name
        """
        cls.current_theme = 'dark' if cls.current_theme == 'light' else 'light'
        return cls.current_theme

    # Spacing
    SPACING = {
        'xs': '2px',
        'sm': '5px',
        'md': '10px',
        'lg': '15px',
        'xl': '20px',
    }

    # Border radius
    RADIUS = {
        'sm': '3px',
        'md': '5px',
        'lg': '8px',
    }

    # Font sizes
    FONT_SIZE = {
        'xs': '10px',
        'sm': '11px',
        'md': '12px',
        'lg': '14px',
        'xl': '16px',
    }

    @classmethod
    def get_stylesheet(cls) -> str:
        """Get the main application stylesheet.

        Returns:
            QSS stylesheet string
        """
        c = cls.get_colors()
        s = cls.SPACING
        r = cls.RADIUS
        f = cls.FONT_SIZE

        return f"""
        /* Main Application */
        QMainWindow {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
        }}

        /* Labels */
        QLabel {{
            color: {c['text_primary']};
            font-size: {f['md']};
        }}

        /* Line Edits */
        QLineEdit {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: {r['sm']};
            padding: {s['sm']} {s['md']};
            font-size: {f['md']};
        }}

        QLineEdit:read-only {{
            background-color: {c['bg_secondary']};
            color: {c['text_secondary']};
        }}

        QLineEdit:focus {{
            border: 1px solid {c['accent']};
        }}

        /* Buttons - Base Style */
        QPushButton {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: {r['sm']};
            padding: {s['sm']} {s['lg']};
            font-size: {f['md']};
            min-height: 15px;
        }}

        QPushButton:hover {{
            background-color: {c['bg_tertiary']};
            border-color: {c['border_dark']};
        }}

        QPushButton:pressed {{
            background-color: {c['border_medium']};
        }}

        QPushButton:disabled {{
            background-color: {c['bg_secondary']};
            color: {c['text_light']};
            border-color: {c['border_light']};
        }}

        /* Primary Buttons (Success/Execute actions) */
        QPushButton[class="primary"] {{
            background-color: {c['primary']};
            color: {c['text_inverse']};
            border: none;
            font-weight: bold;
        }}

        QPushButton[class="primary"]:hover {{
            background-color: {c['primary_hover']};
        }}

        QPushButton[class="primary"]:disabled {{
            background-color: {c['text_light']};
        }}

        /* Info Buttons (Preview/Browse) */
        QPushButton[class="info"] {{
            background-color: {c['info']};
            color: {c['text_inverse']};
            border: none;
        }}

        QPushButton[class="info"]:hover {{
            background-color: {c['info_hover']};
        }}

        /* Text Edit */
        QTextEdit {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: {r['sm']};
            padding: {s['sm']};
            font-size: {f['sm']};
            font-family: "Courier New", monospace;
        }}

        /* Tree View */
        QTreeView {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: {r['sm']};
            selection-background-color: {c['accent']};
            selection-color: {c['text_inverse']};
        }}

        QTreeView::item:hover {{
            background-color: {c['bg_secondary']};
        }}

        QTreeView::item:selected {{
            background-color: {c['accent']};
            color: {c['text_inverse']};
        }}

        /* Table Widget */
        QTableWidget {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            gridline-color: {c['border_light']};
            selection-background-color: {c['accent']};
            selection-color: {c['text_inverse']};
        }}

        QTableWidget::item {{
            padding: {s['sm']};
        }}

        QHeaderView::section {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            padding: {s['sm']} {s['md']};
            border: 1px solid {c['border_medium']};
            font-weight: bold;
        }}

        /* Progress Bar */
        QProgressBar {{
            background-color: {c['bg_secondary']};
            border: 1px solid {c['border_medium']};
            border-radius: {r['sm']};
            text-align: center;
            color: {c['text_primary']};
            font-size: {f['md']};
        }}

        QProgressBar::chunk {{
            background-color: {c['success']};
            border-radius: {r['sm']};
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            border-top: 1px solid {c['border_medium']};
        }}

        /* Frames */
        QFrame {{
            border-radius: {r['sm']};
        }}

        /* Dialog */
        QDialog {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
        }}

        /* Menu Bar */
        QMenuBar {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border-bottom: 1px solid {c['border_light']};
        }}

        QMenuBar::item:selected {{
            background-color: {c['bg_secondary']};
        }}

        QMenu {{
            background-color: {c['bg_main']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
        }}

        QMenu::item:selected {{
            background-color: {c['accent']};
            color: {c['text_inverse']};
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {c['border_light']};
        }}

        QSplitter::handle:hover {{
            background-color: {c['border_medium']};
        }}
        """

    @classmethod
    def get_project_bar_style(cls) -> str:
        """Get stylesheet for the project selector bar.

        Returns:
            QSS stylesheet string
        """
        c = cls.get_colors()
        return f"""
            QFrame {{
                background-color: {c['bg_secondary']};
                border: 1px solid {c['border_medium']};
                border-radius: 3px;
                padding: 2px;
            }}
        """

    @classmethod
    def get_file_display_style(cls) -> str:
        """Get stylesheet for file display box in operations panel.

        Returns:
            QSS stylesheet string
        """
        c = cls.get_colors()
        return f"""
            padding: {cls.SPACING['md']};
            background-color: {c['bg_secondary']};
            color: {c['text_primary']};
            border-radius: {cls.RADIUS['sm']};
            border: 1px solid {c['border_medium']};
        """
