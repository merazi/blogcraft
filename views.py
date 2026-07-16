import datetime
import os
from typing import List, Tuple, Any
import jinja2

from models import PostModel, ConfigModel


class Templates:
    """HTML templates for the blog."""

    NEW_ARTICLE: str = """---
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
    def __init__(self, config: ConfigModel):
        self.config = config
        
        import sys
        app_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        templates_dir = self.config.get('templates_dir', 'templates')
        
        searchpath = [templates_dir] if os.path.exists(templates_dir) else []
        bundled_templates = os.path.join(app_base, 'templates')
        if os.path.exists(bundled_templates) and bundled_templates not in searchpath:
            searchpath.append(bundled_templates)
            
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath))

    def _get_template_context(self, title: str) -> dict:
        return {
            'title': title,
            'site_title': self.config['site_title'],
            'site_subtitle': self.config.get('site_subtitle', 'Generated with Python'),
            'year': datetime.datetime.now().year,
            'socials': self.config.get('socials', {})
        }

    def render_post(self, post: PostModel) -> str:
        template = self.env.get_template('post.html')
        context = self._get_template_context(f"{post.title} | {self.config['site_title']}")
        context['post'] = post
        return template.render(**context)

    def render_index(self, posts: List[Tuple[PostModel, str]]) -> str:
        template = self.env.get_template('index.html')
        context = self._get_template_context(f"Home | {self.config['site_title']}")
        context['posts'] = posts
        context['rss_enabled'] = self.config.get('rss', False)
        return template.render(**context)

    def render_404(self) -> str:
        template = self.env.get_template('404.html')
        context = self._get_template_context(f"404 | {self.config['site_title']}")
        return template.render(**context)
