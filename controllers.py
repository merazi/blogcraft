import datetime
import http.server
import shutil
import socketserver
import subprocess
import sys
import os
import threading
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

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
        Path(self.config['md_dir']).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created source directory: {self.config['md_dir']}")
        print("\n✨ Setup complete! You can now create a post with 'python blogcraft.py new my-post'.")

    def serve(self, port: int = 8000, watch: bool = False) -> None:
        """Starts a local preview server."""
        public_dir = Path(self.config['public_dir'])
        
        if not public_dir.exists():
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
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        md_dir = self.config['md_dir']
        print(f"👀 Watch mode enabled. Monitoring '{md_dir}' for changes...")
        
        root_dir = Path.cwd().parent.resolve()
        full_md_path = root_dir / md_dir

        class RebuildHandler(FileSystemEventHandler):
            def __init__(self, controller):
                self.controller = controller
                self.root_dir = root_dir

            def on_any_event(self, event):
                if event.is_directory:
                    return
                print("\n🔄 Changes detected! Rebuilding...")
                current_cwd = Path.cwd()
                os.chdir(self.root_dir)
                self.controller.build()
                os.chdir(current_cwd)

        observer = Observer()
        observer.schedule(RebuildHandler(self), str(full_md_path), recursive=True)
        observer.daemon = True
        observer.start()

    def build(self) -> None:
        """Orchestrates the full site build process."""
        md_dir = Path(self.config['md_dir'])
        if not md_dir.exists():
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
        """Cleans the contents of the public output directory without deleting the root."""
        public_dir = Path(self.config['public_dir'])
        public_dir.mkdir(parents=True, exist_ok=True)
        for item in public_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def _process_all_posts(self) -> List[Tuple[PostModel, str]]:
        """Finds and renders all Markdown posts."""
        md_dir = Path(self.config['md_dir'])
        post_filename = self.config['post_filename']
        public_dir = Path(self.config['public_dir'])
        
        posts_data: List[Tuple[PostModel, str]] = []

        for md_path in md_dir.rglob(post_filename):
            try:
                post = PostModel(str(md_path))
                post_dir = md_path.parent
                
                # Calculate output paths
                rel_post_dir = post_dir.relative_to(md_dir)
                target_dir = public_dir / 'posts' / rel_post_dir
                target_html_path = target_dir / 'index.html'
                
                # Render and Save
                target_dir.mkdir(parents=True, exist_ok=True)
                target_html_path.write_text(self.view.render_post(post), encoding='utf-8')
                
                self._copy_post_assets(post_dir, target_dir)
                
                url = target_html_path.relative_to(public_dir).as_posix()
                posts_data.append((post, url))
                print(f"  ✅ Post: {post.title}")

            except Exception as e:
                print(f"  ❌ Error processing {md_path}: {e}")
        
        return posts_data

    def _generate_metadata_pages(self, posts_data: List[Tuple[PostModel, str]]) -> None:
        """Generates the index, RSS feed, and 404 pages."""
        public_dir = Path(self.config['public_dir'])

        # RSS
        rss_items = []
        for post, url in posts_data:
            slug = url
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
        (public_dir / 'index.html').write_text(index_html, encoding='utf-8')
        print("  ✅ Index")

        # 404
        (public_dir / '404.html').write_text(self.view.render_404(), encoding='utf-8')
        print("  ✅ 404 Page")

    def new_article(self, slug: str) -> None:
        """Creates a new post template and opens it in the default editor."""
        md_dir = Path(self.config['md_dir'])
        post_filename = self.config['post_filename']
        assets_dir = self.config['assets_dir']

        target_dir = md_dir / slug
        if target_dir.exists():
            print(f"🛑 Error: Article directory already exists: '{target_dir}'")
            return

        (target_dir / assets_dir).mkdir(parents=True, exist_ok=True)
        target_md_path = target_dir / post_filename
        
        post_title = slug.replace('-', ' ').title()
        content = Templates.NEW_ARTICLE.format(
            title=post_title,
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            slug=slug,
            assets_dir=assets_dir
        )
        
        target_md_path.write_text(content, encoding='utf-8')

        print(f"\n🎉 Successfully created new article structure at: '{target_dir}'")
        self._open_in_editor(str(target_md_path))
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
        public_dir = Path(self.config['public_dir'])
        assets = ['code_highlight.css', 'style.css']
        
        # Determine application base (works for source and pyinstaller bundles)
        app_base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.resolve()))

        for filename in assets:
            # Prefer local override in CWD, fall back to app bundle
            src = Path(filename) if Path(filename).exists() else app_base / filename
            
            if src.exists():
                shutil.copy2(src, public_dir / filename)
            else:
                print(f"  ⚠️ Warning: External asset '{filename}' not found.")

    def _copy_post_assets(self, source_dir: Path, target_dir: Path) -> None:
        """Copies all files from a post directory (except the Markdown file) to target."""
        post_filename = self.config['post_filename']
        for item in source_dir.iterdir():
            if item.name == post_filename:
                continue
            
            dst = target_dir / item.name
            
            if item.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)
