import os
import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from src.core.beat_detector import BeatDetector

class AnalysisWorker(QObject):
    """Worker that runs in a separate thread to analyze songs."""
    progress = pyqtSignal(str, float) # Song Name, Percent (0-100)
    finished = pyqtSignal(str)        # Song Name (All diffs done)
    diff_finished = pyqtSignal(str, str) # Song Name, Difficulty Name
    all_finished = pyqtSignal()
    
    def __init__(self, songs, difficulties=["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"]):
        super().__init__()
        self.songs = list(songs) # Current queue
        self.difficulties = ["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"]
        self._is_running = True
        self._index = 0

    def run(self):
        print("DEBUG: AnalysisWorker started.")
        total_diffs = len(self.difficulties)
        
        while self._is_running:
            if self._index >= len(self.songs):
                time.sleep(1.0) # Wait for more
                continue
            
            song_path = self.songs[self._index]
            self._index += 1
            
            song_name = os.path.basename(song_path)
            
            try:
                # Initialize detector (lightweight)
                detector = BeatDetector(song_path)
                
                for i, diff in enumerate(self.difficulties):
                    if not self._is_running: break
                    
                    # Check if cache exists
                    cache_path = detector._get_cache_path(diff)
                    
                    # Base progress for this difficulty
                    base_prog = (i / total_diffs) * 100
                    
                    if not os.path.exists(cache_path):
                        print(f"DEBUG: Generating cache for {song_name} [{diff}]")
                        
                        # INTERNAL Callback to map 0-100 of step to overall song progress
                        def internal_prog(val, msg):
                            # SAFETY: Check if we are still running/not deleted
                            if not self._is_running: return
                            try:
                                # overall = base_prog + (val / total_diffs)
                                overall = base_prog + (val / total_diffs)
                                self.progress.emit(song_path, overall)
                            except RuntimeError:
                                # This happens if the C++ object is already deleted
                                pass
                            
                        detector.analyze(diff, progress_callback=internal_prog, stop_check=lambda: not self._is_running)
                        time.sleep(0.05) 
                    else:
                        pass
                    
                    # Notify this specific diff is done/ready
                    try: self.diff_finished.emit(song_path, diff)
                    except RuntimeError: pass
                    
                try: self.finished.emit(song_path)
                except RuntimeError: pass
            except Exception as e:
                print(f"Error checking {song_name}: {e}")
            
        print("DEBUG: AnalysisWorker finished all tasks.")
        try: self.all_finished.emit()
        except RuntimeError: pass

    def stop(self):
        self._is_running = False

class AnalysisManager(QObject):
    """Wrapper to manage the thread and worker."""
    def __init__(self, songs):
        super().__init__()
        self.thread = QThread()
        self.worker = AnalysisWorker(songs)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

    def wait(self):
        self.thread.wait()

    def is_running(self):
        return self.thread.isRunning()

    def add_songs(self, new_songs):
        """Dynamically add songs to the analysis queue."""
        for s in new_songs:
            if s not in self.worker.songs:
                self.worker.songs.append(s)

class AnalysisThread(QThread):
    """Thread for a single song analysis (used for previews)."""
    finished = pyqtSignal(object)
    progress = pyqtSignal(float, str)
    
    def __init__(self, song_path, difficulty="Normal"):
        super().__init__()
        self.song_path = song_path
        self.difficulty = difficulty
        
    def run(self):
        try:
            detector = BeatDetector(self.song_path)
            # Internal callback to emit the signal
            def internal_cb(val, msg):
                try: self.progress.emit(float(val), msg)
                except RuntimeError: pass
                
            result = detector.analyze(self.difficulty, progress_callback=internal_cb)
            try: self.finished.emit(result)
            except RuntimeError: pass
        except Exception as e:
            print(f"Preview/Analysis Error: {e}")
            try: self.finished.emit(None)
            except RuntimeError: pass
