from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
import pygame
import os
import json
import src.ui.styles as styles

# Export submodules

class RadialIconWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(70, 85) # Increased height for text below
        self._progress = -1 # -1 means hidden/not active
        self._hover = False
        
    def set_progress(self, val):
        self._progress = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Center coords
        # Circle size 60x60
        cx = self.width() / 2
        cy = 30 + 5 # Top margin 5
        radius = 28 
        
        # 1. Background Circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1A1A1A"))
        painter.drawEllipse(int(cx - 30), 5, 60, 60)
        
        # 2. Icon
        painter.setPen(QColor(styles.COLOR_ACCENT))
        painter.setFont(QFont("Segoe UI Emoji", 24))
        painter.drawText(int(cx - 30), 5, 60, 60, Qt.AlignCenter, "🎵")
        
        # 3. Progress Arc (if active)
        if self._progress >= 0 and self._progress < 100:
            pen = QPen(QColor(styles.COLOR_ACCENT))
            pen.setWidth(3)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            
            # Draw arc
            # Rect for arc needs to be slightly smaller or larger?
            # User said "em volta" (around). Let's draw on the edge.
            # 60x60 circle. Rect 5,5 60,60?
            
            span = int(-self._progress * 3.6 * 16)
            painter.drawArc(int(cx - 28), 7, 56, 56, 90 * 16, span)
            
            # 4. Percentage Text
            painter.setPen(QColor("#AAA"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.drawText(0, 65, self.width(), 20, Qt.AlignCenter, f"{int(self._progress)}%")

class ModernSongCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, song_data, stars=1.0):
        super().__init__()
        # song_data is a dict from AudioManager: {"path":..., "title":..., "artist":..., "duration":...}
        self.song_path = song_data["path"]
        self.song_title = song_data.get("title", "Unknown Title")
        self.song_artist = song_data.get("artist", "Unknown Artist")
        self.song_duration = song_data.get("duration", "--:--")
        
        self.setStyleSheet(styles.CARD_STYLE)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(120) # Increased slightly for stripes
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Top Content
        self.content_container = QWidget()
        content_layout = QHBoxLayout(self.content_container)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(15)
        
        # Icon Widget (Radial)
        self.icon_widget = RadialIconWidget()
        content_layout.addWidget(self.icon_widget)
        
        # Info
        info_l = QVBoxLayout()
        info_l.setSpacing(5)
        
        # Title
        self.title = QLabel(self.song_title)
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; border: none; background: transparent;")
        info_l.addWidget(self.title)
        
        # Subtitle
        self.subtitle = QLabel(f"{self.song_artist} • {self.song_duration}")
        self.subtitle.setStyleSheet("font-size: 12px; color: #AAA; border: none; background: transparent;")
        info_l.addWidget(self.subtitle)
        
        content_layout.addLayout(info_l)
        content_layout.addStretch()
        
        # Difficulty Stars
        self.stars_label = QLabel("★ " + f"{stars:.1f}")
        self.stars_label.setStyleSheet(f"color: {styles.COLOR_ACCENT}; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        content_layout.addWidget(self.stars_label)
        
        self.main_layout.addWidget(self.content_container)
        
        # Difficulty Stripes (Bottom)
        self.stripes_container = QWidget()
        self.stripes_container.setFixedHeight(6)
        self.stripes_layout = QHBoxLayout(self.stripes_container)
        self.stripes_layout.setContentsMargins(15, 0, 15, 4)
        self.stripes_layout.setSpacing(2)
        self.main_layout.addWidget(self.stripes_container)
        
        self.cached_diffs = []
        self._init_cache_check()

    def _init_cache_check(self):
        # Initial check for cached difficulties
        from src.core.beat_detector import BeatDetector
        detector = BeatDetector(self.song_path)
        diffs = ["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"]
        found = []
        for d in diffs:
            if os.path.exists(detector._get_cache_path(d)):
                found.append(d)
        self.update_cached_diffs(found)

    def mousePressEvent(self, event):
        self.clicked.emit(self.song_path)

    def set_stars(self, val):
        self.stars_label.setText(f"★ {val:.1f}")
        
    def set_analysis_progress(self, val):
        self.icon_widget.set_progress(val)
        
    def update_cached_diffs(self, difficulties):
        self.cached_diffs = difficulties
        # Clear stripes
        while self.stripes_layout.count():
            item = self.stripes_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        # Add new stripes
        # Sort them by importance/order
        order = ["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"]
        for d in order:
            if d in difficulties:
                stripe = QFrame()
                stripe.setFixedHeight(3)
                stripe.setFixedWidth(20) # Small segments
                color = styles.DIFFICULTY_COLORS.get(d, "#FFF")
                stripe.setStyleSheet(f"background-color: {color}; border-radius: 1.5px;")
                self.stripes_layout.addWidget(stripe)
        self.stripes_layout.addStretch()
