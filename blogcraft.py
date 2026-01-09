import os
import shutil
import markdown
import glob
import argparse
import datetime
import subprocess 
import json 
import re 
# --- Templates ---

class Templates:
    BASE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="/code_highlight.css" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
</head>
<body>
    <main class="container">
        <header>
            <hgroup>
                <h1><a href="/" style="text-decoration: none; color: inherit;">{site_title}</a></h1>
                <p>{site_subtitle}</p>
            </hgroup>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li style="padding: 0 0.5rem; color: var(--pico-muted-color); border: none;" aria-hidden="true">|</li>
                    {social_nav_links} 
                </ul>
            </nav>
        </header>
        {content}
        <footer>
            <small>&copy; {year} {site_title}</small>
        </footer>
    </main>
</body>
</html>
"""

    POST_CONTENT = """
<article>
    {html_content}
    <a href="/" role="button" class="secondary">Back to Home</a>
</article>
"""

    INDEX_CONTENT = """
<h2>Latest Posts</h2>
<ul role="list">
{post_list}
</ul>
"""

    NEW_ARTICLE = """---
title: {title}
date: {date}
---

This is the content for your new article, '{slug}'. 

Start writing your awesome content here! You can include assets in the accompanying `{assets_dir}` folder.

## Sub-heading Example

* List item 1
* List item 2
"""

# --- MVC Classes ---

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
            exit(1)
        except json.JSONDecodeError as e:
            print(f"🛑 Error: Invalid JSON format in '{config_file}'. Details: {e}")
            exit(1)

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

class BlogView:
    """Handles HTML generation (View)."""
    def __init__(self, config):
        self.config = config
        self._social_printed = False

    def _generate_social_nav(self):
        social_nav_links = ""
        socials = self.config.get('socials')
        if socials and isinstance(socials, dict):
            if not self._social_printed:
                print("  ℹ️ Adding social media links to navigation.")
                self._social_printed = True
            for name, url in socials.items():
                social_nav_links += f'<li><a href="{url}" target="_blank">{name}</a></li>\n'
        return social_nav_links

    def _wrap_base(self, title, content):
        return Templates.BASE.format(
            title=title,
            site_title=self.config['site_title'],
            site_subtitle=self.config.get('site_subtitle', 'Generated with Python'),
            content=content,
            year=datetime.datetime.now().year,
            social_nav_links=self._generate_social_nav()
        )

    def render_post(self, post):
        content = Templates.POST_CONTENT.format(html_content=post.html_content)
        title = f"{post.title} | {self.config['site_title']}"
        return self._wrap_base(title, content)

    def render_index(self, posts):
        list_items = ""
        for post, url in posts:
            list_items += (
                f'<li>'
                f'<a href="/{url}">{post.title}</a> '
                f'<span style="color: var(--pico-muted-color); font-size: 0.9em; margin-left: 0.5rem;">'
                f'({post.date_str})'
                f'</span>'
                f'</li>\n'
            )
        content = Templates.INDEX_CONTENT.format(post_list=list_items)
        title = f"Home | {self.config['site_title']}"
        return self._wrap_base(title, content)

    def render_404(self):
        content = """
    <article>
        <header>
            <h2>404 - Page Not Found</h2>
        </header>
        <p>Oops! The page you are looking for does not exist.</p>
        <a href="/" role="button">Go to Home</a>
    </article>
    """
        title = f"404 | {self.config['site_title']}"
        return self._wrap_base(title, content)

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

        self._clean_public()
        self._copy_external_assets()

        posts_data = [] # List of (PostModel, url)

        print(f"\n--- Processing '{md_dir}' contents ---")
        search_path = os.path.join(md_dir, '**', post_filename)
        
        for md_path in glob.glob(search_path, recursive=True):
            post_dir = os.path.dirname(md_path)
            print(f"\nProcessing post in: {post_dir}")

            try:
                post = PostModel(md_path)
                
                # Determine output path
                rel_post_dir = os.path.relpath(post_dir, md_dir)
                target_html_path = os.path.join(public_dir, rel_post_dir, 'index.html')
                
                # Render
                html = self.view.render_post(post)
                
                # Write
                os.makedirs(os.path.dirname(target_html_path), exist_ok=True)
                with open(target_html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                print(f"  ✅ Generated post: {os.path.relpath(target_html_path, public_dir)}")
                
                # Copy assets
                self._copy_post_assets(post_dir, os.path.dirname(target_html_path))
                
                # Add to index list
                url = os.path.relpath(target_html_path, public_dir)
                posts_data.append((post, url))

            except Exception as e:
                print(f"  ❌ Error processing {md_path}: {e}")

        # Generate Index
        print("\nGenerating index.html...")
        posts_data.sort(key=lambda x: x[0].date_obj, reverse=True)
        index_html = self.view.render_index(posts_data)
        with open(os.path.join(public_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print(f"  ✅ Generated: {os.path.join(public_dir, 'index.html')}")

        # Generate 404
        print("Generating 404.html...")
        not_found_html = self.view.render_404()
        with open(os.path.join(public_dir, '404.html'), 'w', encoding='utf-8') as f:
            f.write(not_found_html)
        print(f"  ✅ Generated: {os.path.join(public_dir, '404.html')}")

        print("\n✨ Site generation complete! Your static site is in the 'public' folder.")
        print(f"You can open '{public_dir}/index.html' in your browser to view it.")

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
            date=datetime.date.today().isoformat(),
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
        print(f"Cleaning existing '{public_dir}' directory...")
        if os.path.exists(public_dir):
            shutil.rmtree(public_dir)
        os.makedirs(public_dir, exist_ok=True)
        print("Done cleaning.")

    def _copy_external_assets(self):
        public_dir = self.config['public_dir']
        files_to_copy = ['code_highlight.css']
        print("\n--- Copying External Assets ---")
        for filename in files_to_copy:
            source_path = os.path.join(os.getcwd(), filename)
            target_path = os.path.join(public_dir, filename)
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                print(f"  ➡️ Copied global asset: {filename}")
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
                print(f"  ➡️ Copied assets folder: {os.path.basename(s)}")
            elif os.path.isfile(s):
                shutil.copy2(s, d)
                print(f"  ➡️ Copied file: {item}")

# --- CLI Setup ---

def cli():
    """Sets up the command-line interface."""
    parser = argparse.ArgumentParser(
        description="blogcraft: A simple Python static site generator.",
        epilog="Use 'python blogcraft.py build' to generate the site, or 'python blogcraft.py new <slug>' to create a new article."
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    build_parser = subparsers.add_parser('build', help='Generates the static site from the content directory into the public directory.')
    
    new_parser = subparsers.add_parser('new', help='Creates the folder structure and article template for a new article.')
    new_parser.add_argument('slug', type=str, help='The URL-friendly slug (e.g., "my-first-post"). This will be the folder name.')

    args = parser.parse_args()
    
    controller = BlogController()

    if args.command == 'build':
        controller.build()
    elif args.command == 'new':
        controller.new_article(args.slug)


if __name__ == "__main__":
    cli()
