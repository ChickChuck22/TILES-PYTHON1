import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLabel, QPushButton, QHBoxLayout, QStackedWidget, 
                             QScrollArea, QFrame, QLineEdit, QComboBox, QSlider,
                             QCheckBox, QProgressBar, QFileDialog, QMessageBox,
                             QGraphicsDropShadowEffect, QButtonGroup, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor

from src.core.settings import SettingsManager
from src.ui.menu_qt import AnalysisThread # Reuse logic
import src.ui.styles as styles
from src.ui.results import ResultsDialog
from src.ui.widgets import ModernSongCard



class ModernMenuQt(QMainWindow):
    song_ready = pyqtSignal(str, str, list, dict) 

    def __init__(self, songs, audio_manager, discord_rpc=None, results=None):
        super().__init__()
        self.songs = songs
        self.audio_manager = audio_manager
        self.discord_rpc = discord_rpc

        if self.discord_rpc:
             self.discord_rpc.update_menu(len(songs))
        
        self.settings_manager = SettingsManager()
        self.selected_song = songs[0] if songs else None
        
        if results:
            print("DEBUG: Scheduling show_results...")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(500, lambda: self.show_results(results))
        
        # Window Setup
        self.setWindowTitle("Piano Tiles - Modern Menu")
        self.resize(1100, 700)
        self.setStyleSheet(styles.GLOBAL_STYLES)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.init_sidebar()
        
        # 2. Content Stack
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # 3. Pages
        self.init_play_page()
        self.init_mods_page()
        self.init_system_page()
        
        # Wire up
        self.nav_play.setChecked(True)
        self.switch_page(0)
        
        # Initial Logic
        if self.selected_song:
            self.select_song(self.selected_song)

    def init_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(styles.SIDEBAR_STYLE)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 40, 0, 20)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("PIANO TILES")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {styles.COLOR_TEXT_PRIMARY}; margin-bottom: 40px;")
        layout.addWidget(title)
        
        # Nav Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        
        def create_nav_btn(text, idx):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda: self.switch_page(idx))
            self.nav_group.addButton(btn)
            layout.addWidget(btn)
            return btn
            
        self.nav_play = create_nav_btn("🎮  PLAY", 0)
        self.nav_mods = create_nav_btn("🛠️  MODIFIERS", 1)
        self.nav_sys = create_nav_btn("⚙️  SYSTEM", 2)
        
        layout.addStretch()
        
        # Version
        ver = QLabel("v2.0 Beta")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(ver)
        
        self.main_layout.addWidget(sidebar)

    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)

    def init_play_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header + Search
        top_bar = QHBoxLayout()
        header = QLabel("Select Song")
        header.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {styles.COLOR_TEXT_PRIMARY};")
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍  Search library...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.setStyleSheet(styles.INPUT_STYLE)
        self.search_bar.textChanged.connect(self.filter_songs)
        
        top_bar.addWidget(header)
        top_bar.addStretch()
        top_bar.addWidget(self.search_bar)
        layout.addLayout(top_bar)
        
        # Song List (Scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        self.song_grid = QVBoxLayout(content)
        self.song_grid.setSpacing(15)
        self.song_grid.setContentsMargins(0, 0, 20, 0) # Right padding for scrollbar
        
        self.song_cards = {}
        for song in self.songs:
            card = ModernSongCard(song)
            card.clicked.connect(self.select_song)
            self.song_grid.addWidget(card)
            self.song_cards[song] = card
            
        self.song_grid.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Bottom Controls (Difficulty + Start)
        bottom = QHBoxLayout()
        bottom.setSpacing(20)
        
        # Selected Song Display
        self.lbl_selected = QLabel("Select a track")
        self.lbl_selected.setStyleSheet("font-size: 16px; color: #AAA; font-weight: 500;")
        
        # Difficulty
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"])
        self.diff_combo.setCurrentText("Normal")
        self.diff_combo.setFixedWidth(150)
        self.diff_combo.setFixedHeight(45)
        self.diff_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #252525; border: 1px solid #444; border-radius: 8px;
                padding: 10px; color: white; font-size: 14px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.diff_combo.currentIndexChanged.connect(self.sync_sliders_to_preset)
        
        # Start Button
        self.btn_start = QPushButton("PLAY NOW  ►")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFixedWidth(200)
        self.btn_start.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
        self.btn_start.clicked.connect(self.start_game)
        
        bottom.addWidget(self.lbl_selected)
        bottom.addStretch()
        bottom.addWidget(self.diff_combo)
        bottom.addWidget(self.btn_start)
        
        layout.addLayout(bottom)
        
        # Progress (Overlay or integrated?)
        # Let's add a small bar above buttons
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(4)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setStyleSheet(f"QProgressBar {{ background: #333; border: none; }} QProgressBar::chunk {{ background: {styles.COLOR_ACCENT}; }}")
        layout.insertWidget(layout.count()-1, self.prog_bar)
        
        self.stack.addWidget(page)

    def init_mods_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)
        
        title = QLabel("Gameplay Modifiers")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        def create_slider(label_text, min_v, max_v, default_v, callback):
            container = QWidget()
            l = QVBoxLayout(container)
            l.setSpacing(10)
            
            lbl = QLabel(f"{label_text}: {default_v}")
            lbl.setStyleSheet("font-size: 16px; color: #CCC;")
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(min_v, max_v)
            slider.setValue(default_v)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{ height: 6px; background: #333; border-radius: 3px; }}
                QSlider::handle:horizontal {{ background: {styles.COLOR_ACCENT}; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px; }}
            """)
            
            def update_lbl(val):
                lbl.setText(f"{label_text}: {val}")
                callback(val)
                
            slider.valueChanged.connect(update_lbl)
            
            l.addWidget(lbl)
            l.addWidget(slider)
            layout.addWidget(container)
            return slider, lbl
            
        self.speed_slider, self.speed_label = create_slider("Scroll Speed", 300, 2500, 500, self.on_speed_changed)
        self.chord_slider, self.chord_label = create_slider("Chord %", 0, 100, 0, self.on_chord_changed)
        self.hold_slider, self.hold_label = create_slider("Hold %", 0, 100, 15, self.on_hold_changed)
        
        # Checkbox
        self.chk_smart_speed = QCheckBox("Enable Smart Speed (Dynamic)")
        self.chk_smart_speed.setStyleSheet(f"QCheckBox {{ font-size: 16px; spacing: 10px; color: #DDD; }} QCheckBox::indicator {{ width: 22px; height: 22px; border: 1px solid #555; border-radius: 6px; }} QCheckBox::indicator:checked {{ background: {styles.COLOR_ACCENT}; }}")
        self.chk_smart_speed.stateChanged.connect(self.update_stars)
        layout.addWidget(self.chk_smart_speed)
        
        layout.addStretch()
        self.stack.addWidget(page)

    def init_system_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(40)
        
        title = QLabel("System Settings")
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)
        
        # Helper for System Sliders
        def create_sys_slider(label_text, default_v, callback):
            container = QWidget()
            l = QVBoxLayout(container)
            l.setSpacing(10)
            
            lbl = QLabel(f"{label_text}: {default_v}%")
            lbl.setStyleSheet("font-size: 16px; color: #CCC;")
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(default_v)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{ height: 6px; background: #333; border-radius: 3px; }}
                QSlider::handle:horizontal {{ background: {styles.COLOR_ACCENT}; width: 20px; height: 20px; margin: -7px 0; border-radius: 10px; }}
            """)
            
            def update_lbl(val):
                lbl.setText(f"{label_text}: {val}%")
                callback(val)
                
            slider.valueChanged.connect(update_lbl)
            
            l.addWidget(lbl)
            l.addWidget(slider)
            layout.addWidget(container)
            return slider
            
        # Music Volume
        self.mvol_slider = create_sys_slider("Music Volume", 100, self.on_mvol_changed)
        
        # SFX Volume
        self.svol_slider = create_sys_slider("SFX Volume", 100, self.on_svol_changed)
        
        # Library Manager
        btn_lib = QPushButton("📂  Manage Music Library")
        btn_lib.setFixedWidth(300)
        btn_lib.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
        btn_lib.clicked.connect(self.open_library_manager)
        layout.addWidget(btn_lib)
        
        layout.addStretch()
        self.stack.addWidget(page)

    # --- Logic Methods (Copied/Adapted from MenuQt) ---
    
    def filter_songs(self, text):
        text = text.lower().strip()
        for song, card in self.song_cards.items():
            name = os.path.basename(song).lower()
            if text in name:
                card.setVisible(True)
            else:
                card.setVisible(False)

    def select_song(self, song_path):
        self.selected_song = song_path
        name = os.path.splitext(os.path.basename(song_path))[0]
        self.lbl_selected.setText(name.upper())
        self.lbl_selected.setStyleSheet(f"font-size: 18px; color: {styles.COLOR_ACCENT}; font-weight: bold;")
        
        # Preview Logic
        self.preview_thread = AnalysisThread(song_path, "Normal")
        self.preview_thread.finished.connect(self.start_preview)
        self.preview_thread.start()

    def start_preview(self, result):
        if isinstance(result, dict):
            start = result.get("preview_start", 0)
            self.audio_manager.play_preview(self.selected_song, start)

    def start_game(self):
        if not self.selected_song: return
        self.btn_start.setEnabled(False)
        self.btn_start.setText("ANALYZING...")
        
        self.thread = AnalysisThread(self.selected_song, self.diff_combo.currentText())
        self.thread.progress.connect(lambda v, m: self.prog_bar.setValue(v))
        self.thread.finished.connect(self.on_analysis_finished)
        self.thread.start()

    def on_analysis_finished(self, result):
        beats = result.get("beats", []) if isinstance(result, dict) else result
        custom = {
            "speed": self.speed_slider.value(),
            "chord_chance": self.chord_slider.value() / 100.0,
            "hold_chance": self.hold_slider.value() / 100.0,
            "smart_speed": self.chk_smart_speed.isChecked(),
            "energy_profile": result.get("energy_profile", []) if isinstance(result, dict) else []
        }
        self.song_ready.emit(self.selected_song, self.diff_combo.currentText(), beats, custom)
        
    def open_library_manager(self):
        from src.ui.menu_qt import MusicLibraryDialog 
        # We can reuse the dialog or reimplement nicely. Reusing for now.
        dlg = MusicLibraryDialog(self.settings_manager, self)
        if dlg.exec_():
             # Refresh logic
             self.songs = self.audio_manager.scan_library(self.settings_manager.get_music_folders())
             # Rebuild grid... (Simplified: just clear and add)
             while self.song_grid.count():
                 c = self.song_grid.takeAt(0)
                 if c.widget(): c.widget().deleteLater()
             self.song_cards = {}
             for song in self.songs:
                card = ModernSongCard(song)
                card.clicked.connect(self.select_song)
                self.song_grid.addWidget(card)
                self.song_cards[song] = card
             self.song_grid.addStretch()

    # Sliders logic
    def on_speed_changed(self, v): 
        self.update_stars()
    def on_chord_changed(self, v):
        self.chord_label.setText(f"Chord %: {v}")
        self.update_stars()
    def on_hold_changed(self, v):
        self.hold_label.setText(f"Hold %: {v}")
        self.update_stars()

    def on_mvol_changed(self, v):
        if hasattr(self, 'audio_manager'):
            self.audio_manager.set_music_volume(v / 100.0)

    def on_svol_changed(self, v):
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
            
            # Update visuals manually
            self.speed_label.setText(f"Scroll Speed: {p['speed']}")
            self.chord_label.setText(f"Chord %: {p['chord']}")
            self.hold_label.setText(f"Hold %: {p['hold']}")
            
    def update_stars(self):
        pass

    def show_results(self, results):
        print(f"DEBUG: Showing Results Dialog for {results.get('song')}")
        dlg = ResultsDialog(results, self)
        dlg.exec_()
            

def run_menu(songs, audio_manager, discord_rpc=None, results=None):
    print(f"DEBUG source run_menu: results={results}")
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Font Loader could go here
    
    window = ModernMenuQt(songs, audio_manager, discord_rpc, results)
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
