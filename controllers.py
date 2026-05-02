import datetime
import glob
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import time
import threading
from typing import List, Tuple, Dict, Any, Optional

from models import ConfigModel, PostModel
from views import BlogView, Templates
from rss import RSSGenerator


class BlogController:
    """Orchestrates the site generation (Controller)."""
    
    def __init__(self):
        self.config: ConfigModel = ConfigModel()
        self.view: BlogView = BlogView(self.config)

    def init_project(self) -> None:
        """Interactive initialization of the blog project."""
        print("🚀 Welcome to Blogcraft! Let's set up your blog.\n")
        
        fields = [
            ("site_title", "Blog Title"),
            ("site_subtitle", "Blog Subtitle"),
            ("site_url", "Site URL"),
            ("default_editor", "Default Editor"),
        ]

        for key, label in fields:
            value = input(f"{label} [{self.config[key]}]: ").strip()
            if value:
                self.config[key] = value

        self.config.save()
        os.makedirs(self.config['md_dir'], exist_ok=True)
        print(f"✅ Created source directory: {self.config['md_dir']}")
        print("\n✨ Setup complete! You can now create a post with 'python blogcraft.py new my-post'.")

    def serve(self, port: int = 8000, watch: bool = False) -> None:
        """Starts a local preview server."""
        public_dir = self.config['public_dir']
        
        if not os.path.exists(public_dir):
            print(f"⚠️  Public directory '{public_dir}' not found. Building site first...")
            self.build()

        os.chdir(public_dir)
        
        if watch:
            self._start_watcher()

        print(f"🌐 Serving blog at http://localhost:{port}")
        print("Press Ctrl+C to stop.")
        
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Server stopped.")
                sys.exit(0)

    def _start_watcher(self) -> None:
        """Initializes and starts the file system watcher thread."""
        md_dir = self.config['md_dir']
        print(f"👀 Watch mode enabled. Monitoring '{md_dir}' for changes...")
        
        # Absolute path to root to ensure watcher works regardless of CWD
        root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
        full_md_path = os.path.join(root_dir, md_dir)

        def watch_loop():
            last_mtime = self._get_max_mtime(full_md_path)
            while True:
                time.sleep(1)
                current_mtime = self._get_max_mtime(full_md_path)
                if current_mtime > last_mtime:
                    print("\n🔄 Changes detected! Rebuilding...")
                    current_cwd = os.getcwd()
                    os.chdir(root_dir)
                    self.build()
                    os.chdir(current_cwd)
                    last_mtime = current_mtime
        
        watcher = threading.Thread(target=watch_loop, daemon=True)
        watcher.start()

    def _get_max_mtime(self, directory: str) -> float:
        """Helper to get the latest modification time in a directory tree."""
        max_mtime = 0.0
        for root, _, files in os.walk(directory):
            for f in files:
                path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(path)
                    if mtime > max_mtime:
                        max_mtime = mtime
                except OSError:
                    continue
        return max_mtime

    def build(self) -> None:
        """Orchestrates the full site build process."""
        md_dir = self.config['md_dir']
        if not os.path.exists(md_dir):
            print(f"🛑 Error: Source directory '{md_dir}' not found.")
            return

        print("🔨 Building site...")
        self._prep_public_dir()
        self._copy_external_assets()

        posts_data = self._process_all_posts()
        posts_data.sort(key=lambda x: x[0].date_obj, reverse=True)

        self._generate_metadata_pages(posts_data)

        print(f"\n✨ Site generation complete! ({len(posts_data)} posts)")
        print(f"   Output: {self.config['public_dir']}/")

    def _prep_public_dir(self) -> None:
        """Cleans and recreates the public output directory."""
        public_dir = self.config['public_dir']
        if os.path.exists(public_dir):
            shutil.rmtree(public_dir)
        os.makedirs(public_dir, exist_ok=True)

    def _process_all_posts(self) -> List[Tuple[PostModel, str]]:
        """Finds and renders all Markdown posts."""
        md_dir = self.config['md_dir']
        post_filename = self.config['post_filename']
        public_dir = self.config['public_dir']
        
        posts_data: List[Tuple[PostModel, str]] = []
        search_pattern = os.path.join(md_dir, '**', post_filename)

        for md_path in glob.glob(search_pattern, recursive=True):
            try:
                post = PostModel(md_path)
                post_dir = os.path.dirname(md_path)
                
                # Calculate output paths
                rel_post_dir = os.path.relpath(post_dir, md_dir)
                target_dir = os.path.join(public_dir, 'posts', rel_post_dir)
                target_html_path = os.path.join(target_dir, 'index.html')
                
                # Render and Save
                os.makedirs(target_dir, exist_ok=True)
                with open(target_html_path, 'w', encoding='utf-8') as f:
                    f.write(self.view.render_post(post))
                
                self._copy_post_assets(post_dir, target_dir)
                
                url = os.path.relpath(target_html_path, public_dir)
                posts_data.append((post, url))
                print(f"  ✅ Post: {post.title}")

            except Exception as e:
                print(f"  ❌ Error processing {md_path}: {e}")
        
        return posts_data

    def _generate_metadata_pages(self, posts_data: List[Tuple[PostModel, str]]) -> None:
        """Generates the index, RSS feed, and 404 pages."""
        public_dir = self.config['public_dir']

        # RSS
        rss_items = []
        for post, url in posts_data:
            slug = url.replace(os.sep, '/')
            if slug.endswith('index.html'):
                slug = slug[:-10]
            
            rss_items.append({
                'title': post.title,
                'date': post.date_str,
                'slug': slug,
                'description': getattr(post, 'description', '')
            })
        
        RSSGenerator(self.config).generate(rss_items)

        # Index
        index_html = self.view.render_index(posts_data)
        with open(os.path.join(public_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("  ✅ Index")

        # 404
        with open(os.path.join(public_dir, '404.html'), 'w', encoding='utf-8') as f:
            f.write(self.view.render_404())
        print("  ✅ 404 Page")

    def new_article(self, slug: str) -> None:
        """Creates a new post template and opens it in the default editor."""
        md_dir = self.config['md_dir']
        post_filename = self.config['post_filename']
        assets_dir = self.config['assets_dir']

        target_dir = os.path.join(md_dir, slug)
        if os.path.exists(target_dir):
            print(f"🛑 Error: Article directory already exists: '{target_dir}'")
            return

        os.makedirs(os.path.join(target_dir, assets_dir))
        target_md_path = os.path.join(target_dir, post_filename)
        
        post_title = slug.replace('-', ' ').title()
        content = Templates.NEW_ARTICLE.format(
            title=post_title,
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            slug=slug,
            assets_dir=assets_dir
        )
        
        with open(target_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"\n🎉 Successfully created new article structure at: '{target_dir}'")
        self._open_in_editor(target_md_path)
        print("\nNext step: Run 'python blogcraft.py build' to generate the site.")

    def _open_in_editor(self, file_path: str) -> None:
        """Attempts to open a file in the user's preferred editor."""
        editor = os.environ.get('EDITOR', self.config.get('default_editor', 'nano'))
        print(f"🖋️ Opening article in your editor ({editor})...")
        try:
            subprocess.call([editor, file_path])
            print("\n✅ Editor closed. Your content is saved!")
        except FileNotFoundError:
            print(f"\n🛑 Error: Editor command '{editor}' not found.")

    def _copy_external_assets(self) -> None:
        """Copies core CSS files from the application base or CWD to public."""
        public_dir = self.config['public_dir']
        assets = ['code_highlight.css', 'style.css']
        
        # Determine application base (works for source and pyinstaller bundles)
        app_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

        for filename in assets:
            # Prefer local override in CWD, fall back to app bundle
            src = filename if os.path.exists(filename) else os.path.join(app_base, filename)
            
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(public_dir, filename))
            else:
                print(f"  ⚠️ Warning: External asset '{filename}' not found.")

    def _copy_post_assets(self, source_dir: str, target_dir: str) -> None:
        """Copies all files from a post directory (except the Markdown file) to target."""
        post_filename = self.config['post_filename']
        for item in os.listdir(source_dir):
            if item == post_filename:
                continue
            
            src = os.path.join(source_dir, item)
            dst = os.path.join(target_dir, item)
            
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
