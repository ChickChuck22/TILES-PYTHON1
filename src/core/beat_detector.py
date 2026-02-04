import librosa
import numpy as np
import os

import json
import hashlib

class BeatDetector:
    def __init__(self, song_path, cache_dir="assets/cache"):
        self.song_path = song_path
        self.cache_dir = cache_dir
        self.beat_times = []
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, difficulty):
        # Unique key based on filename and difficulty
        file_hash = hashlib.md5(os.path.basename(self.song_path).encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{file_hash}_{difficulty}.json")

    def analyze(self, difficulty="Normal", progress_callback=None):
        """Analyzes the song to find beat timestamps with caching."""
        cache_path = self._get_cache_path(difficulty)
        
        # Check cache
        if os.path.exists(cache_path):
            if progress_callback: progress_callback(50, "Loading from cache...")
            with open(cache_path, 'r') as f:
                self.beat_times = json.load(f)
            if progress_callback: progress_callback(100, "Ready!")
            return self.beat_times

        try:
            if progress_callback: progress_callback(10, "Loading audio file...")
            
            # Difficulty mapping
            diff_settings = {"Easy": 0.8, "Normal": 0.5, "Hard": 0.35, "Insane": 0.25, "Impossible": 0.15}
            min_interval = diff_settings.get(difficulty, 0.5)

            y, sr = librosa.load(self.song_path)
            if progress_callback: progress_callback(40, "Analyzing rhythmic peaks...")
            
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            if progress_callback: progress_callback(70, "Tracking beats...")
            
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            self.beat_times = librosa.frames_to_time(beats, sr=sr).tolist()
            
            # CLIMAX DETECTION (For Preview)
            # We calculate RMS energy over the track
            rms = librosa.feature.rms(y=y)[0]
            times = librosa.times_like(rms, sr=sr)
            
            # Find the window of 5 seconds with max energy
            window_size_frames = int(5.0 * sr / 512) # hop_length default is 512
            max_energy = 0
            best_start_time = 0
            
            # Simple sliding window average
            if len(rms) > window_size_frames:
                # Use convolution for moving average if available, or simple loop
                # Just sampling every 1 second is enough for preview finding
                for i in range(0, len(rms) - window_size_frames, window_size_frames // 5):
                    chunk_energy = np.sum(rms[i:i+window_size_frames])
                    if chunk_energy > max_energy:
                        max_energy = chunk_energy
                        best_start_time = times[i]
            
            # Ensure we don't start at the very end
            duration = librosa.get_duration(y=y, sr=sr)
            if best_start_time > duration - 10:
                best_start_time = 0
            
            # Filter beats (keep existing logic)
            filtered_beats = []
            last_time = -1.0
            for t in self.beat_times:
                if t - last_time >= min_interval:
                    filtered_beats.append(t)
                    last_time = t
            
            self.beat_times = filtered_beats
            
            
            # Prepare result
            result = {
                "beats": self.beat_times,
                "preview_start": float(best_start_time)
            }
            
            # Save to cache
            if progress_callback: progress_callback(90, "Saving to cache...")
            with open(cache_path, 'w') as f:
                json.dump(result, f)
            
            if progress_callback: progress_callback(100, "Ready!")
            return result
            
        except Exception as e:
            print(f"Error during beat analysis: {e}")
            return {"beats": [i * 0.5 for i in range(1, 100)], "preview_start": 0.0}
