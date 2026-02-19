from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import src.ui.styles as styles

class ResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Results")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(600, 500)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {styles.COLOR_BG}; border: 2px solid {styles.COLOR_ACCENT}; border-radius: 15px; }}
            QLabel {{ color: white; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title = QLabel(f"Finished: {results.get('song', 'Unknown')}")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #AAA;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Rank
        rank = QLabel(results.get('rank', 'F'))
        rank_color = "#FFD700" if results.get('rank') == 'S' else "#00B8D4" if results.get('rank') == 'A' else "#FFFFFF"
        rank.setStyleSheet(f"font-size: 120px; font-weight: bold; color: {rank_color};")
        rank.setAlignment(Qt.AlignCenter)
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(rank_color))
        rank.setGraphicsEffect(shadow)
        layout.addWidget(rank)
        
        # Score & Accuracy
        score_lbl = QLabel(f"Score: {results.get('score', 0):,}")
        score_lbl.setStyleSheet("font-size: 36px; font-weight: bold; color: white;")
        score_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(score_lbl)

        acc_lbl = QLabel(f"Accuracy: {results.get('accuracy', 0):.2f}%")
        acc_lbl.setStyleSheet("font-size: 20px; color: #CCC;")
        acc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(acc_lbl)
        
        # Stats Grid
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 10px;")
        grid = QHBoxLayout(grid_frame)
        
        def make_stat(name, val, color):
            vbox = QVBoxLayout()
            l_val = QLabel(str(val))
            l_val.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            l_val.setAlignment(Qt.AlignCenter)
            l_name = QLabel(name)
            l_name.setStyleSheet("font-size: 14px; color: #888;")
            l_name.setAlignment(Qt.AlignCenter)
            vbox.addWidget(l_val)
            vbox.addWidget(l_name)
            return vbox

        grid.addLayout(make_stat("Perfect", results.get('perfects', 0), "#00FF00"))
        grid.addLayout(make_stat("Good", results.get('goods', 0), "#00B8D4"))
        grid.addLayout(make_stat("Miss", results.get('misses', 0), "#FF5555"))
        grid.addLayout(make_stat("Max Combo", results.get('max_combo', 0), "#FFFF00"))
        
        layout.addWidget(grid_frame)
        layout.addStretch()
        
        # Continue Button
        btn_cont = QPushButton("CONTINUE")
        btn_cont.setCursor(Qt.PointingHandCursor)
        btn_cont.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {styles.COLOR_ACCENT}; 
                color: {styles.COLOR_BG}; 
                font-size: 20px; 
                font-weight: bold;
                padding: 15px; 
                border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: white; }}
        """)
        btn_cont.clicked.connect(self.accept)
        layout.addWidget(btn_cont)
