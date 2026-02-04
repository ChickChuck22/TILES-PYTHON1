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
            
            # Difficulty mapping: (Min Interval, Onset Sensitivity)
            # Min Interval: Minimum time between notes (seconds)
            # Onset Delta: Sensitivity for picking up weak notes (lower = more notes)
            diff_settings = {
                "Easy":       (0.80, 2.0),
                "Normal":     (0.50, 1.5),
                "Hard":       (0.35, 1.0),
                "Insane":     (0.25, 0.7),
                "Impossible": (0.15, 0.4),
                "God":        (0.12, 0.2),
                "Beyond":     (0.08, 0.1)
            }
            min_interval, onset_delta = diff_settings.get(difficulty, (0.5, 1.0))

            y, sr = librosa.load(self.song_path)
            if progress_callback: progress_callback(30, "Analyzing Rhythm & Vocals...")
            
            # 1. Standard Beat Track (The "Pulse")
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            beat_times = librosa.frames_to_time(beats, sr=sr)
            
            # 2. Onset Detection (The "Vocals/Melody")
            # We look for peaks in the onset envelope that represent notes
            if progress_callback: progress_callback(60, "Capturing details...")
            
            # Use peak picking on onset envelope for finer details
            # delta controls threshold. Lower delta = more peaks = more notes.
            onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, 
                                              backtrack=True, 
                                              units='time', 
                                              delta=onset_delta)
            
            # 3. Combine both sources
            # We want the steady beat (rhythm) AND the extra details (vocals)
            combined_times = np.concatenate((beat_times, onsets))
            combined_times = np.unique(combined_times) # Remove exact duplicates
            combined_times.sort()
            
            self.beat_times = combined_times.tolist()
            
            if progress_callback: progress_callback(80, "Optimizing gameplay...")

            # CLIMAX DETECTION (For Preview)
            rms = librosa.feature.rms(y=y)[0]
            times_rms = librosa.times_like(rms, sr=sr)
            window_size_frames = int(5.0 * sr / 512)
            max_energy = 0
            best_start_time = 0
            
            if len(rms) > window_size_frames:
                for i in range(0, len(rms) - window_size_frames, window_size_frames // 5):
                    chunk_energy = np.sum(rms[i:i+window_size_frames])
                    if chunk_energy > max_energy:
                        max_energy = chunk_energy
                        best_start_time = times_rms[i]
            
            duration = librosa.get_duration(y=y, sr=sr)
            if best_start_time > duration - 10:
                best_start_time = 0
            
            # Filter beats (Limit density based on difficulty)
            filtered_beats = []
            last_time = -10.0
            
            # Sophisticated Filtering:
            # We iterate through the sorted times. If a note is too close to the previous one,
            # we skip it UNLESS it's a "Standard Beat" (we prioritize the main beat over extra onsets? 
            # Actually, standard filtering is enough: just enforce physical speed limit).
            
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
            try:
                with open(cache_path, 'w') as f:
                    json.dump(result, f)
            except Exception as e:
                print(f"Cache save failed: {e}")
            
            if progress_callback: progress_callback(100, "Ready!")
            return result
            
        except Exception as e:
            print(f"Error during beat analysis: {e}")
            import traceback
            traceback.print_exc()
            return {"beats": [i * 0.5 for i in range(1, 100)], "preview_start": 0.0}
