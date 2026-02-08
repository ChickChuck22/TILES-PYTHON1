
# Colors
COLOR_BG = "#121212"
COLOR_SIDEBAR = "#1E1E1E"
COLOR_ACCENT = "#00B8D4"
COLOR_ACCENT_HOVER = "#00E5FF"
COLOR_TEXT_PRIMARY = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#AAAAAA"
COLOR_CARD_BG = "#252525"
COLOR_CARD_HOVER = "#303030"

# Fonts
FONT_Family = "Segoe UI"
FONT_SIZE_TITLE = "24px"
FONT_SIZE_HEADER = "18px"
FONT_SIZE_NORMAL = "14px"
FONT_SIZE_SMALL = "12px"

DIFFICULTY_COLORS = {
    "Easy": "#4CAF50",
    "Normal": "#2196F3",
    "Hard": "#FFEB3B",
    "Insane": "#FF9800",
    "Impossible": "#F44336",
    "God": "#9C27B0",
    "Beyond": "#E91E63"
}

GLOBAL_STYLES = f"""
    QMainWindow {{
        background-color: {COLOR_BG};
    }}
    QWidget {{
        font-family: "{FONT_Family}";
        color: {COLOR_TEXT_PRIMARY};
    }}
    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 8px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #333;
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    QComboBox {{
        background-color: #333;
        color: white;
        border: 1px solid #555;
        padding: 5px;
        border-radius: 4px;
        font-size: 14px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: #333;
        color: white;
        selection-background-color: {COLOR_ACCENT};
    }}
"""

SIDEBAR_STYLE = f"""
    QWidget {{
        background-color: {COLOR_SIDEBAR};
        border-right: 1px solid #333;
    }}
    QPushButton {{
        text-align: left;
        padding: 15px 20px;
        border: none;
        background-color: transparent;
        color: {COLOR_TEXT_SECONDARY};
        font-size: 16px;
        font-weight: 500;
        border-left: 4px solid transparent;
    }}
    QPushButton:hover {{
        background-color: #252525;
        color: {COLOR_TEXT_PRIMARY};
    }}
    QPushButton:checked {{
        color: {COLOR_ACCENT};
        background-color: #252525;
        border-left: 4px solid {COLOR_ACCENT};
        font-weight: bold;
    }}
"""

CARD_STYLE = f"""
    QFrame {{
        background-color: {COLOR_CARD_BG};
        border-radius: 12px;
        border: 1px solid #333;
    }}
    QFrame:hover {{
        background-color: {COLOR_CARD_HOVER};
        border: 1px solid #444;

    }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        background-color: #252525;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px 15px;
        color: white;
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_ACCENT};
    }}
"""

BUTTON_PRIMARY_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_ACCENT};
        color: #000;
        border-radius: 8px;
        font-weight: bold;
        padding: 12px;
        font-size: 14px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_ACCENT_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_ACCENT};
        padding-top: 13px; /* visual press */
    }}
    QPushButton:disabled {{
        background-color: #333;
        color: #555;
    }}
"""
