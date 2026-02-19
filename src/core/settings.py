import json
import os

SETTINGS_FILE = "settings.json"

class SettingsManager:
    def __init__(self):
        self.settings = {
            "music_folders": []
        }
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    # Merge with defaults
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_music_folders(self):
        return self.settings.get("music_folders", [])

    def add_music_folder(self, path):
        folders = self.get_music_folders()
        if path not in folders:
            folders.append(path)
            self.settings["music_folders"] = folders
            self.save()
            return True
        return False

    def remove_music_folder(self, path):
        folders = self.get_music_folders()
        if path in folders:
            folders.remove(path)
            self.settings["music_folders"] = folders
            self.save()
            return True
        return False
