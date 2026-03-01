from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
    QPushButton, QGraphicsDropShadowEffect, QFileDialog, QWidget
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QImage
import os
import datetime
import src.ui.styles as styles

class PrecisionChart(QWidget):
    def __init__(self, hit_log, duration, parent=None):
        super().__init__(parent)
        self.hit_log = hit_log # List of (time, judgement)
        self.duration = duration if duration > 0 else 1.0
        self.setMinimumHeight(80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background line
        painter.setPen(QPen(QColor(100, 100, 100, 100), 2))
        painter.drawLine(10, h // 2, w - 10, h // 2)

        # Draw hits
        for time_pos, judgment in self.hit_log:
            x = 10 + (time_pos / self.duration) * (w - 20)
            
            color = QColor(255, 255, 255) # Default
            size = 6
            if judgment == "PERFECT":
                color = QColor(0, 255, 0)
            elif judgment == "GOOD":
                color = QColor(0, 184, 212)
            elif judgment == "MISS":
                color = QColor(255, 50, 50)
                size = 8

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(int(x), h // 2), size // 2, size // 2)

class ResultsDialog(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.setWindowTitle("Results")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(700, 600)
        
        # Main Container (for translucent border)
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 700, 600)
        self.container.setStyleSheet(f"""
            QFrame {{ 
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #0a0a0a);
                border: 2px solid {styles.COLOR_ACCENT}; 
                border-radius: 20px; 
            }}
            QLabel {{ color: white; border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Song Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(0)
        title = QLabel(results.get('song', 'Unknown Song'))
        title.setStyleSheet("font-size: 28px; font-weight: 900; color: #EEE;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        diff = QLabel(f"DIFFICULTY: {results.get('difficulty', 'NORMAL').upper()}")
        diff.setStyleSheet(f"font-size: 14px; color: {styles.COLOR_ACCENT}; font-weight: bold; letter-spacing: 2px;")
        diff.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(diff)
        layout.addLayout(header_layout)
        
        # Rank Area (Animated)
        self.rank_label = QLabel(results.get('rank', 'F'))
        self.rank_color = "#FFD700" if results.get('rank') == 'S' else "#00B8D4" if results.get('rank') == 'A' else "#FFFFFF"
        self.rank_label.setStyleSheet(f"font-size: 160px; font-weight: 900; color: {self.rank_color};")
        self.rank_label.setAlignment(Qt.AlignCenter)
        
        # Rank Shadow Glow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(self.rank_color))
        shadow.setOffset(0, 0)
        self.rank_label.setGraphicsEffect(shadow)
        
        layout.addWidget(self.rank_label)
        
        # Score & Accuracy
        score_val = results.get('score', 0)
        self.score_lbl = QLabel(f"{score_val:,}")
        self.score_lbl.setStyleSheet("font-size: 48px; font-weight: 900; color: white;")
        self.score_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_lbl)

        acc_lbl = QLabel(f"ACCURACY: {results.get('accuracy', 0):.2f}%")
        acc_lbl.setStyleSheet("font-size: 18px; color: #AAA; letter-spacing: 1px;")
        acc_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(acc_lbl)
        
        # Precision Chart
        chart_lbl = QLabel("PRECISION TIMELINE")
        chart_lbl.setStyleSheet("font-size: 10px; color: #555; font-weight: bold; margin-top: 10px;")
        layout.addWidget(chart_lbl)
        
        self.chart = PrecisionChart(results.get('hit_log', []), results.get('duration', 1))
        layout.addWidget(self.chart)
        
        # Stats Grid
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);")
        grid = QHBoxLayout(grid_frame)
        
        def make_stat(name, val, color):
            vbox = QVBoxLayout()
            l_val = QLabel(str(val))
            l_val.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {color};")
            l_val.setAlignment(Qt.AlignCenter)
            l_name = QLabel(name.upper())
            l_name.setStyleSheet("font-size: 10px; color: #666; font-weight: bold;")
            l_name.setAlignment(Qt.AlignCenter)
            vbox.addWidget(l_val)
            vbox.addWidget(l_name)
            return vbox

        grid.addLayout(make_stat("Perfect", results.get('perfects', 0), "#00FF00"))
        grid.addLayout(make_stat("Good", results.get('goods', 0), "#00B8D4"))
        grid.addLayout(make_stat("Miss", results.get('misses', 0), "#FF5555"))
        grid.addLayout(make_stat("Max Combo", results.get('max_combo', 0), "#FFFF00"))
        layout.addWidget(grid_frame)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.btn_share = QPushButton("SHARE CARD")
        self.btn_share.setCursor(Qt.PointingHandCursor)
        self.btn_share.setStyleSheet(f"""
            QPushButton {{ 
                background-color: transparent; border: 2px solid {styles.COLOR_ACCENT}; 
                color: {styles.COLOR_ACCENT}; font-weight: bold; padding: 12px; border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: rgba(0, 184, 212, 0.1); }}
        """)
        self.btn_share.clicked.connect(self.save_as_card)
        
        self.btn_cont = QPushButton("CONTINUE")
        self.btn_cont.setCursor(Qt.PointingHandCursor)
        self.btn_cont.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {styles.COLOR_ACCENT}; 
                color: {styles.COLOR_BG}; font-weight: 900; padding: 12px; border-radius: 10px;
            }}
            QPushButton:hover {{ background-color: white; }}
        """)
        self.btn_cont.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_share)
        btn_layout.addWidget(self.btn_cont)
        layout.addLayout(btn_layout)

        # Start Animation
        self.run_animations()

    def run_animations(self):
        # Rank Entry Animation (Scale & Fade)
        self.anim = QPropertyAnimation(self.rank_label, b"geometry")
        self.anim.setDuration(800)
        self.anim.setStartValue(QRect(200, 100, 300, 300))
        self.anim.setEndValue(self.rank_label.geometry())
        self.anim.setEasingCurve(QEasingCurve.OutElastic)
        self.anim.start()

    def save_as_card(self):
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        song_name = self.results.get('song', 'score').replace(' ', '_')
        filename = f"PT_Result_{song_name}_{timestamp}.png"
        
        path, _ = QFileDialog.getSaveFileName(self, "Save Result Card", filename, "PNG Images (*.png)")
        if path:
            # Hide buttons for screenshot
            self.btn_share.hide()
            self.btn_cont.hide()
            
            # Grab container
            pixmap = self.container.grab() 
            pixmap.save(path, "PNG")
            
            # Show buttons again
            self.btn_share.show()
            self.btn_cont.show()

if __name__ == "__main__":
    # Test stub - logic to handle standalone run vs module run
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # Mock styles if running standalone
    try:
        import src.ui.styles as styles
    except ModuleNotFoundError:
        class MockStyles:
            COLOR_BG = "#121212"
            COLOR_ACCENT = "#00B8D4"
            COLOR_TEXT_PRIMARY = "#FFFFFF"
        styles = MockStyles()
    
    res = {
        "song": "Test Music", "rank": "S", "score": 1250000, 
        "accuracy": 98.5, "perfects": 1500, "goods": 20, "misses": 5, 
        "max_combo": 1200, "hit_log": [(i*0.1, "PERFECT") for i in range(100)],
        "duration": 10.0
    }
    dlg = ResultsDialog(res)
    dlg.setAttribute(Qt.WA_DeleteOnClose)
    dlg.show()
    sys.exit(app.exec_())
