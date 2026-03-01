import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
import src.ui.styles as styles

class ModeCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, mode_id, title, description, icon_name=None):
        super().__init__()
        self.mode_id = mode_id
        self.setObjectName("ModeCard")
        self.setFixedSize(280, 380)
        self.setStyleSheet(styles.CARD_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(15)
        
        # Icon/Visual placeholder
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(80, 80)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet(f"background: #333; border-radius: 40px; border: 2px solid {styles.COLOR_ACCENT}; font-size: 30px;")
        # Simple symbol as icon
        symbols = {"classic": "🎹", "cyber_run": "🏃", "vibe_tunnel": "🌀"}
        self.icon_lbl.setText(symbols.get(mode_id, "🎮"))
        layout.addWidget(self.icon_lbl, 0, Qt.AlignCenter)
        
        layout.addSpacing(10)
        
        # Title
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)
        
        # Description
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"color: {styles.COLOR_TEXT_SECONDARY}; font-size: 14px;")
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_lbl)
        
        layout.addStretch()
        
        # Select Button
        self.btn = QPushButton("PLAY")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet(styles.BUTTON_PRIMARY_STYLE)
        self.btn.clicked.connect(lambda: self.clicked.emit(self.mode_id))
        layout.addWidget(self.btn)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        self.clicked.emit(self.mode_id)

class LauncherWindow(QMainWindow):
    mode_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Titanium Piano - Launcher")
        self.setFixedSize(1000, 600)
        self.setStyleSheet(styles.GLOBAL_STYLES)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("TITANIUM PIANO")
        title.setStyleSheet(f"font-size: 36px; font-weight: 900; color: {styles.COLOR_ACCENT}; letter-spacing: 5px;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("SELECT YOUR VIBE")
        subtitle.setStyleSheet(f"font-size: 14px; color: {styles.COLOR_TEXT_SECONDARY}; letter-spacing: 2px; font-weight: bold;")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        layout.addSpacing(50)
        
        # Modes Container
        modes_layout = QHBoxLayout()
        modes_layout.setSpacing(30)
        modes_layout.setAlignment(Qt.AlignCenter)
        
        self.cards = [
            ModeCard("classic", "CLASSIC", "The original rhythm experience. Hit the tiles to the beat."),
            ModeCard("cyber_run", "CYBER RUN", "Runner mode. Jump and slide through obstacles synced with the BPM."),
            ModeCard("vibe_tunnel", "VIBE TUNNEL", "Experimental visual trip. Reactive 3D tunnel synced with energy.")
        ]
        
        for card in self.cards:
            card.clicked.connect(self.on_mode_clicked)
            modes_layout.addWidget(card)
            
        layout.addLayout(modes_layout)
        layout.addStretch()

    def on_mode_clicked(self, mode_id):
        self.mode_selected.emit(mode_id)
        self.close()

def run_launcher():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    window = LauncherWindow()
    window.show()
    
    selected_mode = [None]
    def handle_mode(m):
        selected_mode[0] = m
        
    window.mode_selected.connect(handle_mode)
    app.exec_()
    return selected_mode[0]

if __name__ == "__main__":
    m = run_launcher()
    print(f"Selected: {m}")
