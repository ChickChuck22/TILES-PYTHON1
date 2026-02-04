from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QListWidget, QListWidgetItem, 
                             QGraphicsDropShadowEffect, QHBoxLayout, QComboBox,
                             QProgressBar, QFrame, QScrollArea, QSlider)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QFontMetrics, QPixmap
import os
import sys

class AnalysisThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)

    def __init__(self, song_path, difficulty):
        super().__init__()
        self.song_path = song_path
        self.difficulty = difficulty

    def run(self):
        from src.core.beat_detector import BeatDetector
        detector = BeatDetector(self.song_path)
        beats = detector.analyze(self.difficulty, self.report_progress)
        self.finished.emit(beats)

    def report_progress(self, val, msg):
        self.progress.emit(val, msg)

class SongCard(QFrame):
    clicked = pyqtSignal(str)
    
    def __init__(self, song_name, parent=None):
        super().__init__(parent)
        self.song_name = song_name
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(280, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("SongCard")
        self.setStyleSheet("""
            #SongCard {
                background-color: #252525;
                border-radius: 12px;
                border: 2px solid transparent;
            }
            #SongCard:hover {
                background-color: #2D2D2D;
                border: 2px solid #00B8D4;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # Icon/Thumbnail placeholder
        self.icon = QLabel("🎵")
        self.icon.setStyleSheet("font-size: 24px; padding-left: 10px;")
        layout.addWidget(self.icon)
        
        # Textinfo
        info_layout = QVBoxLayout()
        metrics = QFontMetrics(QFont("Arial", 11, QFont.Bold))
        elided = metrics.elidedText(self.song_name, Qt.ElideRight, 180)
        
        self.title = QLabel(elided)
        self.title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        self.sub = QLabel("Local MP3 File")
        self.sub.setStyleSheet("color: #777; font-size: 11px;")
        
        info_layout.addWidget(self.title)
        info_layout.addWidget(self.sub)
        layout.addLayout(info_layout)
        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.song_name)

class MenuQt(QMainWindow):
    song_ready = pyqtSignal(str, str, list, dict) # name, diff, beats, custom_settings

    def __init__(self, songs):
        super().__init__()
        self.songs = songs
        self.selected_song = songs[0] if songs else None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Titanium Piano - Music Dashboard")
        self.setFixedSize(1100, 750)
        self.setStyleSheet("background-color: #121212; font-family: 'Segoe UI', sans-serif;")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT PANEL: Details
        self.left_panel = QFrame()
        self.left_panel.setFixedWidth(450)
        self.left_panel.setStyleSheet("background-color: #1A1A1A; border-right: 1px solid #333;")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(15)

        title_label = QLabel("PIANO TILES")
        title_label.setStyleSheet("color: #00B8D4; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
        left_layout.addWidget(title_label)

        self.song_display = QLabel("SELECT A SONG")
        self.song_display.setWordWrap(True)
        self.song_display.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-top: 10px;")
        left_layout.addWidget(self.song_display)

        left_layout.addSpacing(10)

        # Base Difficulty
        diff_label = QLabel("BASE DIFFICULTY")
        diff_label.setStyleSheet("color: #555; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        left_layout.addWidget(diff_label)
        
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"])
        self.diff_combo.setCurrentText("Normal")
        self.diff_combo.setFixedHeight(40)
        self.diff_combo.setStyleSheet("""
            QComboBox { background-color: #252525; color: white; border-radius: 6px; padding-left: 10px; border: 1px solid #333; }
            QComboBox QAbstractItemView { background-color: #252525; color: white; selection-background-color: #00B8D4; }
        """)
        left_layout.addWidget(self.diff_combo)

        # CUSTOM CUSTOMIZATION AREA
        custom_header = QLabel("CUSTOM CUSTOMIZATION")
        custom_header.setStyleSheet("color: #00B8D4; font-size: 12px; font-weight: 800; margin-top: 15px;")
        left_layout.addWidget(custom_header)

        # Speed Slider
        speed_box = QWidget()
        speed_l = QVBoxLayout(speed_box)
        speed_l.setContentsMargins(0,0,0,0)
        self.speed_label = QLabel("Scroll Speed: 500")
        self.speed_label.setStyleSheet("color: #AAA; font-size: 11px;")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(300, 2500)
        self.speed_slider.setValue(500)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_l.addWidget(self.speed_label)
        speed_l.addWidget(self.speed_slider)
        left_layout.addWidget(speed_box)

        # Chord Chance Slider
        chord_box = QWidget()
        chord_l = QVBoxLayout(chord_box)
        chord_l.setContentsMargins(0,0,0,0)
        self.chord_label = QLabel("Chord Probability: Default (Auto)")
        self.chord_label.setStyleSheet("color: #AAA; font-size: 11px;")
        self.chord_slider = QSlider(Qt.Horizontal)
        self.chord_slider.setRange(0, 100)
        self.chord_slider.setValue(0)
        self.chord_slider.valueChanged.connect(self.on_chord_changed)
        chord_l.addWidget(self.chord_label)
        chord_l.addWidget(self.chord_slider)
        left_layout.addWidget(chord_box)

        # Hold Chance Slider
        hold_box = QWidget()
        hold_l = QVBoxLayout(hold_box)
        hold_l.setContentsMargins(0,0,0,0)
        self.hold_label = QLabel("Hold Probability: 15%")
        self.hold_label.setStyleSheet("color: #AAA; font-size: 11px;")
        self.hold_slider = QSlider(Qt.Horizontal)
        self.hold_slider.setRange(0, 100)
        self.hold_slider.setValue(15)
        self.hold_slider.valueChanged.connect(self.on_hold_changed)
        hold_l.addWidget(self.hold_label)
        hold_l.addWidget(self.hold_slider)
        left_layout.addWidget(hold_box)

        left_layout.addStretch()

        # Connect diff combo AFTER sliders are created
        self.diff_combo.currentIndexChanged.connect(self.sync_sliders_to_preset)

        # Progress bar
        self.progress_container = QWidget()
        prog_layout = QVBoxLayout(self.progress_container)
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(4)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setStyleSheet("QProgressBar { background: #333; border-radius: 2px; } QProgressBar::chunk { background: #00B8D4; }")
        self.prog_label = QLabel("Ready to play")
        self.prog_label.setStyleSheet("color: #00B8D4; font-size: 10px;")
        prog_layout.addWidget(self.prog_bar)
        prog_layout.addWidget(self.prog_label)
        left_layout.addWidget(self.progress_container)

        self.start_btn = QPushButton("PLAY SONG")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #00B8D4; color: white; border-radius: 6px; font-weight: bold; font-size: 15px; }
            QPushButton:hover { background-color: #00E5FF; }
            QPushButton:disabled { background-color: #333; color: #777; }
        """)
        self.start_btn.clicked.connect(self.on_start_clicked)
        left_layout.addWidget(self.start_btn)

        main_layout.addWidget(self.left_panel)

        # RIGHT PANEL: Song List
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(40, 60, 40, 40)
        
        header = QLabel("MUSIC LIBRARY")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        right_layout.addWidget(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 4px; background: transparent; } QScrollBar::handle:vertical { background: #333; border-radius: 2px; }")
        
        scroll_content = QWidget()
        self.grid_layout = QVBoxLayout(scroll_content)
        self.grid_layout.setSpacing(12)
        
        for song in self.songs:
            card = SongCard(song)
            card.clicked.connect(self.select_song)
            self.grid_layout.addWidget(card)
        
        self.grid_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        main_layout.addWidget(self.right_panel)
        
        if self.selected_song:
            self.select_song(self.selected_song)

    def on_speed_changed(self, v):
        self.speed_label.setText(f"Scroll Speed: {v}")

    def on_chord_changed(self, v):
        self.chord_label.setText(f"Chord Probability: {v}%" if v > 0 else "Chord Probability: Default (Auto)")

    def on_hold_changed(self, v):
        self.hold_label.setText(f"Hold Probability: {v}%")

    def sync_sliders_to_preset(self):
        diff = self.diff_combo.currentText()
        presets = {
            "Easy": {"speed": 350, "chord": 0, "hold": 15},
            "Normal": {"speed": 500, "chord": 0, "hold": 15},
            "Hard": {"speed": 700, "chord": 15, "hold": 15},
            "Insane": {"speed": 900, "chord": 25, "hold": 15},
            "Impossible": {"speed": 1200, "chord": 25, "hold": 15},
            "God": {"speed": 1600, "chord": 35, "hold": 15},
            "Beyond": {"speed": 2100, "chord": 35, "hold": 15}
        }
        if diff in presets:
            p = presets[diff]
            self.speed_slider.setValue(p["speed"])
            self.chord_slider.setValue(p["chord"])
            self.hold_slider.setValue(p["hold"])

    def select_song(self, song_name):
        self.selected_song = song_name
        metrics = QFontMetrics(QFont("Segoe UI", 24, QFont.Bold))
        self.song_display.setText(metrics.elidedText(song_name, Qt.ElideRight, 320))

    def on_start_clicked(self):
        self.start_btn.setEnabled(False)
        self.diff_combo.setEnabled(False)
        self.prog_label.setText("Preparing...")
        
        song_path = os.path.join("assets/music", self.selected_song)
        self.thread = AnalysisThread(song_path, self.diff_combo.currentText())
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.on_analysis_finished)
        self.thread.start()

    @pyqtSlot(int, str)
    def update_progress(self, val, msg):
        self.prog_bar.setValue(val)
        self.prog_label.setText(msg.upper())

    def on_analysis_finished(self, beats):
        custom = {
            "speed": self.speed_slider.value(),
            "chord_chance": self.chord_slider.value() / 100.0 if self.chord_slider.value() > 0 else None,
            "hold_chance": self.hold_slider.value() / 100.0
        }
        self.song_ready.emit(self.selected_song, self.diff_combo.currentText(), beats, custom)
        self.close()

def run_menu(songs):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = MenuQt(songs)
    window.show()
    
    result = {"song": None, "diff": "Normal", "beats": [], "custom": {}}
    def handle_ready(song, diff, beats, custom):
        result["song"] = song
        result["diff"] = diff
        result["beats"] = beats
        result["custom"] = custom
        window.close()
    
    window.song_ready.connect(handle_ready)
    app.exec_()
    return result["song"], result["diff"], result["beats"], result["custom"]
