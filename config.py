import json

class ConfigHandler:
    """Base class for configuration management"""
    def __init__(self, config_path):
        self.default_config = {}
        self.config_path = config_path

    def load_config(self, allow_empty=False):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if isinstance(e, FileNotFoundError) and not allow_empty:
                raise ValueError(f"Configuration file '{self.config_path}' not found.")
            elif isinstance(e, json.JSONDecodeError):
                raise ValueError(f"Configuration file '{self.config_path}' is malformed.")
            # Use & create default config if file not found or empty
            json.dump(self.default_config, open(self.config_path, 'w', encoding='utf-8'), indent=2)
            return self.default_config.copy()

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()


class ProgramConfig(ConfigHandler):
    """Configuration for the main program settings"""
    def __init__(self, config_path="program_config.json"):
        super().__init__(config_path)
        self.default_config = {
            "window_size": [800, 600],
            "theme": "light",
        }
        self.config = self.load_config(allow_empty=True)

    def get_window_size(self):
        return tuple(self.get("window_size", [800, 600]))

    def set_window_size(self, size):
        self.set("window_size", list(size))

    def get_theme(self):
        return self.get("theme", "light")

    def set_theme(self, theme):
        self.set("theme", theme)



class DataConfig(ConfigHandler):
    """Configuration for data management settings"""
    def __init__(self, config_path="data_config.json"):
        super().__init__(config_path)
        self.config = self.load_config(allow_empty=False)

