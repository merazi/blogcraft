import os
import shutil
import unittest
import json
import tempfile
import datetime
import socket
import xml.etree.ElementTree as ET
from blogcraft import cli
from controllers import BlogController
from models import ConfigModel, PostModel
from rss import RSSGenerator

class TestBlogcraft(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for each test
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Mock necessary files if needed, but BlogController handles missing config
        self.controller = BlogController()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_config_initialization(self):
        """Test that ConfigModel loads default settings correctly."""
        config = ConfigModel('test_config.json')
        self.assertEqual(config['site_title'], "My Blogcraft Site")
        self.assertEqual(config['md_dir'], "md")

    def test_new_article_creation(self):
        """Test that 'new' command creates the correct directory and file."""
        slug = "test-post"
        # Mocking EDITOR to avoid opening an editor during tests
        os.environ['EDITOR'] = 'true' 
        self.controller.new_article(slug)
        
        expected_path = os.path.join(self.test_dir, "md", slug, "article.md")
        self.assertTrue(os.path.exists(expected_path))
        
        with open(expected_path, 'r') as f:
            content = f.read()
            self.assertIn("title: Test Post", content)

    def test_build_generation(self):
        """Test that 'build' command generates the static site."""
        # 1. Create a post
        os.environ['EDITOR'] = 'true'
        self.controller.new_article("hello-world")
        
        # 2. Build the site
        # We need style.css and code_highlight.css in the test root for build to find them
        # or it will look in the app_base. Since we are in a temp dir, let's provide them.
        with open("style.css", "w") as f: f.write("body {}")
        with open("code_highlight.css", "w") as f: f.write(".code {}")
        
        self.controller.build()
        
        # 3. Verify output
        public_dir = os.path.join(self.test_dir, "public")
        self.assertTrue(os.path.exists(os.path.join(public_dir, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(public_dir, "posts", "hello-world", "index.html")))
        self.assertTrue(os.path.exists(os.path.join(public_dir, "feed.xml")))
        self.assertTrue(os.path.exists(os.path.join(public_dir, "style.css")))

    def test_frontmatter_parsing(self):
        """Test that PostModel correctly parses frontmatter."""
        post_dir = os.path.join(self.test_dir, "md", "custom-post")
        os.makedirs(post_dir)
        md_path = os.path.join(post_dir, "article.md")
        
        with open(md_path, "w") as f:
            f.write("---\ntitle: Custom Title\ndate: 2023-10-27\n---\nContent here.")
            
        post = PostModel(md_path)
        self.assertEqual(post.title, "Custom Title")
        self.assertEqual(post.date_str, "2023-10-27")
        self.assertIn("<p>Content here.</p>", post.html_content)

    def test_rss_content(self):
        """Test that RSS feed contains expected items."""
        os.environ['EDITOR'] = 'true'
        self.controller.new_article("rss-test")
        
        # Provide assets
        with open("style.css", "w") as f: f.write("")
        with open("code_highlight.css", "w") as f: f.write("")
        
        self.controller.build()
        
        rss_path = os.path.join(self.test_dir, "public", "feed.xml")
        with open(rss_path, 'r') as f:
            content = f.read()
            self.assertIn("<title>Rss Test</title>", content)
            self.assertIn("<link>http://localhost:8000/posts/rss-test/</link>", content)

    def test_archive_filters_current_posts_and_paginates(self):
        current_year = datetime.date.today().year
        os.makedirs("md/current-post")
        os.makedirs("md/old-post")
        os.makedirs("md/older-post")
        for slug, year in (("current-post", current_year), ("old-post", current_year - 1), ("older-post", current_year - 2)):
            with open(os.path.join("md", slug, "article.md"), "w") as f:
                f.write(f"---\ntitle: {slug}\ndate: {year}-05-01\n---\nContent")

        self.controller.config['archive_page_size'] = 1
        with open("style.css", "w") as f: f.write("")
        with open("code_highlight.css", "w") as f: f.write("")
        self.controller.build()

        with open("public/index.html") as f:
            index = f.read()
        with open("public/archive/index.html") as f:
            archive = f.read()
        with open("public/archive/page/2/index.html") as f:
            archive_page_two = f.read()
        self.assertIn("current-post", index)
        self.assertNotIn("old-post", index)
        self.assertIn("old-post", archive)
        self.assertIn("older-post", archive_page_two)

    def test_rss_escapes_xml_and_orders_dates(self):
        self.controller.config['site_url'] = 'https://example.com'
        self.controller.config['site_title'] = 'A & B'
        self.controller.config['site_description'] = 'A <description>'
        self.controller.config['public_dir'] = 'public'
        RSSGenerator(self.controller.config).generate([
            {'title': 'Older', 'date': '2025-12-01', 'slug': 'posts/older/'},
            {'title': 'New & Improved', 'date': '2026-01-01T12:00:00+00:00', 'slug': 'posts/new/'}
        ])

        root = ET.parse("public/feed.xml").getroot()
        channel = root.find("channel")
        self.assertEqual(channel.findtext("title"), "A & B")
        items = channel.findall("item")
        self.assertEqual(items[0].findtext("title"), "New & Improved")
        self.assertEqual(items[0].findtext("link"), "https://example.com/posts/new/")

    def test_serve_reports_port_conflict(self):
        public_dir = os.path.join(self.test_dir, "public")
        os.makedirs(public_dir)
        occupied_socket = socket.socket()
        occupied_socket.bind(("", 0))
        occupied_port = occupied_socket.getsockname()[1]
        try:
            self.controller.serve(port=occupied_port)
        finally:
            occupied_socket.close()

if __name__ == '__main__':
    unittest.main()
