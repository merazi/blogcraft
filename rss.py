import os
from datetime import datetime, timezone
from email.utils import formatdate
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from dateutil import parser

from models import ConfigModel


class RSSGenerator:
    """Handles the generation of an RSS feed for the static site."""

    def __init__(self, config: ConfigModel):
        self.config: ConfigModel = config
        self.site_title: str = config.get('site_title', 'My Blog')
        # RSS requires absolute URLs, default to localhost if not set
        self.site_url: str = config.get('site_url', 'http://localhost:8000').rstrip('/')
        self.description: str = config.get('site_description', 'Recent content.')
        self.public_dir: str = config.get('public_dir', 'public')
        self.rss_filename: str = 'feed.xml'

    def generate(self, posts: List[Dict[str, Any]]) -> None:
        """
        Generates the RSS feed if enabled in config.

        :param posts: List of post dictionaries. Each post is expected to have
                      'title', 'date' (YYYY-MM-DD), and 'slug'.
        """
        if not self.config.get('rss', False):
            return

        print("Generating RSS feed...")

        # Sort posts by their source date, keeping the feed deterministic.
        sorted_posts = sorted(posts, key=self._sort_key, reverse=True)
        channel = ET.Element('channel')
        self._add_text(channel, 'title', self.site_title)
        self._add_text(channel, 'link', self.site_url)
        self._add_text(channel, 'description', self.description)
        self._add_text(channel, 'lastBuildDate', formatdate(usegmt=True))
        self._add_text(channel, 'generator', 'blogcraft')

        for post in sorted_posts:
            channel.append(self._create_item(post))

        rss = ET.Element('rss', {'version': '2.0'})
        rss.append(channel)
        rss_xml = ET.tostring(rss, encoding='unicode')
        rss_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + rss_xml

        output_path = os.path.join(self.public_dir, self.rss_filename)
        os.makedirs(self.public_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rss_xml)

        print(f"RSS feed written to {output_path}")

    def _create_item(self, post: Dict[str, Any]) -> ET.Element:
        slug = str(post.get('slug', '')).lstrip('/')
        link = urljoin(f'{self.site_url}/', slug)
        item = ET.Element('item')
        self._add_text(item, 'title', str(post.get('title', 'Untitled')))
        self._add_text(item, 'link', link)
        guid = ET.SubElement(item, 'guid', {'isPermaLink': 'true'})
        guid.text = link
        self._add_text(item, 'pubDate', self._parse_date(post.get('date')))
        self._add_text(item, 'description', str(post.get('description', '')))
        return item

    @staticmethod
    def _add_text(parent: ET.Element, name: str, value: str) -> None:
        element = ET.SubElement(parent, name)
        element.text = value

    def _parse_date(self, date_str: Optional[str]) -> str:
        """Converts date string to RFC 822 format."""
        if not date_str:
            return ''
        try:
            dt = parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return formatdate(dt.timestamp(), usegmt=True)
        except (ValueError, TypeError, OverflowError):
            return ''

    @staticmethod
    def _sort_key(post: Dict[str, Any]) -> datetime:
        date_str = post.get('date')
        if not date_str:
            return datetime.min
        try:
            parsed = parser.parse(str(date_str))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        except (ValueError, TypeError, OverflowError):
            return datetime.min
