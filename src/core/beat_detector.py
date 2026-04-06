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
        # Unique key based on FULL PATH and difficulty (prevents collisions)
        file_hash = hashlib.md5(os.path.abspath(self.song_path).encode()).hexdigest()
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
            
            # GLOBAL PRECISION SETTING
            hop_length = 128 
            
            # 1. Standard Beat Track (The "Pulse")
            # HIGH PRECISION MODE: hop_length=128 (~5.8ms)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length, n_mels=128, aggregate=np.median)
            tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length)
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
            
            # --- PROFESSIONAL STUDIO ANALYSIS (HPSS Separation) ---
            # 1. Separate the "Soul" (Harmonic) from the "Skeleton" (Percussive)
            if progress_callback: progress_callback(40, "Separating Instruments (HPSS)...")
            
            # This is the "Heavy" part - Decomposing audio into frequency layers
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # 2. Analyze PERCUSSIVE Layer (The Beat & Rhythm)
            if progress_callback: progress_callback(50, "Analyzing Drums & Percussion...")
            
            # DEFINITION FIXED HERE
            hop_length = 128 
            
            # Percussive Onsets
            p_onset_env = librosa.onset.onset_strength(y=y_percussive, sr=sr, hop_length=hop_length, aggregate=np.median)
            try:
                p_onsets = librosa.onset.onset_detect(onset_envelope=p_onset_env, sr=sr, 
                                                    backtrack=True, units='time', hop_length=hop_length,
                                                    delta=0.05) # Low delta = Catch ghost notes/hi-hats
            except: p_onsets = np.array([])

            # 3. Analyze HARMONIC Layer (The Melody & Vocals)
            if progress_callback: progress_callback(60, "Analyzing Vocals & Instruments...")
            # Harmonic needs to catch pitch changes and "strums"
            h_onset_env = librosa.onset.onset_strength(y=y_harmonic, sr=sr, hop_length=hop_length, aggregate=np.mean)
            try:
                h_onsets = librosa.onset.onset_detect(onset_envelope=h_onset_env, sr=sr, 
                                                    backtrack=True, units='time', hop_length=hop_length,
                                                    delta=0.10) # Higher delta = Only distinct notes (don't capture sustained vibrato)
            except: h_onsets = np.array([])

            # 4. Beat Tracking (Global Tempo/Pulse) - Optional, mainly for stats or fallbacks
            if progress_callback: progress_callback(70, "Synchronizing Layers...")
            tempo, beats = librosa.beat.beat_track(y=y_percussive, sr=sr, hop_length=hop_length)
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop_length)
            
            # 5. MERGE LAYERS BASED ON DIFFICULTY
            # We filter sources so Easy modes aren't overwhelmed by Vocals/Noise
            if difficulty in ["Easy", "Normal"]:
                # Focus on Rhythm: Beats + Percussion only
                all_events = np.concatenate((beat_times, p_onsets))
            elif difficulty == "Hard":
                # Rhythm + Harmonics
                all_events = np.concatenate((beat_times, p_onsets, h_onsets))
            else:
                # Full Studio Mode
                all_events = np.concatenate((beat_times, p_onsets, h_onsets))

            all_events = np.unique(all_events)
            all_events.sort()
            
            if progress_callback: progress_callback(80, "Finalizing Note Map...")

            # Initial raw list
            self.beat_times = all_events.tolist()
            
            # NO DE-DUPLICATION HERE YET - WE DO IT POST-ENERGY ANALYSIS
            
            if progress_callback: progress_callback(80, "Optimizing gameplay...")

            # --- ENERGY ANALYSIS (Smart Speed) ---
            try:
                # Calculate RMS energy for the whole track
                print("Calculating RMS...")
                duration = librosa.get_duration(y=y, sr=sr)
                
                # Use same high precision hop_length for consistency
                rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)[0]
                times_rms = librosa.times_like(rms, sr=sr, hop_length=hop_length)
                
                # Normalize RMS to 0.0 - 1.0
                max_rms = np.max(rms) if np.max(rms) > 0 else 1.0
                norm_rms = rms / max_rms
                
                # Create a lookup function for energy at time t
                def get_energy_at(t):
                    idx = int(t * sr / hop_length)
                    if 0 <= idx < len(norm_rms):
                        return float(norm_rms[idx])
                    return 0.0
                    
                print(f"Sampling Energy Profile for duration {duration:.2f}s...")
                # Sample energy profile for JSON (resolution: 1 point every 0.1s for smoother curve?)
                energy_profile = []
                for t in np.arange(0, duration, 0.2):
                    energy_profile.append([float(t), get_energy_at(t)])

                # CLIMAX DETECTION (For Preview) using the calculated RMS
                window_size_frames = int(5.0 * sr / hop_length)
                max_energy_sum = 0
                best_start_time = 0
                
                if len(norm_rms) > window_size_frames:
                    for i in range(0, len(norm_rms) - window_size_frames, window_size_frames // 5):
                        chunk_energy = np.sum(norm_rms[i:i+window_size_frames])
                        if chunk_energy > max_energy_sum:
                            max_energy_sum = chunk_energy
                            best_start_time = times_rms[i]
                
                if best_start_time > duration - 10: best_start_time = 0
                
                # --- DENSITY FILTERING (Restored for Playability) ---
                # We filter based on difficulty limits to prevent "spam".
                # However, we allow bursts if Energy is high.
                
                print(f"Filtering beats (Base Interval: {min_interval}s)...")
                filtered_beats = []
                last_time = -10.0
                
                for t in self.beat_times:
                    local_energy = get_energy_at(t)
                    
                    # Dynamic Interval Logic
                    # If Energy is High (>0.5), we relax the limit to allow rolls/bursts.
                    # If Energy is Low, we enforce the strict difficulty limit.
                    
                    current_min_limit = min_interval
                    
                    if local_energy > 0.6:
                        # High energy: Allow notes to be slightly closer, but not too much
                        current_min_limit *= 0.75 
                    
                    # HARD SAFETY: Increase to 0.1 to prevents overlapping tiles visually
                    if current_min_limit < 0.12: current_min_limit = 0.12
                    
                    if t - last_time >= current_min_limit:
                        filtered_beats.append(t)
                        last_time = t
                
                print(f"Filtering Complete. Beats: {len(self.beat_times)} -> {len(filtered_beats)}")
                self.beat_times = filtered_beats
                
            except Exception as e:
                print(f"CRITICAL ERROR IN ENERGY ANALYSIS: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to just beats without fancy filtering if energy analysis dies
                energy_profile = []
                best_start_time = 0
            
            # Prepare result
            result = {
                "beats": self.beat_times,
                "preview_start": float(best_start_time),
                "energy_profile": energy_profile
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
            if not isinstance(e, RuntimeError):
                print(f"Error during beat analysis: {e}")
                import traceback
                traceback.print_exc()
            return {"beats": [i * 0.5 for i in range(1, 100)], "preview_start": 0.0}
