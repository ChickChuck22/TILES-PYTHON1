import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, 
    QGraphicsDropShadowEffect, QApplication, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QFont, QPixmap
from src.ui import styles
from src.core.analysis_manager import AnalysisThread

class BootstrapperQt(QWidget):
    """
    A premium loading screen that bridges Menu and Gameplay.
    Performs beat analysis and audio prep with rich animations.
    """
    finished = pyqtSignal(object) # Emits beats when ready
    
    def __init__(self, song_path, difficulty, custom_settings, metadata=None):
        super().__init__()
        self.song_path = song_path
        self.difficulty = difficulty
        self.custom_settings = custom_settings
        self.metadata = metadata or {}
        self.beats = None
        
        self.init_ui()
        
        # Load Album Art (with local fallback)
        self.load_image(self.metadata.get("image"))
            
        self.start_analysis()

    def load_image(self, img_source=None):
        # 1. Try metadata image (URL or path)
        if img_source and img_source.startswith("http"):
            from src.ui.modern_menu import get_image_manager
            get_image_manager().load(img_source, self)
            return
        elif img_source and os.path.exists(img_source):
            self.set_image(QPixmap(img_source))
            return

    def set_image(self, pixmap):
        try:
            self.img_label.setPixmap(pixmap)
            self.img_label.setText("")
        except: pass
        
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        
        # Main Container (Glassmorphic)
        self.container = QFrame(self)
        self.container.setGeometry(10, 10, 580, 380)
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: rgba(20, 20, 20, 230);
                border: 2px solid #333;
                border-radius: 30px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 255, 120, 80))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)
        
        # Upper Section: Image + Info
        header_layout = QHBoxLayout()
        header_layout.setSpacing(25)
        
        # Album Art Placeholder / Image
        self.img_label = QLabel()
        self.img_label.setFixedSize(140, 140)
        self.img_label.setStyleSheet("background-color: #121212; border-radius: 15px; border: 1px solid #333;")
        self.img_label.setScaledContents(True)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setText("🎵")
        header_layout.addWidget(self.img_label)
        
        info_l = QVBoxLayout()
        info_l.setSpacing(5)
        
        self.lbl_status = QLabel("INITIALIZING BOOTSTRAPPER...")
        self.lbl_status.setStyleSheet("color: #1DB954; font-weight: bold; letter-spacing: 2px; font-size: 11px;")
        # Song Info
        name = self.metadata.get("name") or self.metadata.get("title")
        artist = self.metadata.get("artist")
        
        if name and artist:
            display_title = f"{artist} - {name}"
        elif name:
            display_title = name
        else:
            display_title = os.path.splitext(os.path.basename(self.song_path))[0]
            
        self.lbl_title = QLabel(display_title.upper())
        self.lbl_title.setStyleSheet("color: white; font-size: 24px; font-weight: 900;")
        self.lbl_title.setWordWrap(True)
        info_l.addWidget(self.lbl_title)
        
        # Difficulty Detail
        self.lbl_diff = QLabel(f"TRACK ANALYZER • {self.difficulty.upper()}")
        self.lbl_diff.setStyleSheet("color: #666; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        info_l.addWidget(self.lbl_diff)
        
        info_l.addStretch()
        header_layout.addLayout(info_l)
        layout.addLayout(header_layout)
        
        layout.addStretch()
        
        # Progress Section
        prog_container = QVBoxLayout()
        prog_container.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #111;
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {styles.COLOR_ACCENT}, stop:1 #00FFCC);
                border-radius: 3px;
            }}
        """)
        prog_container.addWidget(self.progress_bar)
        
        self.lbl_percent = QLabel("0% READY")
        self.lbl_percent.setAlignment(Qt.AlignRight)
        self.lbl_percent.setStyleSheet("color: #444; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        prog_container.addWidget(self.lbl_percent)
        
        layout.addLayout(prog_container)
        
        # Pulsating Glow Animation
        self.glow_val = 30
        self.glow_timer = QTimer()
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)
        self.glow_dir = 1
        
        # Fade In Animation
        self.setWindowOpacity(0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()

    def update_glow(self):
        self.glow_val += 2 * self.glow_dir
        if self.glow_val > 60 or self.glow_val < 20: 
            self.glow_dir *= -1
            
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(self.glow_val)
        shadow.setColor(QColor(0, 255, 120, 100))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)

    def start_analysis(self):
        self.thread = AnalysisThread(self.song_path, self.difficulty)
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()
        
    def on_progress(self, val, msg):
        self.progress_bar.setValue(int(val))
        self.lbl_percent.setText(f"{int(val)}% OPTIMIZED")
        
        # Precise status updates
        if val < 20: self.lbl_status.setText("BOOTSTRAPPER: DECODING AUDIO...")
        elif val < 40: self.lbl_status.setText("BOOTSTRAPPER: CALCULATING SPECTROGRAM...")
        elif val < 60: self.lbl_status.setText("BOOTSTRAPPER: DETECTING TRANSIENTS...")
        elif val < 80: self.lbl_status.setText("BOOTSTRAPPER: GENERATING TILES...")
        else: self.lbl_status.setText("BOOTSTRAPPER: FINALIZING SYNC...")

    def on_finished(self, beats):
        if beats:
            self.beats = beats
            self.lbl_status.setText("BOOTSTRAPPER: READY")
            self.progress_bar.setValue(100)
            self.lbl_percent.setText("100%")
            
            # Subtle delay before closing for the "Ready" feel
            QTimer.singleShot(800, self.close_and_emit)
        else:
            self.lbl_status.setText("ERROR: FAILED TO LOAD AUDIO")
            self.lbl_status.setStyleSheet("color: #FF4444; font-weight: bold;")
            QTimer.singleShot(2000, self.close)

    def close_and_emit(self):
        # Fade Out
        self.fade_anim.setDirection(QPropertyAnimation.Backward)
        self.fade_anim.finished.connect(self._do_close)
        self.fade_anim.start()
        
    def _do_close(self):
        self.finished.emit(self.beats)
        self.close()

def run_bootstrapper(song_path, difficulty, custom_settings, metadata=None):
    """Wrapper to run the bootstrapper and return beats."""
    # Check if QApplication exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    boot = BootstrapperQt(song_path, difficulty, custom_settings, metadata)
    boot.show()
    
    # We use a nested event loop to wait for the signal
    from PyQt5.QtCore import QEventLoop
    loop = QEventLoop()
    result_beats = []
    
    def handle_finish(beats):
        result_beats.append(beats)
        loop.quit()
        
    boot.finished.connect(handle_finish)
    loop.exec_()
    
    return result_beats[0] if result_beats else None
