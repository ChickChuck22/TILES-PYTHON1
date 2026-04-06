import sys
import os
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QHBoxLayout, QStackedWidget, 
    QScrollArea, QFrame, QLineEdit, QComboBox, QSlider,
    QCheckBox, QProgressBar, QFileDialog, QMessageBox,
    QGraphicsDropShadowEffect, QButtonGroup, QDialog, QSizePolicy, QTabWidget,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot, QThread, QUrl, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QFontMetrics

# Local imports
from src.core.settings import SettingsManager
import src.ui.styles as styles
from src.ui.results import ResultsDialog
from src.ui.widgets import ModernSongCard
from src.services.discord_rpc import DiscordRPC
from src.services.spotify_service import SpotifyService
from src.services.youtube_service import YouTubeService
from src.core.analysis_manager import AnalysisManager, AnalysisThread


class ModernMenuQt(QMainWindow):
    song_ready = pyqtSignal(str, str, list, dict) 
    download_finished_signal = pyqtSignal(str, str)
    download_progress_signal = pyqtSignal(float)

    def __init__(self, songs, audio_manager, discord_rpc=None, results=None):
        super().__init__()
        self.songs = songs
        self.audio_manager = audio_manager
        self.discord_rpc = discord_rpc

        if self.discord_rpc:
             self.discord_rpc.update_menu(len(songs))
        
        self.settings_manager = SettingsManager()
        self.selected_song = songs[0]["path"] if songs else None
        self.song_cards = {} # TRACK SONG CARDS
        
        # Signal Connections
        self.download_finished_signal.connect(self._finish_yt_download)
        self.download_progress_signal.connect(self._update_yt_progress)
        
        # Background Analysis
        self.analysis_manager = None
        # Toast removed
        
        if results:
            print("DEBUG: Scheduling show_results...")
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
        self.init_spotify_page()
        self.init_youtube_page()
        
        # Wire up
        self.nav_musics.setChecked(True)
        self.switch_page(0)
        
        # Initial Logic (This triggers populate_tabs and analysis_manager)
        self.refresh_library()
        
        if self.selected_song:
            self.select_song(self.selected_song)

    def closeEvent(self, event):
        """Cleanup threads on exit."""
        if self.analysis_manager:
            self.analysis_manager.stop()
        if hasattr(self, 'preview_thread') and self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop_flag = True # Add flag if needed, or terminate
            self.preview_thread.terminate()
            self.preview_thread.wait()
        if hasattr(self, 'game_analysis_thread') and isinstance(self.game_analysis_thread, QThread) and self.game_analysis_thread.isRunning():
            self.game_analysis_thread.terminate()
            self.game_analysis_thread.wait()
        event.accept()

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
            
        self.nav_musics = create_nav_btn("🎵  MUSICS", 0)
        self.nav_mods = create_nav_btn("🛠️  MODIFIERS", 1)
        self.nav_sys = create_nav_btn("⚙️  SYSTEM", 2)
        self.nav_spotify_dl = create_nav_btn("🟢  SPOTIFY DL", 3)
        self.nav_youtube_dl = create_nav_btn("🔴  YOUTUBE DL", 4)
        
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
        # Container for the Musics Page
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("MUSIC LIBRARY")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {styles.COLOR_TEXT_PRIMARY}; margin: 20px;")
        layout.addWidget(header)
        
        # Tabs
        self.music_tabs = QTabWidget()
        self.music_tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab {
                background: #222;
                color: #AAA;
                padding: 12px 40px;
                min-width: 120px;
                font-weight: bold;
                font-size: 14px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #333;
                color: white;
                border-bottom: 2px solid #00F0FF;
            }
            QTabBar::tab:hover {
                background: #2A2A2A;
            }
        """)
        
        # Tab 1: LOCALS
        self.tab_locals = QWidget()
        self.grid_locals = self.create_song_tab(self.tab_locals, "Local Files")
        self.music_tabs.addTab(self.tab_locals, "LOCALS")
        
        # Tab 2: SPOTIFY (Downloads)
        self.tab_spotify_dl = QWidget()
        self.grid_spotify = self.create_song_tab(self.tab_spotify_dl, "Spotify Downloads")
        self.music_tabs.addTab(self.tab_spotify_dl, "SPOTIFY")
        
        # Tab 3: YOUTUBE (Downloads)
        self.tab_youtube_dl = QWidget()
        self.grid_youtube = self.create_song_tab(self.tab_youtube_dl, "YouTube Downloads")
        self.music_tabs.addTab(self.tab_youtube_dl, "YOUTUBE")
        
        layout.addWidget(self.music_tabs)
        
        # Common Bottom Controls (Difficulty + Start) - Shared across all tabs?
        # Or should each tab have its own start?
        # Shared is better for consistency.
        
        bottom_container = QWidget()
        bottom = QHBoxLayout(bottom_container)
        bottom.setContentsMargins(40, 20, 40, 20)
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
            QComboBox QAbstractItemView {{
                background-color: #252525;
                color: white;
                selection-background-color: #444;
            }}
        """)
        
        # Colorize items
        from PyQt5.QtGui import QColor
        for i, d in enumerate(["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"]):
            self.diff_combo.setItemData(i, QColor(styles.DIFFICULTY_COLORS[d]), Qt.ForegroundRole)
            
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
        
        layout.addWidget(bottom_container)
        
        # Integrated Progress Bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(4)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setStyleSheet(f"QProgressBar {{ background: #333; border: none; }} QProgressBar::chunk {{ background: {styles.COLOR_ACCENT}; }}")
        layout.addWidget(self.prog_bar)
        
        self.stack.addWidget(container)

    def create_song_tab(self, page, placeholder_text):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(20)
        
        # Search Bar specific to this tab? 
        # Or filters self.song_cards?
        # If we have 3 grids, we need 3 lists of cards.
        # Let's add a search bar here.
        
        search_bar = QLineEdit()
        search_bar.setPlaceholderText(f"🔍  Search {placeholder_text}...")
        search_bar.setStyleSheet(styles.INPUT_STYLE)
        # We need to filter THIS grid.
        # Defining a closure for filtering
        
        layout.addWidget(search_bar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        grid = QVBoxLayout(content)
        grid.setSpacing(10)
        grid.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Store reference to grid for population
        # Return layout to caller?
        
        # We need to hook up search.
        # This requires storing the cards for THIS tab.
        # Let's attach them to the layout object or page object.
        page.cards = [] # List of (name, widget)
        
        def filter_tab(text):
            text = text.lower().strip()
            for name, widget in page.cards:
                if text in name.lower():
                    widget.setVisible(True)
                else:
                    widget.setVisible(False)
                    
        search_bar.textChanged.connect(filter_tab)
        
        return grid


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

    # --- Reverting init_locals_tab is not needed as init_play_page now does it all --- 
    # But clean up the method if unused. For now, let's just make ensure init_spotify/youtube are pages again.

    def init_spotify_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Header
        header = QLabel("Spotify Downloader")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #1DB954;")
        layout.addWidget(header)
        
        self.spotify_service = SpotifyService()
        
        # Connect Button (Initial State)
        self.spotify_login_btn = QPushButton("Connect with Spotify")
        self.spotify_login_btn.setFixedSize(200, 50)
        self.spotify_login_btn.setCursor(Qt.PointingHandCursor)
        self.spotify_login_btn.setStyleSheet("background-color: #1DB954; color: white; border-radius: 25px; font-weight: bold;")
        self.spotify_login_btn.clicked.connect(self.login_spotify)
        layout.addWidget(self.spotify_login_btn, alignment=Qt.AlignCenter)
        
        # Content Area (Hidden until login)
        self.spotify_content = QWidget()
        self.spotify_content.setVisible(False)
        content_layout = QVBoxLayout(self.spotify_content)
        content_layout.setContentsMargins(0,0,0,0)
        
        # Playlists Combo
        self.playlist_combo = QComboBox()
        self.playlist_combo.setStyleSheet(styles.INPUT_STYLE)
        self.playlist_combo.currentIndexChanged.connect(self.load_spotify_tracks_from_combo)
        content_layout.addWidget(QLabel("Select Playlist:"))
        content_layout.addWidget(self.playlist_combo)
        
        # Tracks List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        tracks_widget = QWidget()
        self.spotify_tracks_layout = QVBoxLayout(tracks_widget)
        self.spotify_tracks_layout.setSpacing(10)
        self.spotify_tracks_layout.addStretch()
        
        scroll.setWidget(tracks_widget)
        content_layout.addWidget(scroll)
        
        layout.addWidget(self.spotify_content)
        self.stack.addWidget(page)

    def init_youtube_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("YouTube Downloader")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF0000;")
        layout.addWidget(header)
        
        self.youtube_service = YouTubeService()
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.yt_search_input = QLineEdit()
        self.yt_search_input.setPlaceholderText("Search YouTube...")
        self.yt_search_input.setStyleSheet(styles.INPUT_STYLE)
        self.yt_search_input.returnPressed.connect(self.search_youtube)
        
        btn_search = QPushButton("Search")
        btn_search.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
        btn_search.clicked.connect(self.search_youtube)
        
        search_layout.addWidget(self.yt_search_input)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        
        # Results Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.yt_results_widget = QWidget()
        self.yt_results_layout = QVBoxLayout(self.yt_results_widget)
        self.yt_results_layout.setSpacing(15)
        self.yt_results_layout.addStretch()
        
        scroll.setWidget(self.yt_results_widget)
        layout.addWidget(scroll)
        
        # Status Label
        self.yt_status = QLabel("")
        self.yt_status.setStyleSheet("color: #AAA; font-style: italic;")
        layout.addWidget(self.yt_status)
        
        # Download Progress
        self.yt_progress = QProgressBar()
        self.yt_progress.setTextVisible(False)
        self.yt_progress.setFixedHeight(6)
        self.yt_progress.setStyleSheet(f"QProgressBar {{ background: #333; border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: {styles.COLOR_ACCENT}; border-radius: 3px; }}")
        self.yt_progress.setValue(0)
        self.yt_progress.setVisible(False)
        layout.addWidget(self.yt_progress)
        
        self.stack.addWidget(page)

    def login_spotify(self):
        self.spotify_login_btn.setText("Connecting...")
        self.spotify_login_btn.setEnabled(False)
        
        # Simplified sync for now as authentication might open browser
        # In a real app, use threading to prevent freeze
        try:
            success = self.spotify_service.authenticate()
        except: success = False
        
        if success:
            self.spotify_login_btn.setVisible(False)
            self.spotify_content.setVisible(True)
            self.load_spotify_playlists()
        else:
            self.spotify_login_btn.setText("Connection Failed. Check .env")
            self.spotify_login_btn.setEnabled(True)

    def load_spotify_playlists(self):
        playlists = self.spotify_service.get_playlists()
        self.playlist_combo.clear()
        self.spotify_playlists_data = playlists
        
        for p in playlists:
            self.playlist_combo.addItem(f"{p['name']} ({p['tracks_total']} tracks)", p['id'])

    def load_spotify_tracks_from_combo(self, idx):
        if idx < 0: return
        playlist_id = self.spotify_combo_data(idx)
        if not playlist_id: return
        
        # Clear tracks
        while self.spotify_tracks_layout.count():
            c = self.spotify_tracks_layout.takeAt(0)
            if c.widget(): c.widget().deleteLater()
            
        tracks = self.spotify_service.get_playlist_tracks(playlist_id)
        
        for t in tracks:
            # Create a simple card for each track
            card = QFrame()
            card.setStyleSheet("background: #222; border-radius: 8px; padding: 10px;")
            card.setFixedHeight(60)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(5,5,5,5)
            
            # Simple Image Load (Blocking - should be async in prod)
            # if t['image']: ...
            
            lbl = QLabel(f"{t['name']} - {t['artist']}")
            lbl.setStyleSheet("color: white; font-size: 14px;")
            cl.addWidget(lbl)
            
            if t['preview_url']:
                btn_preview = QPushButton("▶")
                btn_preview.setFixedSize(30, 30)
                btn_preview.setStyleSheet("background: #1DB954; color: white; border-radius: 15px;")
                # Use lambda default arg to capture track url
                btn_preview.clicked.connect(lambda _, url=t['preview_url']: self.play_spotify_preview(url))
                cl.addWidget(btn_preview)
            
            self.spotify_tracks_layout.insertWidget(self.spotify_tracks_layout.count()-1, card)

    def spotify_combo_data(self, idx):
        if 0 <= idx < len(self.spotify_playlists_data):
            return self.spotify_playlists_data[idx]['id']
        return None

    def play_spotify_preview(self, url):
        print(f"Playing Preview: {url}")
        import webbrowser
        webbrowser.open(url)

    def init_youtube_tab(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("YouTube Downloads")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #FF0000;")
        layout.addWidget(header)
        
        self.youtube_service = YouTubeService()
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.yt_search_input = QLineEdit()
        self.yt_search_input.setPlaceholderText("Search YouTube...")
        self.yt_search_input.setStyleSheet(styles.INPUT_STYLE)
        self.yt_search_input.returnPressed.connect(self.search_youtube)
        
        btn_search = QPushButton("Search")
        btn_search.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
        btn_search.clicked.connect(self.search_youtube)
        
        search_layout.addWidget(self.yt_search_input)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        
        # Results Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.yt_results_widget = QWidget()
        self.yt_results_layout = QVBoxLayout(self.yt_results_widget)
        self.yt_results_layout.setSpacing(15)
        self.yt_results_layout.addStretch()
        
        scroll.setWidget(self.yt_results_widget)
        layout.addWidget(scroll)
        
        # Status Label
        self.yt_status = QLabel("")
        self.yt_status.setStyleSheet("color: #AAA; font-style: italic;")
        layout.addWidget(self.yt_status)

    def search_youtube(self):
        query = self.yt_search_input.text().strip()
        if not query: return
        
        self.yt_status.setText("Searching...")
        self.yt_search_input.setEnabled(False)
        
        # Thread search
        import threading
        def _search():
            results = self.youtube_service.search(query)
            # We need to signal back to UI thread. 
            # For simplicity in this edit, we'll assume a method to update UI exists or use QTimer hacks if needed.
            # But here we can use QMetaObject.invokeMethod if we had slot, or just QTimer.singleShot(0, ...)
            # Let's try to update self.latest_yt_results and trigger update via QTimer
            self.latest_yt_results = results
            # Trigger update on main thread? 
            # Actually, let's just do sync search for now to avoid crashing with threading issues if not handled perfectly.
            # It will freeze UI for a second but is safer for this specific edit context.
            pass

        # Doing SYNC search for stability in this prompt context
        try:
             results = self.youtube_service.search(query)
             self.display_youtube_results(results)
             self.yt_status.setText(f"Found {len(results)} results.")
        except Exception as e:
             self.yt_status.setText(f"Error: {e}")
        
        self.yt_search_input.setEnabled(True)

    def display_youtube_results(self, results):
        # Clear previous
        while self.yt_results_layout.count():
            c = self.yt_results_layout.takeAt(0)
            if c.widget(): c.widget().deleteLater()
            
        for vid in results:
            card = QFrame()
            card.setStyleSheet("background: #222; border-radius: 8px; padding: 10px;")
            card.setMinimumHeight(100) # Allow expansion
            
            h = QHBoxLayout(card)
            h.setContentsMargins(5,5,5,5)
            h.setSpacing(15)
            
            # Thumbnail Button (Clickable)
            btn_thumb = QPushButton()
            btn_thumb.setFixedSize(120, 70) 
            btn_thumb.setCursor(Qt.PointingHandCursor)
            btn_thumb.setStyleSheet("background-color: #000; border: none; border-radius: 4px;")
            btn_thumb.clicked.connect(lambda _, vid_id=vid['id'], title=vid['title']: self.download_and_play_youtube(vid_id, title))
            
            # Async Thumb Loading
            try:
                from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
                from PyQt5.QtCore import QUrl
                
                # We need a persistent manager or keep reference
                if not hasattr(self, '_nam'): self._nam = QNetworkAccessManager()
                
                def on_thumb_loaded(reply, btn_ref):
                    try:
                        if reply.error() != reply.NoError:
                            print(f"Thumb Network Error: {reply.errorString()}")
                            reply.deleteLater()
                            return
                        
                        data = reply.readAll()
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        if not pixmap.isNull():
                            # Scale to btn size
                            icon = QIcon(pixmap.scaled(120, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            btn_ref.setIcon(icon)
                            btn_ref.setIconSize(btn_ref.size())
                        else:
                            print(f"Thumb Error: Pixmap is null for url {reply.url().toString()}")
                    except Exception as e:
                        print(f"Thumb Load Exception: {e}")
                    finally:
                        reply.deleteLater()

                req = QNetworkRequest(QUrl(vid['thumbnail']))
                req.setAttribute(QNetworkRequest.FollowRedirectsAttribute, True)
                req.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                
                reply = self._nam.get(req)
                # Pass btn_thumb explicitly to avoid closure issues
                reply.finished.connect(lambda r=reply, b=btn_thumb: on_thumb_loaded(r, b))
            except Exception as e:
                print(f"Network Image Error: {e}")
                btn_thumb.setText("▶") # Fallback
                
            h.addWidget(btn_thumb)
            
            # Text Info
            v = QVBoxLayout()
            v.setSpacing(5)
            
            title = QLabel(vid['title'])
            title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
            title.setWordWrap(True) 
            title.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            # Ensure it expands
            title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            
            uploader = QLabel(f"{vid['uploader']} • {vid['duration']}s")
            uploader.setStyleSheet("color: #AAA; font-size: 12px;")
            uploader.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            
            v.addWidget(title)
            v.addWidget(uploader)
            v.addStretch()
            h.addLayout(v, stretch=1) # Give text more space
            
            # Play Button
            btn_dl = QPushButton("PLAY")
            btn_dl.setFixedSize(80, 40)
            btn_dl.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
            btn_dl.setCursor(Qt.PointingHandCursor)
            btn_dl.clicked.connect(lambda _, vid_id=vid['id'], title=vid['title']: self.download_and_play_youtube(vid_id, title))
            h.addWidget(btn_dl)
            
            self.yt_results_layout.insertWidget(self.yt_results_layout.count()-1, card)

    def download_and_play_youtube(self, video_id, title):
        self.yt_status.setText(f"Downloading '{title}'... Please wait.")
        self.yt_progress.setVisible(True)
        self.yt_progress.setValue(0)
        
        # We need a slot for thread-safety updates
        # Since we are in a lambda/thread scope, we can use QMetaObject or signals.
        # But for simplicity in this structure without defining a new signal on the class (which requires restart),
        # we can use a small helper with QTimer or assume direct update works if called from hook (it might warn but often works in pyqt).
        # BETTER: Use a defined signal. But I can't easily add a signal to the class definition dynamically.
        # SAFE APPROACH: Use QTimer to poll or a thread-safe wrapper.
        
        # Actually, let's define a method on self that is thread-safe via QMetaObject.invokeMethod?
        # Or just use the fact that I can't add signals now.
        # Let's use a simple detailed approach:
        
    def download_and_play_youtube(self, video_id, title):
        self.yt_status.setText(f"Downloading '{title}'... Please wait.")
        self.yt_progress.setVisible(True)
        self.yt_progress.setValue(0)
        
        # Use signals for thread safety
        def update_prog(val):
            # Emit signal from background thread (safe in PyQt)
            self.download_progress_signal.emit(float(val))
            
        def on_done(file_path):
            # Emit signal
            self.download_finished_signal.emit(str(file_path) if file_path else "", title)
            
        self.youtube_service.download_audio(video_id, on_done, progress_callback=update_prog)

    def _update_yt_progress(self, val):
        self.yt_progress.setValue(int(val))

    def _finish_yt_download(self, file_path, title):
        print(f"DEBUG: _finish_yt_download called with path={file_path}")
        # Update progress to 100% just in case
        self.yt_progress.setValue(100)
        
        # Hide after a delay so user sees completion
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.yt_progress.setVisible(False))
        
        # self.stack.setEnabled(True)
        if file_path and os.path.exists(file_path):
            self.yt_status.setText(f"Downloaded: {title}")
            
            # Refresh ONLY the youtube folder to avoid stutter
            youtube_path = os.path.join("assets", "music", "youtube")
            self.refresh_library(folder_to_scan=youtube_path)
            
            # Select the new song
            self.select_song(file_path)
            
            # Switch to "Musics" page (index 0) and "YouTube" tab (index 2)
            self.nav_musics.setChecked(True)
            self.switch_page(0)
            self.music_tabs.setCurrentIndex(2) # 0=Locals, 1=Spotify, 2=YouTube
            
            # Scroll to it? (Hard with current layout, but selection highlights it)
            
            # Notify user via status or popup?
            # For now, just switching to library is enough "Play on the spot" enabler
            # If they want IMMEDIATE play, we could still auto-start, but user said 
            # "add a play button to play on the spot", implying maybe a choice?
            # But earlier they said "loop downloading". Let's stick to showing it in library.
            
        else:
            self.yt_status.setText("Download failed. Check implementation.")

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
        if hasattr(self, 'preview_thread') and self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.terminate()
            self.preview_thread.wait()
            
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
        
        # Stop preview before starting game analysis to avoid collisions
        if hasattr(self, 'preview_thread') and self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.terminate()
            self.preview_thread.wait()

        self.game_analysis_thread = AnalysisThread(self.selected_song, self.diff_combo.currentText())
        self.game_analysis_thread.progress.connect(lambda v, m: self.prog_bar.setValue(int(v)))
        self.game_analysis_thread.finished.connect(self.on_analysis_finished)
        self.game_analysis_thread.start()

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
        dlg = MusicLibraryDialog(self.settings_manager, self)
        if dlg.exec_():
             self.refresh_library()

    def refresh_library(self, folder_to_scan=None):
        if folder_to_scan:
            # Incremental refresh
            print(f"DEBUG: Incremental refresh for {folder_to_scan}")
            new_songs = self.audio_manager.scan_library([folder_to_scan])
            
            # Filter what we already have
            actually_new = []
            seen = {os.path.normpath(s).lower() for s in self.songs}
            for s in new_songs:
                if os.path.normpath(s).lower() not in seen:
                    actually_new.append(s)
            
            if actually_new:
                print(f"DEBUG: Found {len(actually_new)} NEW songs.")
                self.songs.extend(actually_new)
                self.add_songs_to_ui(actually_new)
                
                # Add to background analysis queue
                if self.analysis_manager:
                    actually_new_paths = [s["path"] for s in actually_new]
                    self.analysis_manager.add_songs(actually_new_paths)
            return

        # Re-scan all configured folders plus our assets/music structure
        folders = self.settings_manager.get_music_folders()
        folders.append("assets/music")
        folders.append(os.path.join("assets", "music", "youtube"))
        folders.append(os.path.join("assets", "music", "spotify"))
        
        print(f"DEBUG: Refreshing library from {folders}")
        self.songs = self.audio_manager.scan_library(folders)
        print(f"DEBUG: Scanned {len(self.songs)} songs.")
        self.populate_tabs(self.songs)
        
        # Start Background Analysis
        if self.analysis_manager:
            self.analysis_manager.stop()
            self.analysis_manager.wait()
            
        song_paths = [s["path"] for s in self.songs]
        self.analysis_manager = AnalysisManager(song_paths)
        self.analysis_manager.worker.progress.connect(self.on_analysis_progress)
        self.analysis_manager.worker.finished.connect(self.on_analysis_step_finished)
        self.analysis_manager.worker.diff_finished.connect(self.on_diff_finished)
        # self.analysis_manager.worker.all_finished.connect(self.on_all_analysis_finished)
        self.analysis_manager.start()
        
    def on_analysis_progress(self, song_path, val):
        if song_path in self.song_cards:
            self.song_cards[song_path].set_analysis_progress(val)
        else:
            # Fallback for path mismatch (e.g. forward/back slashes)
            norm_path = os.path.normpath(song_path)
            for k, card in self.song_cards.items():
                if os.path.normpath(k) == norm_path:
                    card.set_analysis_progress(val)
                    return
            print(f"DEBUG: Could not find card for {song_path}")
        
    def on_analysis_step_finished(self, song_path):
        if song_path in self.song_cards:
            self.song_cards[song_path].set_analysis_progress(-1)
        else:
            norm_path = os.path.normpath(song_path)
            for k, card in self.song_cards.items():
                if os.path.normpath(k) == norm_path:
                    card.set_analysis_progress(-1)
                    return

    def on_diff_finished(self, song_path, difficulty):
        # Update the stripes on the card
        if song_path in self.song_cards:
            card = self.song_cards[song_path]
            if difficulty not in card.cached_diffs:
                card.update_cached_diffs(card.cached_diffs + [difficulty])
        else:
            norm_path = os.path.normpath(song_path)
            for k, card in self.song_cards.items():
                if os.path.normpath(k) == norm_path:
                    if difficulty not in card.cached_diffs:
                        card.update_cached_diffs(card.cached_diffs + [difficulty])
                    return
        
    def on_all_analysis_finished(self):
        pass

    def populate_tabs(self, songs):
        print(f"DEBUG: Populating tabs with {len(songs)} songs...")
        # Clear existing
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
        
        clear_layout(self.grid_locals)
        clear_layout(self.grid_spotify)
        clear_layout(self.grid_youtube)
        
        self.tab_locals.cards = []
        self.tab_spotify_dl.cards = []
        self.tab_youtube_dl.cards = []
        
        # Populate
        self.song_cards = {} # Reset map
        for song_data in songs:
            card = ModernSongCard(song_data)
            card.clicked.connect(self.select_song)
            self.song_cards[song_data["path"]] = card
            
            norm = os.path.normpath(song_data["path"]).lower() 
            name = os.path.basename(song_data["path"])
            
            # Simple heuristic based on path
            if "youtube" in norm:
                self.grid_youtube.addWidget(card)
                self.tab_youtube_dl.cards.append((name, card))
            elif "spotify" in norm:
                self.grid_spotify.addWidget(card)
                self.tab_spotify_dl.cards.append((name, card))
            else:
                self.grid_locals.addWidget(card)
                self.tab_locals.cards.append((name, card)) # Everything else is local
                
        # Add stretches
        self.grid_locals.addStretch()
        self.grid_spotify.addStretch()
        self.grid_youtube.addStretch()

    def add_songs_to_ui(self, songs):
        """Incrementally adds cards to the UI without a full clear."""
        for song_data in songs:
            if song_data["path"] in self.song_cards: continue
            
            card = ModernSongCard(song_data)
            card.clicked.connect(self.select_song)
            self.song_cards[song_data["path"]] = card
            
            norm = os.path.normpath(song_data["path"]).lower()
            name = os.path.basename(song_data["path"])
            
            # Removestretch temporarily? No, layouts often have stretch at end.
            # Grid layouts in this app are actually QVBoxLayout with addWidget.
            # But the 'grid' variables are QVBoxLayouts.
            
            if "youtube" in norm:
                # Insert BEFORE the stretch
                self.grid_youtube.insertWidget(self.grid_youtube.count()-1, card)
                self.tab_youtube_dl.cards.append((name, card))
            elif "spotify" in norm:
                self.grid_spotify.insertWidget(self.grid_spotify.count()-1, card)
                self.tab_spotify_dl.cards.append((name, card))
            else:
                self.grid_locals.insertWidget(self.grid_locals.count()-1, card)
                self.tab_locals.cards.append((name, card))

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
