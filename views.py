import datetime


class Templates:
    """HTML templates for the blog."""
    BASE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="/code_highlight.css" />
    <link rel="stylesheet" href="/style.css" />
</head>
<body>
    <main class="container">
        <header>
            <hgroup>
                <h1><a href="/" class="site-title">{site_title}</a></h1>
                <p>{site_subtitle}</p>
            </hgroup>
            <nav>
                <ul>
                    <li><a href="/">Home</a></li>
                    <li class="separator" aria-hidden="true">|</li>
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

## Code Block Example

```python
def hello():
    print("Hello, world!")
```
"""


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
            date_display = post.date_str
            if date_display:
                date_display = date_display.split(' ')[0].split('T')[0]
            list_items += (
                f'<li>'
                f'<a href="/{url}">{post.title}</a> '
                f'<span class="post-date">'
                f'({date_display})'
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