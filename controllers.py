import datetime
import glob
import os
import shutil
import subprocess
import sys

from models import ConfigModel, PostModel
from views import BlogView, Templates


class BlogController:
    """Orchestrates the site generation (Controller)."""
    def __init__(self):
        self.config = ConfigModel()
        self.view = BlogView(self.config)

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