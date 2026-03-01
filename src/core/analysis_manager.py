import os
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QRunnable, QThreadPool
from src.core.beat_detector import BeatDetector

class AnalysisWorker(QRunnable):
    """Worker that runs as a task in a thread pool to analyze a single song."""
    class Signals(QObject):
        progress = pyqtSignal(str, float)    # Song Name, Percent (0-100)
        finished = pyqtSignal(str)           # Song Name (All diffs done)
        diff_finished = pyqtSignal(str, str) # Song Name, Difficulty Name
    
    def __init__(self, song_path, difficulties):
        super().__init__()
        self.song_path = song_path
        self.difficulties = difficulties
        self.signals = self.Signals()
        self._is_running = True

    def run(self):
        song_name = os.path.basename(self.song_path)
        total_diffs = len(self.difficulties)
        
        try:
            # Initialize detector (lightweight)
            detector = BeatDetector(self.song_path)
            
            for i, diff in enumerate(self.difficulties):
                if not self._is_running: break
                
                # Check if cache exists
                cache_path = detector._get_cache_path(diff)
                
                # Base progress for this difficulty
                base_prog = (i / total_diffs) * 100
                
                if not os.path.exists(cache_path):
                    print(f"DEBUG Parallel: Generating cache for {song_name} [{diff}]")
                    
                    def internal_prog(val, msg):
                        if not self._is_running: return
                        try:
                            overall = base_prog + (val / total_diffs)
                            self.signals.progress.emit(self.song_path, overall)
                        except: pass
                        
                    detector.analyze(diff, progress_callback=internal_prog, stop_check=lambda: not self._is_running)
                
                # Notify this specific diff is done/ready
                try: self.signals.diff_finished.emit(self.song_path, diff)
                except: pass
                
            try: self.signals.finished.emit(self.song_path)
            except: pass
        except Exception as e:
            print(f"Parallel Worker Error ({song_name}): {e}")

    def stop(self):
        self._is_running = False

class AnalysisManager(QObject):
    """Manages a pool of analysis workers."""
    # Signals to bubble up to UI
    worker_progress = pyqtSignal(str, float)
    worker_finished = pyqtSignal(str)
    worker_diff_finished = pyqtSignal(str, str)
    all_finished = pyqtSignal()

    def __init__(self, songs, max_threads=1):
        super().__init__()
        self.max_threads = max_threads
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(max_threads)
        self.active_workers = {} # song_path -> worker
        self.songs_in_queue = set()
        
        for s in songs:
            self.add_song(s)

    def set_max_threads(self, count):
        self.max_threads = count
        self.pool.setMaxThreadCount(count)

    def add_song(self, song_path):
        if song_path in self.songs_in_queue: return
        self.songs_in_queue.add(song_path)
        
        worker = AnalysisWorker(song_path, ["Easy", "Normal", "Hard", "Insane", "Impossible", "God", "Beyond"])
        # Map worker signals to manager signals (UI connects to manager)
        worker.signals.progress.connect(self.worker_progress.emit)
        worker.signals.finished.connect(self.worker_finished.emit)
        worker.signals.diff_finished.connect(self.worker_diff_finished.emit)
        
        self.active_workers[song_path] = worker
        self.pool.start(worker)

    def stop(self):
        for worker in self.active_workers.values():
            worker.stop()
        self.pool.clear()
        self.active_workers.clear()
        self.songs_in_queue.clear()

    def add_songs(self, new_songs):
        for s in new_songs:
            self.add_song(s)

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
