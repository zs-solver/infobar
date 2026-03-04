"""
数据持久化 - JSON存储
"""
import json
import os

class Storage:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "columns": [
                "A项目\nX功能",
                "A项目\nY功能",
                "B项目",
                "C项目"
            ],
            "window": {"x": 100, "y": 50, "width": 800, "height": 35},
            "theme": {
                "bg_color": "#2b2b2b",
                "bg_opacity": 1.0,
                "text_color": "#ffffff",
                "text_opacity": 1.0
            }
        }

    def load(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.default_config

    def save(self, config):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
