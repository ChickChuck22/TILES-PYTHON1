from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
import os
import src.ui.styles as styles

class ModernSongCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, song_path, duration="--:--", stars=1.0):
        super().__init__()
        self.song_path = song_path
        self.setStyleSheet(styles.CARD_STYLE)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(110)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        
        # Icon / Album Art Placeholder
        icon_cont = QLabel("🎵")
        icon_cont.setAlignment(Qt.AlignCenter)
        icon_cont.setFixedSize(60, 60)
        icon_cont.setStyleSheet(f"background: #1A1A1A; border-radius: 30px; font-size: 24px; color: {styles.COLOR_ACCENT}; border: none;")
        layout.addWidget(icon_cont)
        
        # Info
        info_l = QVBoxLayout()
        info_l.setSpacing(5)
        
        # Title
        filename = os.path.basename(song_path)
        display_name = os.path.splitext(filename)[0]
        self.title = QLabel(display_name)
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; border: none; background: transparent;")
        info_l.addWidget(self.title)
        
        # Subtitle
        self.subtitle = QLabel("Unknown Artist • " + duration)
        self.subtitle.setStyleSheet("font-size: 12px; color: #AAA; border: none; background: transparent;")
        info_l.addWidget(self.subtitle)
        
        layout.addLayout(info_l)
        layout.addStretch()
        
        # Difficulty Stars
        self.stars_label = QLabel("★ " + f"{stars:.1f}")
        self.stars_label.setStyleSheet(f"color: {styles.COLOR_ACCENT}; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        layout.addWidget(self.stars_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.song_path)

    def set_stars(self, val):
        self.stars_label.setText(f"★ {val:.1f}")
