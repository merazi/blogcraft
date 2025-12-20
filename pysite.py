import os
import shutil
import markdown
import glob
import argparse
import datetime
import subprocess # NEW: For launching the text editor

# --- Configuration ---
MD_DIR = 'md'
PUBLIC_DIR = 'public'
SITE_TITLE = "My Awesome Static Site"
POST_FILENAME = 'article.md'
ASSETS_DIR = 'media'

# --- HTML Templates (Omitted for brevity, assumed to be the same) ---
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

POST_CONTENT_TEMPLATE = """
<article>
    <header>
        <h2>{post_title}</h2>
    </header>
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

# --- Article Template (Unchanged) ---
NEW_ARTICLE_TEMPLATE = """
# {title}

**Date:** {date}

This is the content for your new article, '{slug}'.

Start writing your awesome content here! You can include assets in the accompanying `{assets_dir}` folder.

## Sub-heading Example

* List item 1
* List item 2
"""

# --- Site Generation Functions (Unchanged) ---

def clean_public_directory():
    # ... (function body is the same)
    print(f"Cleaning existing '{PUBLIC_DIR}' directory...")
    if os.path.exists(PUBLIC_DIR):
        shutil.rmtree(PUBLIC_DIR)
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    print("Done cleaning.")

def generate_post_page(md_path, html_target_path):
    # ... (function body is the same)
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = markdown.markdown(md_content)

        import re
        match = re.search(r'<h1>(.*?)<\/h1>|<h2>(.*?)<\/h2>', html_content, re.IGNORECASE)
        default_title = os.path.basename(os.path.dirname(md_path)).replace('-', ' ').title()
        post_title = (match.group(1) or match.group(2)) if match else default_title

        final_content = POST_CONTENT_TEMPLATE.format(
            post_title=post_title,
            html_content=html_content
        )

        full_html = BASE_TEMPLATE.format(
            title=f"{post_title} | {SITE_TITLE}",
            site_title=SITE_TITLE,
            content=final_content,
            year=datetime.datetime.now().year
        )

        os.makedirs(os.path.dirname(html_target_path), exist_ok=True)
        with open(html_target_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        print(f"  ✅ Generated post: {os.path.relpath(html_target_path, PUBLIC_DIR)}")
        return post_title, os.path.relpath(html_target_path, PUBLIC_DIR)

    except Exception as e:
        print(f"  ❌ Error processing {md_path}: {e}")
        return None, None

def copy_assets(source_dir, target_dir):
    # ... (function body is the same)
    for item in os.listdir(source_dir):
        s = os.path.join(source_dir, item)
        d = os.path.join(target_dir, item)

        if item == POST_FILENAME:
            continue

        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
            print(f"  ➡️ Copied assets folder: {os.path.basename(s)}")
        elif os.path.isfile(s):
            shutil.copy2(s, d)
            print(f"  ➡️ Copied file: {item}")

def generate_index_page(post_links):
    # ... (function body is the same)
    print("\nGenerating index.html...")
    list_items = ""
    for title, url in post_links:
        list_items += f'<li><a href="/{url}">{title}</a></li>\n'

    final_content = INDEX_CONTENT_TEMPLATE.format(post_list=list_items)

    full_html = BASE_TEMPLATE.format(
        title=f"Home | {SITE_TITLE}",
        site_title=SITE_TITLE,
        content=final_content,
        year=datetime.datetime.now().year
    )

    index_path = os.path.join(PUBLIC_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"  ✅ Generated: {index_path}")

def generate_404_page():
    # ... (function body is the same)
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

    full_html = BASE_TEMPLATE.format(
        title=f"404 | {SITE_TITLE}",
        site_title=SITE_TITLE,
        content=final_content,
        year=datetime.datetime.now().year
    )

    not_found_path = os.path.join(PUBLIC_DIR, '404.html')
    with open(not_found_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"  ✅ Generated: {not_found_path}")

def generate_site():
    # ... (function body is the same)
    if not os.path.exists(MD_DIR):
        print(f"🛑 Error: Source directory '{MD_DIR}' not found. Please create it and add your content.")
        return

    clean_public_directory()

    all_post_links = []

    print(f"\n--- Processing '{MD_DIR}' contents ---")

    for md_article_path in glob.glob(os.path.join(MD_DIR, '**', POST_FILENAME), recursive=True):

        post_dir = os.path.dirname(md_article_path)
        rel_post_dir = os.path.relpath(post_dir, MD_DIR)
        target_html_path = os.path.join(PUBLIC_DIR, rel_post_dir, 'index.html')

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
    print("You can open 'public/index.html' in your browser to view it.")

# --- Updated Feature Function ---

def create_article(slug):
    """
    Creates the folder structure and article.md template for a new article,
    then opens the file in the user's defined text editor.
    """
    target_dir = os.path.join(MD_DIR, slug)
    target_md_path = os.path.join(target_dir, POST_FILENAME)
    target_media_dir = os.path.join(target_dir, ASSETS_DIR)

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
        assets_dir=ASSETS_DIR
    )
    with open(target_md_path, 'w', encoding='utf-8') as f:
        f.write(template_content)

    print(f"\n🎉 Successfully created new article structure at: '{target_dir}'")

    # 3. Determine the editor command
    # Use the EDITOR env var, defaulting to 'vim' if not set
    editor_command = os.environ.get('EDITOR', 'vim')

    print(f"🖋️ Opening article in your editor ({editor_command}). Save and close the file to return to the prompt...")

    # 4. Launch the editor and wait for it to close
    try:
        # subprocess.call blocks the script until the process (editor) returns
        subprocess.call([editor_command, target_md_path])

        print("\n✅ Editor closed. Your content is saved!")

    except FileNotFoundError:
        print(f"\n🛑 Error: Editor command '{editor_command}' not found.")
        print("Please ensure the command is in your system's PATH or set the EDITOR environment variable correctly.")

    print("\nNext step: Run 'python pysite.py build' to generate the site with your new article.")


# --- CLI Setup (Unchanged) ---

def cli():
    """
    Sets up the command-line interface for the pysite script.
    """
    parser = argparse.ArgumentParser(
        description="pysite: A simple Python static site generator.",
        epilog="Use 'python pysite.py build' to generate the site, or 'python pysite.py new <slug>' to create a new article."
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # 'build' command
    build_parser = subparsers.add_parser('build', help='Generates the static site from the "md" directory into the "public" directory.')
    build_parser.set_defaults(func=generate_site)

    # 'new' command
    new_parser = subparsers.add_parser('new', help='Creates the folder structure and article template for a new article.')
    new_parser.add_argument('slug', type=str, help='The URL-friendly slug (e.g., "my-first-post"). This will be the folder name.')
    # The lambda function is updated to use the modified create_article signature
    new_parser.set_defaults(func=lambda args: create_article(args.slug))

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args) if args.command == 'new' else args.func()
    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
