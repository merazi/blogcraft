import os
import shutil
import markdown
import glob
import argparse
import datetime
import subprocess 
import json 

# --- Configuration Holder ---
CONFIG = {}

# --- JSON Configuration Loader ---

def load_config(config_file='config.json'):
    """Loads configuration settings from a JSON file."""
    global CONFIG
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            CONFIG.update(json.load(f))
        
        print(f"Loaded configuration from {config_file}.")

    except FileNotFoundError:
        print(f"🛑 Error: Configuration file '{config_file}' not found.")
        print("Please create a 'config.json' file in the project root.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"🛑 Error: Invalid JSON format in '{config_file}'. Details: {e}")
        exit(1)
    
# --- HTML Templates ---

BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
</head>
<body>
    <main class="container">
        <header>
            <hgroup>
                <h1><a href="/" style="text-decoration: none; color: inherit;">{site_title}</a></h1>
                <p>Generated with Python</p>
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

# MODIFIED: Removed the <header> and <h2>{post_title}</h2> to prevent title duplication
POST_CONTENT_TEMPLATE = """
<article>
    {html_content}
    <a href="/" role="button" class="secondary">Back to Home</a>
</article>
"""

INDEX_CONTENT_TEMPLATE = """
<h2>Latest Posts</h2>
<ul role="list">
{post_list}
</ul>
"""

NEW_ARTICLE_TEMPLATE = """
# {title}

**Date:** {date}

This is the content for your new article, '{slug}'. 

Start writing your awesome content here! You can include assets in the accompanying `{assets_dir}` folder.

## Sub-heading Example

* List item 1
* List item 2
"""

# --- Site Generation Functions ---

def generate_social_nav_html():
    """Generates the HTML list items for social links, if configured, for the navigation bar."""
    social_nav_links = ""
    
    if 'socials' in CONFIG and isinstance(CONFIG['socials'], dict):
        socials_config = CONFIG['socials']
        
        # We only print the info message once
        if CONFIG.get('_social_printed', False) is False:
            print("  ℹ️ Adding social media links to navigation.")
            CONFIG['_social_printed'] = True
            
        for social_name, social_url in socials_config.items():
            # Use the exact key name for the display text
            display_name = social_name 
            # Generate the list item link with target="_blank"
            social_nav_links += f'<li><a href="{social_url}" target="_blank">{display_name}</a></li>\n'
            
    return social_nav_links


def clean_public_directory():
    """Removes the public directory and recreates it."""
    public_dir = CONFIG['public_dir']
    print(f"Cleaning existing '{public_dir}' directory...")
    if os.path.exists(public_dir):
        shutil.rmtree(public_dir)
    os.makedirs(public_dir, exist_ok=True)
    print("Done cleaning.")

def generate_post_page(md_path, html_target_path):
    """
    Converts a single article.md file to HTML and writes the full page.
    """
    post_filename = CONFIG['post_filename']
    site_title = CONFIG['site_title']

    try:
        # 1. Read Markdown content
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 2. Convert Markdown to HTML
        html_content = markdown.markdown(md_content)
        
        import re
        match = re.search(r'<h1>(.*?)<\/h1>|<h2>(.*?)<\/h2>', html_content, re.IGNORECASE)
        # Fallback title if no H1/H2 found
        default_title = os.path.basename(os.path.dirname(md_path)).replace('-', ' ').title()
        post_title = (match.group(1) or match.group(2)) if match else default_title

        # 3. Apply post content template
        # NOTE: We only pass html_content. post_title is now implicit in html_content (from Markdown H1)
        final_content = POST_CONTENT_TEMPLATE.format(
            html_content=html_content
        )

        # 4. Apply base template
        social_nav_html = generate_social_nav_html() 
        
        full_html = BASE_TEMPLATE.format(
            title=f"{post_title} | {site_title}",
            site_title=site_title,
            content=final_content,
            year=datetime.datetime.now().year,
            social_nav_links=social_nav_html # Pass to the base template
        )

        # 5. Write to target file
        os.makedirs(os.path.dirname(html_target_path), exist_ok=True)
        with open(html_target_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
            
        print(f"  ✅ Generated post: {os.path.relpath(html_target_path, CONFIG['public_dir'])}")
        return post_title, os.path.relpath(html_target_path, CONFIG['public_dir'])

    except Exception as e:
        print(f"  ❌ Error processing {md_path}: {e}")
        return None, None

def copy_assets(source_dir, target_dir):
    """
    Copies all content of the source_dir *except* the markdown file.
    """
    post_filename = CONFIG['post_filename']
    assets_dir = CONFIG['assets_dir']
    
    for item in os.listdir(source_dir):
        s = os.path.join(source_dir, item)
        d = os.path.join(target_dir, item)
        
        if item == post_filename:
            continue
            
        if os.path.isdir(s):
            # For a directory like 'media', copy its entire tree
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
            print(f"  ➡️ Copied assets folder: {os.path.basename(s)}")
        elif os.path.isfile(s):
            shutil.copy2(s, d)
            print(f"  ➡️ Copied file: {item}")

def generate_index_page(post_links):
    """
    Creates the index.html page with a list of links to all posts.
    """
    site_title = CONFIG['site_title']
    public_dir = CONFIG['public_dir']

    print("\nGenerating index.html...")
    list_items = ""
    for title, url in post_links:
        list_items += f'<li><a href="/{url}">{title}</a></li>\n'

    # The content template no longer includes social links
    final_content = INDEX_CONTENT_TEMPLATE.format(post_list=list_items)

    # Get the social links for the navigation
    social_nav_html = generate_social_nav_html()

    full_html = BASE_TEMPLATE.format(
        title=f"Home | {site_title}",
        site_title=site_title,
        content=final_content,
        year=datetime.datetime.now().year,
        social_nav_links=social_nav_html
    )

    index_path = os.path.join(public_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"  ✅ Generated: {index_path}")

def generate_404_page():
    """
    Creates a simple 404.html page.
    """
    site_title = CONFIG['site_title']
    public_dir = CONFIG['public_dir']

    print("Generating 404.html...")
    final_content = """
    <article>
        <header>
            <h2>404 - Page Not Found</h2>
        </header>
        <p>Oops! The page you are looking for does not exist.</p>
        <a href="/" role="button">Go to Home</a>
    </article>
    """
    
    # Get the social links for the navigation
    social_nav_html = generate_social_nav_html()
    
    full_html = BASE_TEMPLATE.format(
        title=f"404 | {site_title}",
        site_title=site_title,
        content=final_content,
        year=datetime.datetime.now().year,
        social_nav_links=social_nav_html
    )

    not_found_path = os.path.join(public_dir, '404.html')
    with open(not_found_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"  ✅ Generated: {not_found_path}")

def generate_site():
    """Main function to orchestrate the site generation."""
    md_dir = CONFIG['md_dir']
    public_dir = CONFIG['public_dir']
    post_filename = CONFIG['post_filename']
    
    # Initialize a flag to ensure the "social links added" message prints only once
    CONFIG['_social_printed'] = False

    if not os.path.exists(md_dir):
        print(f"🛑 Error: Source directory '{md_dir}' not found. Please create it and add your content.")
        return

    clean_public_directory()

    all_post_links = []

    print(f"\n--- Processing '{md_dir}' contents ---")
    
    # We look for the POST_FILENAME in any subdirectory of MD_DIR
    for md_article_path in glob.glob(os.path.join(md_dir, '**', post_filename), recursive=True):
        
        post_dir = os.path.dirname(md_article_path)
        rel_post_dir = os.path.relpath(post_dir, md_dir)
        target_html_path = os.path.join(public_dir, rel_post_dir, 'index.html')
        
        print(f"\nProcessing post in: {post_dir}")
        
        post_title, post_url = generate_post_page(md_article_path, target_html_path)
        
        if post_title and post_url:
            all_post_links.append((post_title, post_url))
            
            target_post_dir = os.path.dirname(target_html_path)
            copy_assets(post_dir, target_post_dir)
            
    all_post_links.reverse()
    
    generate_index_page(all_post_links)
    generate_404_page()

    print("\n✨ Site generation complete! Your static site is in the 'public' folder.")
    print(f"You can open '{public_dir}/index.html' in your browser to view it.")

# --- Article Creation Function (Updated to use CONFIG) ---

def create_article(slug):
    """
    Creates the folder structure and article.md template for a new article,
    then opens the file in the user's defined text editor.
    """
    md_dir = CONFIG['md_dir']
    post_filename = CONFIG['post_filename']
    assets_dir = CONFIG['assets_dir']

    target_dir = os.path.join(md_dir, slug)
    target_md_path = os.path.join(target_dir, post_filename)
    target_media_dir = os.path.join(target_dir, assets_dir)
    
    # 1. Check if the directory already exists
    if os.path.exists(target_dir):
        print(f"🛑 Error: Article directory already exists: '{target_dir}'")
        return

    # 2. Create the directories and template file (as before)
    os.makedirs(target_dir)
    os.makedirs(target_media_dir)
    post_title = slug.replace('-', ' ').title()
    template_content = NEW_ARTICLE_TEMPLATE.format(
        title=post_title,
        date=datetime.date.today().isoformat(),
        slug=slug,
        assets_dir=assets_dir
    )
    with open(target_md_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
        
    print(f"\n🎉 Successfully created new article structure at: '{target_dir}'")
    
    # 3. Determine the editor command
    # Use the EDITOR env var, falling back to config value
    editor_command = os.environ.get('EDITOR', CONFIG.get('default_editor', 'nano'))
    
    print(f"🖋️ Opening article in your editor ({editor_command}). Save and close the file to return to the prompt...")

    # 4. Launch the editor and wait for it to close
    try:
        subprocess.call([editor_command, target_md_path])
        
        print("\n✅ Editor closed. Your content is saved!")

    except FileNotFoundError:
        print(f"\n🛑 Error: Editor command '{editor_command}' not found.")
        print("Please ensure the command is in your system's PATH or set the EDITOR environment variable/config file correctly.")
        
    print("\nNext step: Run 'python pysite.py build' to generate the site with your new article.")


# --- CLI Setup ---

def cli():
    """
    Sets up the command-line interface for the pysite script.
    """
    # Load configuration FIRST
    load_config() 
    
    parser = argparse.ArgumentParser(
        description="pysite: A simple Python static site generator.",
        epilog="Use 'python pysite.py build' to generate the site, or 'python pysite.py new <slug>' to create a new article."
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # 'build' command
    build_parser = subparsers.add_parser('build', help='Generates the static site from the content directory into the public directory.')
    build_parser.set_defaults(func=generate_site)
    
    # 'new' command
    new_parser = subparsers.add_parser('new', help='Creates the folder structure and article template for a new article.')
    new_parser.add_argument('slug', type=str, help='The URL-friendly slug (e.g., "my-first-post"). This will be the folder name.')
    new_parser.set_defaults(func=lambda args: create_article(args.slug))

    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args) if args.command == 'new' else args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()