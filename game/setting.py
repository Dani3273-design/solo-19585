import json
import os


class Settings:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        self.difficulty = 2
        self.sound_enabled = True
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.difficulty = data.get('difficulty', 2)
                    self.sound_enabled = data.get('sound_enabled', True)
            except Exception:
                pass

    def save(self):
        data = {
            'difficulty': self.difficulty,
            'sound_enabled': self.sound_enabled
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def set_difficulty(self, level):
        if 1 <= level <= 3:
            self.difficulty = level
            self.save()

    def get_difficulty(self):
        return self.difficulty

    def set_sound(self, enabled):
        self.sound_enabled = enabled
        self.save()

    def get_sound(self):
        return self.sound_enabled


settings = Settings()
