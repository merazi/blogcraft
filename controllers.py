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

from models import ConfigModel, PostModel
from views import BlogView, Templates
from rss import RSSGenerator


class BlogController:
    """Orchestrates the site generation (Controller)."""
    def __init__(self):
        self.config = ConfigModel()
        self.view = BlogView(self.config)

    def init_project(self):
        """Interactive initialization of the blog project."""
        print("🚀 Welcome to Blogcraft! Let's set up your blog.\n")
        
        title = input(f"Blog Title [{self.config['site_title']}]: ").strip()
        if title: self.config['site_title'] = title
        
        subtitle = input(f"Blog Subtitle [{self.config['site_subtitle']}]: ").strip()
        if subtitle: self.config['site_subtitle'] = subtitle

        url = input(f"Site URL [{self.config['site_url']}]: ").strip()
        if url: self.config['site_url'] = url

        editor = input(f"Default Editor [{self.config['default_editor']}]: ").strip()
        if editor: self.config['default_editor'] = editor

        self.config.save()
        
        # Ensure directories exist
        os.makedirs(self.config['md_dir'], exist_ok=True)
        print(f"✅ Created source directory: {self.config['md_dir']}")
        
        print("\n✨ Setup complete! You can now create a post with 'python blogcraft.py new my-post'.")

    def serve(self, port=8000, watch=False):
        """Starts a local preview server."""
        public_dir = self.config['public_dir']
        
        if not os.path.exists(public_dir):
            print(f"⚠️  Public directory '{public_dir}' not found. Building site first...")
            self.build()

        os.chdir(public_dir)

        Handler = http.server.SimpleHTTPRequestHandler
        
        if watch:
            print(f"👀 Watch mode enabled. Monitoring '{self.config['md_dir']}' for changes...")
            # We need to go back to root to watch md_dir
            root_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
            
            def watch_loop():
                last_mtime = self._get_max_mtime(os.path.join(root_dir, self.config['md_dir']))
                while True:
                    time.sleep(1)
                    current_mtime = self._get_max_mtime(os.path.join(root_dir, self.config['md_dir']))
                    if current_mtime > last_mtime:
                        print("\n🔄 Changes detected! Rebuilding...")
                        # Run build from root
                        current_cwd = os.getcwd()
                        os.chdir(root_dir)
                        self.build()
                        os.chdir(current_cwd)
                        last_mtime = current_mtime
            
            watcher = threading.Thread(target=watch_loop, daemon=True)
            watcher.start()

        print(f"🌐 Serving blog at http://localhost:{port}")
        print("Press Ctrl+C to stop.")
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n🛑 Server stopped.")
                sys.exit(0)

    def _get_max_mtime(self, directory):
        """Helper to get the latest modification time in a directory tree."""
        max_mtime = 0
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

    def build(self):
        md_dir = self.config['md_dir']
        public_dir = self.config['public_dir']
        post_filename = self.config['post_filename']

        if not os.path.exists(md_dir):
            print(f"🛑 Error: Source directory '{md_dir}' not found.")
            return

        print("🔨 Building site...")
        self._clean_public()
        self._copy_external_assets()

        posts_data = []  # List of (PostModel, url)

        search_path = os.path.join(md_dir, '**', post_filename)

        for md_path in glob.glob(search_path, recursive=True):
            post_dir = os.path.dirname(md_path)

            try:
                post = PostModel(md_path)
                
                # Determine output path
                rel_post_dir = os.path.relpath(post_dir, md_dir)
                target_html_path = os.path.join(public_dir, 'posts', rel_post_dir, 'index.html')
                
                # Render
                html = self.view.render_post(post)
                
                # Write
                os.makedirs(os.path.dirname(target_html_path), exist_ok=True)
                with open(target_html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                print(f"  ✅ Post: {post.title}")
                
                # Copy assets
                self._copy_post_assets(post_dir, os.path.dirname(target_html_path))
                
                # Add to index list
                url = os.path.relpath(target_html_path, public_dir)
                posts_data.append((post, url))

            except Exception as e:
                print(f"  ❌ Error processing {md_path}: {e}")

        # Generate Index
        posts_data.sort(key=lambda x: x[0].date_str or "", reverse=True)

        # Generate RSS
        rss_items = []
        for post, url in posts_data:
            # Normalize path separators and remove index.html for clean URLs
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

        index_html = self.view.render_index(posts_data)
        with open(os.path.join(public_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("  ✅ Index")

        # Generate 404
        not_found_html = self.view.render_404()
        with open(os.path.join(public_dir, '404.html'), 'w', encoding='utf-8') as f:
            f.write(not_found_html)
        print("  ✅ 404 Page")

        print(f"\n✨ Site generation complete! ({len(posts_data)} posts)")
        print(f"   Output: {public_dir}/")

    def new_article(self, slug):
        md_dir = self.config['md_dir']
        post_filename = self.config['post_filename']
        assets_dir = self.config['assets_dir']

        target_dir = os.path.join(md_dir, slug)
        target_md_path = os.path.join(target_dir, post_filename)
        target_media_dir = os.path.join(target_dir, assets_dir)

        if os.path.exists(target_dir):
            print(f"🛑 Error: Article directory already exists: '{target_dir}'")
            return

        os.makedirs(target_dir)
        os.makedirs(target_media_dir)
        post_title = slug.replace('-', ' ').title()
        template_content = Templates.NEW_ARTICLE.format(
            title=post_title,
            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            slug=slug,
            assets_dir=assets_dir
        )
        with open(target_md_path, 'w', encoding='utf-8') as f:
            f.write(template_content)

        print(f"\n🎉 Successfully created new article structure at: '{target_dir}'")

        editor_command = os.environ.get('EDITOR', self.config.get('default_editor', 'nano'))
        print(f"🖋️ Opening article in your editor ({editor_command})...")

        try:
            subprocess.call([editor_command, target_md_path])
            print("\n✅ Editor closed. Your content is saved!")
        except FileNotFoundError:
            print(f"\n🛑 Error: Editor command '{editor_command}' not found.")

        print("\nNext step: Run 'python blogcraft.py build' to generate the site.")

    def _clean_public(self):
        public_dir = self.config['public_dir']
        if os.path.exists(public_dir):
            shutil.rmtree(public_dir)
        os.makedirs(public_dir, exist_ok=True)

    def _copy_external_assets(self):
        public_dir = self.config['public_dir']
        files_to_copy = ['code_highlight.css', 'style.css']
        
        # Determine the application base path (where the script/exe lives)
        if getattr(sys, 'frozen', False):
            app_base = sys._MEIPASS
        else:
            app_base = os.path.dirname(os.path.abspath(__file__))

        for filename in files_to_copy:
            # 1. Check User's CWD (Override)
            cwd_path = os.path.join(os.getcwd(), filename)
            # 2. Check App Bundle/Source (Default)
            app_path = os.path.join(app_base, filename)
            
            target_path = os.path.join(public_dir, filename)
            
            if os.path.exists(cwd_path):
                shutil.copy2(cwd_path, target_path)
            elif os.path.exists(app_path):
                shutil.copy2(app_path, target_path)
            else:
                print(f"  ⚠️ Warning: External asset '{filename}' not found.")

    def _copy_post_assets(self, source_dir, target_dir):
        post_filename = self.config['post_filename']
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(target_dir, item)
            if item == post_filename:
                continue
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            elif os.path.isfile(s):
                shutil.copy2(s, d)