from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QFileDialog, QLabel)
from PyQt5.QtCore import Qt

class MusicLibraryDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("Manage Music Library")
        self.resize(500, 400)
        
        self.init_ui()
        self.load_folders()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        label = QLabel("Music Folders:")
        layout.addWidget(label)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        # Buttons for add/remove
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Folder")
        self.remove_btn = QPushButton("Remove Selected")
        
        self.add_btn.clicked.connect(self.add_folder)
        self.remove_btn.clicked.connect(self.remove_folder)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)
        
        # OK/Cancel
        bottom_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.ok_btn)
        bottom_layout.addWidget(self.cancel_btn)
        layout.addLayout(bottom_layout)
        
        # Apply modern-ish styles
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; color: white; }
            QLabel { color: #ccc; font-size: 14px; }
            QListWidget { 
                background-color: #252525; 
                border: 1px solid #333; 
                color: #eee; 
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton { 
                background-color: #333; 
                color: white; 
                border: none; 
                padding: 8px 15px; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #444; }
            QPushButton#ok_btn { background-color: #2e7d32; }
            QPushButton#ok_btn:hover { background-color: #388e3c; }
        """)
        self.ok_btn.setObjectName("ok_btn")

    def load_folders(self):
        self.list_widget.clear()
        folders = self.settings_manager.get_music_folders()
        for folder in folders:
            self.list_widget.addItem(folder)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            if self.settings_manager.add_music_folder(folder):
                self.load_folders()

    def remove_folder(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            folder = current_item.text()
            if self.settings_manager.remove_music_folder(folder):
                self.load_folders()
