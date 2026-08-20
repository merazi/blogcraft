import datetime
import json
import os
from typing import Any, Dict, Optional

import markdown
import yaml


class ConfigModel:
    """Manages configuration data."""
    DEFAULT_SETTINGS: Dict[str, Any] = {
        "site_title": "My Blogcraft Site",
        "site_url": "http://localhost:8000",
        "site_subtitle": "Built with Blogcraft",
        "rss": True,
        "archive_page_size": 10,
        "md_dir": "md",
        "public_dir": "public",
        "post_filename": "article.md",
        "assets_dir": "files",
        "default_editor": "nano",
        "socials": {}
    }

    def __init__(self, config_file: str = 'config.json'):
        self.config_file: str = config_file
        self.settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self._load(config_file)

    def _load(self, config_file: str) -> None:
        if not os.path.exists(config_file):
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                self.settings.update(user_settings)
            print(f"Loaded configuration from {config_file}.")
        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Invalid JSON format in '{config_file}'. Using defaults. Details: {e}")

    def save(self) -> None:
        """Saves current settings to the config file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"🛑 Error saving configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.settings[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.settings[key] = value


class PostModel:
    """Represents a single blog post (Model)."""
    def __init__(self, file_path: str):
        self.file_path: str = file_path
        self.metadata: Dict[str, str] = {}
        self.content: str = ""
        self.html_content: str = ""
        self._parse()

    def _parse(self) -> None:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        if raw_content.startswith('---'):
            parts = raw_content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_block = parts[1].strip()
                self.content = parts[2].strip()
                
                try:
                    parsed_meta = yaml.safe_load(frontmatter_block)
                    if isinstance(parsed_meta, dict):
                        # Ensure all keys and values are strings to maintain compatibility
                        self.metadata = {str(k): str(v) for k, v in parsed_meta.items()}
                except yaml.YAMLError as e:
                    print(f"⚠️ Warning: Invalid YAML in frontmatter of {self.file_path}: {e}")
            else:
                self.content = raw_content
        else:
            self.content = raw_content

        # Markdown conversion
        self.html_content = markdown.markdown(
            self.content,
            extensions=['codehilite', 'fenced_code']
        )

    @property
    def title(self) -> str:
        default_title = os.path.basename(os.path.dirname(self.file_path)).replace('-', ' ').title()
        return self.metadata.get('title', default_title)

    @property
    def date_str(self) -> str:
        return self.metadata.get('date', "N/A")

    @property
    def date_obj(self) -> datetime.date:
        date_str = self.date_str
        if not date_str or date_str == "N/A":
            return datetime.date.min
        try:
            from dateutil import parser
            return parser.parse(date_str).date()
        except (ValueError, TypeError):
            return datetime.date.min
