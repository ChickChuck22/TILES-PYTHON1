from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QListWidget, QListWidgetItem, 
                             QGraphicsDropShadowEffect, QHBoxLayout, QComboBox,
                             QProgressBar, QFrame, QScrollArea, QSlider, QDialog, 
                             QFileDialog, QMessageBox, QTabWidget, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QFontMetrics, QPixmap, QIcon
import os
import sys
from src.core.settings import SettingsManager

# ... (AnalysisThread and MusicLibraryDialog classes omitted for brevity, they remain unchanged)
# I need to keep them or use multi_replace.
# Since I'm replacing a huge chunk of init_ui, I should probably use multi_replace for specific sections 
# or just be very careful with StartLine/EndLine.
# But `init_ui` is huge.
# Let's replace the CONTENT of `init_ui` regarding the Left Panel.

# Wait, `replace_file_content` is better if I can target the whole block.
# The block spans from `left_layout = QVBoxLayout(self.left_panel)` (line 223) to `left_layout.addStretch()` (line 348).
# That covers almost everything I want to move.

# Steps:
# 1. Update imports (line 1-4).
# 2. Refactor Left Panel content (line 223-348).

# Let's do imports first.
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QFontMetrics, QPixmap, QIcon
import os
import sys
from src.core.settings import SettingsManager

class AnalysisThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object) # Changed from list to object to support dict

    def __init__(self, song_path, difficulty):
        super().__init__()
        self.song_path = song_path
        self.difficulty = difficulty

    def run(self):
        from src.core.beat_detector import BeatDetector
        detector = BeatDetector(self.song_path)
        result = detector.analyze(self.difficulty, self.report_progress)
        self.finished.emit(result)

    def report_progress(self, val, msg):
        self.progress.emit(val, msg)

class MusicLibraryDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Manage Music Library")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: #222; color: white; font-family: 'Segoe UI';")
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Additional Music Folders:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #333; border: 1px solid #555; padding: 5px;")
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Folder")
        add_btn.setStyleSheet("background-color: #00B8D4; color: black; padding: 8px; border-radius: 4px; font-weight: bold;")
        add_btn.clicked.connect(self.add_folder)
        
        rem_btn = QPushButton("Remove Selected")
        rem_btn.setStyleSheet("background-color: #D32F2F; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        rem_btn.clicked.connect(self.remove_folder)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(rem_btn)
        layout.addLayout(btn_layout)
        
        save_btn = QPushButton("Save & Rescan")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; font-weight: bold; border-radius: 4px; margin-top: 10px;")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)
        
        self.load_folders()
        
    def load_folders(self):
        self.list_widget.clear()
        for f in self.settings_manager.get_music_folders():
            self.list_widget.addItem(f)
            
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            if self.settings_manager.add_music_folder(folder):
                self.load_folders()
                
    def remove_folder(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            item = self.list_widget.item(row)
            self.settings_manager.remove_music_folder(item.text())
            self.load_folders()

class SongCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, song_path, duration="--:--", stars=1.0):
        super().__init__()
        self.song_path = song_path
        
        # Extract display name
        filename = os.path.basename(song_path)
        display_name = os.path.splitext(filename)[0]
        
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(100) # Increased height for word wrap
        self.setStyleSheet("""
            QFrame { background-color: #252525; border-radius: 8px; border: 1px solid #333; }
            QFrame:hover { background-color: #333; border-color: #444; }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Icon
        icon = QLabel("🎵")
        icon.setStyleSheet("color: #00B8D4; font-size: 24px; border: none; background: transparent;")
        layout.addWidget(icon)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Title (Full Text, Word Wrap)
        self.title = QLabel(display_name)
        self.title.setWordWrap(True)
        self.title.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        info_layout.addWidget(self.title)
        
        # Metadata Row (Stars | Time)
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(10)
        
        self.star_label = QLabel(f"⭐ {stars:.1f}")
        self.star_label.setStyleSheet("color: #FFD700; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        meta_layout.addWidget(self.star_label)
        
        self.time_label = QLabel(duration)
        self.time_label.setStyleSheet("color: #888; font-size: 12px; border: none; background: transparent;")
        meta_layout.addWidget(self.time_label)
        
        meta_layout.addStretch()
        info_layout.addLayout(meta_layout)
        
        layout.addLayout(info_layout)
        
    def set_stars(self, val):
        self.star_label.setText(f"⭐ {val:.1f}")
        
    def set_time(self, text):
        self.time_label.setText(text)

    def mousePressEvent(self, event):
        self.clicked.emit(self.song_path)

class MenuQt(QMainWindow):
    song_ready = pyqtSignal(str, str, list, dict) # name, diff, beats, custom_settings

    def __init__(self, songs, audio_manager):
        super().__init__()
        self.songs = songs
        self.audio_manager = audio_manager
        self.selected_song = songs[0] if songs else None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Titanium Piano - Music Dashboard")
        self.setWindowIcon(QIcon("assets/icon.png"))
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

    def __init__(self, songs, audio_manager):
        super().__init__()
        self.songs = songs
        self.audio_manager = audio_manager
        self.settings_manager = SettingsManager()
        self.selected_song = songs[0] if songs else None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Titanium Piano - Music Dashboard")
        self.setWindowIcon(QIcon("assets/icon.png"))
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
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(10)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #1A1A1A; }
            QTabBar::tab {
                background: #1A1A1A;
                color: #777;
                padding: 12px 25px;
                min-width: 90px;
                font-weight: bold;
                font-size: 14px;
                border-bottom: 3px solid transparent;
            }
            QTabBar::tab:selected {
                color: #00B8D4;
                border-bottom: 3px solid #00B8D4;
                background: #202020;
            }
            QTabBar::tab:hover { color: white; background: #252525; }
        """)
        left_layout.addWidget(self.tabs)

        # --- TAB 1: PLAY ---
        tab_play = QWidget()
        play_layout = QVBoxLayout(tab_play)
        play_layout.setContentsMargins(20, 20, 20, 20)
        play_layout.setSpacing(15)
        
        # Title & Song Display
        title_label = QLabel("PIANO TILES")
        title_label.setStyleSheet("color: #00B8D4; font-size: 28px; font-weight: 900; letter-spacing: 2px;")
        play_layout.addWidget(title_label)
        
        self.song_display = QLabel("SELECT A SONG")
        self.song_display.setWordWrap(True)
        self.song_display.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-top: 10px;")
        play_layout.addWidget(self.song_display)
        
        play_layout.addSpacing(20)
        
        # Difficulty
        diff_label = QLabel("DIFFICULTY PRESET")
        diff_label.setStyleSheet("color: #555; font-size: 11px; font-weight: 800; letter-spacing: 1px;")
        play_layout.addWidget(diff_label)
        
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"])
        self.diff_combo.setCurrentText("Normal")
        self.diff_combo.setFixedHeight(45)
        self.diff_combo.setStyleSheet("""
            QComboBox { background-color: #252525; color: white; border-radius: 6px; padding-left: 15px; border: 1px solid #333; font-size: 14px; }
            QComboBox QAbstractItemView { background-color: #252525; color: white; selection-background-color: #00B8D4; }
            QComboBox::drop-down { border: none; }
        """)
        play_layout.addWidget(self.diff_combo)
        
        play_layout.addStretch()
        self.tabs.addTab(tab_play, "PLAY")

        # --- TAB 2: MODS ---
        tab_mods = QWidget()
        mods_layout = QVBoxLayout(tab_mods)
        mods_layout.setContentsMargins(20, 20, 20, 20)
        mods_layout.setSpacing(20)
        
        # Custom Header
        custom_header = QLabel("GAMEPLAY MODIFIERS")
        custom_header.setStyleSheet("color: #00B8D4; font-size: 12px; font-weight: 800;")
        mods_layout.addWidget(custom_header)
        
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
        mods_layout.addWidget(speed_box)

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
        mods_layout.addWidget(chord_box)

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
        mods_layout.addWidget(hold_box)
        
        # Smart Speed
        self.chk_smart_speed = QCheckBox("Enable Smart Speed")
        self.chk_smart_speed.setToolTip("Dynamic scroll speed based on music energy")
        self.chk_smart_speed.setStyleSheet("QCheckBox { color: #AAA; spacing: 10px; } QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #555; } QCheckBox::indicator:checked { background-color: #00B8D4; }")
        self.chk_smart_speed.stateChanged.connect(self.on_smart_speed_toggled)
        mods_layout.addWidget(self.chk_smart_speed)

        mods_layout.addStretch()
        self.tabs.addTab(tab_mods, "MODS")

        # --- TAB 3: SYSTEM ---
        tab_sys = QWidget()
        sys_layout = QVBoxLayout(tab_sys)
        sys_layout.setContentsMargins(20, 20, 20, 20)
        sys_layout.setSpacing(20)
        
        # Volume Header
        vol_header = QLabel("SYSTEM SETTINGS")
        vol_header.setStyleSheet("color: #00B8D4; font-size: 12px; font-weight: 800;")
        sys_layout.addWidget(vol_header)
        
        # Music Volume
        mvol_box = QWidget()
        mvol_l = QVBoxLayout(mvol_box)
        mvol_l.setContentsMargins(0,0,0,0)
        self.mvol_label = QLabel("Music Volume: 100%")
        self.mvol_label.setStyleSheet("color: #AAA; font-size: 11px;")
        self.mvol_slider = QSlider(Qt.Horizontal)
        self.mvol_slider.setRange(0, 100)
        self.mvol_slider.setValue(100)
        self.mvol_slider.valueChanged.connect(self.on_mvol_changed)
        mvol_l.addWidget(self.mvol_label)
        mvol_l.addWidget(self.mvol_slider)
        sys_layout.addWidget(mvol_box)

        # SFX Volume
        svol_box = QWidget()
        svol_l = QVBoxLayout(svol_box)
        svol_l.setContentsMargins(0,0,0,0)
        self.svol_label = QLabel("SFX Volume: 100%")
        self.svol_label.setStyleSheet("color: #AAA; font-size: 11px;")
        self.svol_slider = QSlider(Qt.Horizontal)
        self.svol_slider.setRange(0, 100)
        self.svol_slider.setValue(100)
        self.svol_slider.valueChanged.connect(self.on_svol_changed)
        svol_l.addWidget(self.svol_label)
        svol_l.addWidget(self.svol_slider)
        sys_layout.addWidget(svol_box)
        
        # Combo Toggle
        self.combo_check = QCheckBox("Show Combo Text")
        self.combo_check.setChecked(True)
        self.combo_check.setStyleSheet("QCheckBox { color: #AAA; spacing: 10px; } QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #555; } QCheckBox::indicator:checked { background-color: #00B8D4; }")
        sys_layout.addWidget(self.combo_check)
        
        # Library Button
        lib_btn = QPushButton("📁 Manage Library")
        lib_btn.setStyleSheet("background-color: #333; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        lib_btn.clicked.connect(self.open_library_manager)
        sys_layout.addWidget(lib_btn)
        
        sys_layout.addStretch()
        self.tabs.addTab(tab_sys, "SYSTEM")

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
        self.start_btn.clicked.connect(self.start_game)
        left_layout.addWidget(self.start_btn)

        main_layout.addWidget(self.left_panel)

        # RIGHT PANEL: Song List
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(40, 60, 40, 40)
        
        header = QLabel("MUSIC LIBRARY")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        right_layout.addWidget(header)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search song...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: white;
                border: 1px solid #444;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QLineEdit:focus { border: 1px solid #00B8D4; }
        """)
        self.search_bar.textChanged.connect(self.filter_songs)
        right_layout.addWidget(self.search_bar)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 4px; background: transparent; } QScrollBar::handle:vertical { background: #333; border-radius: 2px; }")
        
        scroll_content = QWidget()
        self.grid_layout = QVBoxLayout(scroll_content)
        self.grid_layout.setSpacing(12)
        
        self.song_cards = {} # Track cards
        
        for song in self.songs:
            # We try to get duration from cache later, or init as is.
            card = SongCard(song)
            card.clicked.connect(self.select_song)
            self.grid_layout.addWidget(card)
            self.song_cards[song] = card
        
        self.grid_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll)

        main_layout.addWidget(self.right_panel)
        
        # Initial Star Calculation
        self.update_stars()
        
        if self.selected_song:
            self.select_song(self.selected_song)

    def calculate_difficulty(self):
        # Formula:
        # Speed: 350(Easy) -> 500(Norm) -> 900(Insane) -> 2100(Beyond)
        # Factor: Speed / 500
        speed = self.speed_slider.value()
        speed_factor = speed / 500.0
        
        # Chord: 0% -> 35%
        chord = self.chord_slider.value()
        chord_factor = (chord / 30.0) * 1.5 # 30% adds 1.5 stars
        
        # Hold: 0% -> 100%
        hold = self.hold_slider.value()
        hold_factor = (hold / 50.0) * 0.5 # 50% adds 0.5 stars
        
        # Smart Speed
        smart = 1.0 if self.chk_smart_speed.isChecked() else 0.0
        
        stars = speed_factor + chord_factor + hold_factor + smart
        return max(0.0, stars)

    def update_stars(self):
        stars = self.calculate_difficulty()
        # Update all cards? Or just show general difficulty?
        # User said: "Conforme você modifica... a estrela aumenta"
        # Since we have global settings for now, let's update ALL cards to reflect
        # what difficulty they WOULD be if played now.
        # Ideally, each song has an intrinsic "density" offset, but we don't know it yet for all.
        # So we display the "Settings Rating".
        for name, card in self.song_cards.items():
            card.set_stars(stars)

    def on_speed_changed(self, v):
        self.speed_label.setText(f"Scroll Speed: {v}")
        self.update_stars()

    def on_speed_release(self):
        pass

    def on_chord_changed(self, v):
        self.chord_label.setText(f"Chord Probability: {v}%" if v > 0 else "Chord Probability: Default (Auto)")
        self.update_stars()

    def on_hold_changed(self, v):
        self.hold_label.setText(f"Hold Probability: {v}%")
        self.update_stars()
        
    def on_smart_speed_toggled(self, state):
        self.update_stars()

    def on_mvol_changed(self, v):
        self.mvol_label.setText(f"Music Volume: {v}%")
        if hasattr(self, 'audio_manager'):
            self.audio_manager.set_music_volume(v / 100.0)

    def on_svol_changed(self, v):
        self.svol_label.setText(f"SFX Volume: {v}%")
        if hasattr(self, 'audio_manager'):
            self.audio_manager.set_sfx_volume(v / 100.0)

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
            self.speed_slider.blockSignals(True)
            self.chord_slider.blockSignals(True)
            self.hold_slider.blockSignals(True)
            
            self.speed_slider.setValue(p["speed"])
            self.chord_slider.setValue(p["chord"])
            self.hold_slider.setValue(p["hold"])
            
            self.speed_slider.blockSignals(False)
            self.chord_slider.blockSignals(False)
            self.hold_slider.blockSignals(False)
            
            # Update labels manually since we blocked signals
            self.on_speed_changed(p["speed"])
            self.on_chord_changed(p["chord"])
            self.on_hold_changed(p["hold"])
        
        self.update_stars()

    def select_song(self, song_path):
        self.selected_song = song_path
        
        display_name = os.path.splitext(os.path.basename(song_path))[0]
        self.song_display.setText(display_name.upper()) # Full text
        
        # Trigger Preview
        # We need to analyze quick or get cache to find preview_start
        # To avoid blocking UI, we could do this in a thread, OR just load cache if exists.
        
        # Quick check cache
        # We replicate basic hash logic or use BeatDetector
        from src.core.beat_detector import BeatDetector
        # detector = BeatDetector(song_path)
        # We don't want to run full analyze here if not cached, too slow.
        # But we modified BeatDetector to be fast if cached.
        
        # Create a worker to fetch preview time so we don't freeze UI
        self.preview_thread = AnalysisThread(song_path, "Normal") # Difficulty doesn't matter for start time
        self.preview_thread.finished.connect(self.start_preview)
        self.preview_thread.start()

    def start_preview(self, result):
        # Result is a dict now
        if isinstance(result, dict):
            start_time = result.get("preview_start", 0.0)
            self.audio_manager.play_preview(self.selected_song, start_time)

    def start_game(self):
        self.start_btn.setEnabled(False)
        self.diff_combo.setEnabled(False)
        self.prog_label.setText("Preparing...")
        
        # song_path is self.selected_song (full path)
        song_path = self.selected_song
        self.thread = AnalysisThread(song_path, self.diff_combo.currentText())
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.on_analysis_finished)
        self.thread.start()

    @pyqtSlot(int, str)
    def update_progress(self, val, msg):
        self.prog_bar.setValue(val)
        self.prog_label.setText(msg.upper())

    def on_analysis_finished(self, result):
        beats = []
        energy_profile = []
        
        if isinstance(result, dict):
            beats = result.get("beats", [])
            energy_profile = result.get("energy_profile", [])
        elif isinstance(result, list):
            beats = result
            
        custom = {
            "speed": self.speed_slider.value(),
            "chord_chance": self.chord_slider.value() / 100.0 if self.chord_slider.value() > 0 else None,
            "hold_chance": self.hold_slider.value() / 100.0,
            "show_combo": self.combo_check.isChecked(),
            "smart_speed": self.chk_smart_speed.isChecked(),
            "energy_profile": energy_profile
        }
        self.song_ready.emit(self.selected_song, self.diff_combo.currentText(), beats, custom)
        self.close()

    def open_library_manager(self):
        dlg = MusicLibraryDialog(self.settings_manager, self)
        if dlg.exec_():
            self.refresh_songs()

    def refresh_songs(self):
        # 1. Get folders
        folders = self.settings_manager.get_music_folders()
        folders.append("assets/music") # Always include default
        
        # 2. Rescan
        print("Refreshing library...")
        self.songs = self.audio_manager.scan_library(folders)
        
        # 3. Clear Grid
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 4. Re-populate
        self.song_cards = {}
        for song in self.songs:
            card = SongCard(song)
            card.clicked.connect(self.select_song)
            self.grid_layout.addWidget(card)
            self.song_cards[song] = card
            
        self.grid_layout.addStretch()
        
        # 5. Update Stars
        self.update_stars()
        
        # 6. Re-apply Search
        if hasattr(self, 'search_bar'):
            self.filter_songs(self.search_bar.text())

    def filter_songs(self, text):
        text = text.lower().strip()
        for song_name, card in self.song_cards.items():
            if text in song_name.lower():
                card.setVisible(True)
            else:
                card.setVisible(False)

def run_menu(songs, audio_manager):
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = MenuQt(songs, audio_manager)
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
