import datetime
import json
import os
import re
import sys

import markdown


class ConfigModel:
    """Manages configuration data."""
    def __init__(self, config_file='config.json'):
        self.settings = {}
        self._load(config_file)

    def _load(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            print(f"Loaded configuration from {config_file}.")
        except FileNotFoundError:
            print(f"🛑 Error: Configuration file '{config_file}' not found.")
            print("Please create a 'config.json' file in the project root.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"🛑 Error: Invalid JSON format in '{config_file}'. Details: {e}")
            sys.exit(1)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def __getitem__(self, key):
        return self.settings[key]


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