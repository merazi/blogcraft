import os
import html
from datetime import datetime
from email.utils import formatdate

class RSSGenerator:
    """Handles the generation of an RSS feed for the static site."""

    def __init__(self, config):
        self.config = config
        self.site_title = config.get('site_title', 'My Blog')
        # RSS requires absolute URLs, default to localhost if not set
        self.site_url = config.get('site_url', 'http://localhost:8000').rstrip('/')
        self.description = config.get('site_description', 'Recent content.')
        self.public_dir = config.get('public_dir', 'public')
        self.rss_filename = 'feed.xml'

    def generate(self, posts):
        """
        Generates the RSS feed if enabled in config.

        :param posts: List of post dictionaries. Each post is expected to have
                      'title', 'date' (YYYY-MM-DD), and 'slug'.
        """
        if not self.config.get('rss', False):
            return

        print("Generating RSS feed...")

        items = []
        # Sort posts by date descending
        sorted_posts = sorted(posts, key=lambda x: x.get('date', ''), reverse=True)

        for post in sorted_posts:
            items.append(self._create_item(post))

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>{html.escape(self.site_title)}</title>
    <link>{self.site_url}</link>
    <description>{html.escape(self.description)}</description>
    <lastBuildDate>{formatdate(usegmt=True)}</lastBuildDate>
    <generator>blogcraft</generator>
    {''.join(items)}
</channel>
</rss>"""

        output_path = os.path.join(self.public_dir, self.rss_filename)
        os.makedirs(self.public_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rss_xml)

        print(f"RSS feed written to {output_path}")

    def _create_item(self, post):
        title = html.escape(post.get('title', 'Untitled'))
        slug = post.get('slug', '')
        link = f"{self.site_url}/{slug}"
        # Use description or excerpt if available, otherwise empty
        description = html.escape(post.get('description', ''))

        date_str = post.get('date')
        pub_date = self._parse_date(date_str)

        return f"""
    <item>
        <title>{title}</title>
        <link>{link}</link>
        <guid>{link}</guid>
        <pubDate>{pub_date}</pubDate>
        <description>{description}</description>
    </item>"""

    def _parse_date(self, date_str):
        """Converts YYYY-MM-DD string to RFC 822 format."""
        if not date_str:
            return formatdate(usegmt=True)
        try:
            dt = datetime.strptime(str(date_str), '%Y-%m-%d')
            return formatdate(dt.timestamp(), usegmt=True)
        except ValueError:
            return formatdate(usegmt=True)