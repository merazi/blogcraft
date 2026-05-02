import datetime
import json
import os
import re
import sys

import markdown


class ConfigModel:
    """Manages configuration data."""
    DEFAULT_SETTINGS = {
        "site_title": "My Blogcraft Site",
        "site_url": "http://localhost:8000",
        "site_subtitle": "Built with Blogcraft",
        "rss": True,
        "md_dir": "md",
        "public_dir": "public",
        "post_filename": "article.md",
        "assets_dir": "files",
        "default_editor": "nano",
        "socials": {}
    }

    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.settings = self.DEFAULT_SETTINGS.copy()
        self._load(config_file)

    def _load(self, config_file):
        if not os.path.exists(config_file):
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                self.settings.update(user_settings)
            print(f"Loaded configuration from {config_file}.")
        except json.JSONDecodeError as e:
            print(f"⚠️ Warning: Invalid JSON format in '{config_file}'. Using defaults. Details: {e}")

    def save(self):
        """Saves current settings to the config file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"🛑 Error saving configuration: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value


class PostModel:
    """Represents a single blog post (Model)."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.metadata = {}
        self.content = ""
        self.html_content = ""
        self._parse()

    def _parse(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        # Frontmatter extraction
        frontmatter_match = re.match(r'---\s*?\n(.*?)\n---\s*?\n?(.*)', raw_content, re.DOTALL)
        if frontmatter_match:
            frontmatter_block = frontmatter_match.group(1).strip()
            self.content = frontmatter_match.group(2).strip()
            for line in frontmatter_block.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    self.metadata[key.strip()] = value.strip()
        else:
            self.content = raw_content

        # Markdown conversion
        self.html_content = markdown.markdown(
            self.content,
            extensions=['codehilite', 'fenced_code']
        )

    @property
    def title(self):
        default_title = os.path.basename(os.path.dirname(self.file_path)).replace('-', ' ').title()
        return self.metadata.get('title', default_title)

    @property
    def date_str(self):
        return self.metadata.get('date', "N/A")

    @property
    def date_obj(self):
        date_str = self.date_str
        if not date_str or date_str == "N/A":
            return datetime.date.min
        try:
            return datetime.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return datetime.date.min