# blogcraft: A Simple Python Static Site Generator

**blogcraft** is a minimal, command-line utility built in Python to convert structured Markdown files into a clean, static HTML website. It includes features for content creation, site generation, and uses the Pico CSS framework for minimal, accessible styling out-of-the-box.

## ✨ Features

* **Configuration File:** Uses `config.json` for easy customization of site title, directory names, and default editor.
* **Markdown to HTML Conversion:** Converts `article.md` files into `index.html` pages.
* **Structured Content:** Respects the directory structure inside the configured content folder (default: `md/`).
* **Asset Handling:** Automatically copies asset directories (images, videos, etc.) to the output structure.
* **Single-File Command:** Includes a `new` command for fast article creation.
* **Editor Integration:** Launches the new article directly in your preferred editor (`$EDITOR` or configured fallback).
* **Minimal Styling:** Uses [Pico CSS](https://picocss.com/) via CDN for a modern, responsive, and classless design.
* **Utility Pages:** Generates `index.html` and `404.html`.
* **Metadata via Frontmatter:** Extracts titles (respecting casing) and dates from a required YAML frontmatter block.

## ⚙️ Configuration (`config.json`)

All key settings for **blogcraft** are managed in the `config.json` file. You can change these values to customize your project structure and default tools.

| Key | Description | Default Value |
| :--- | :--- | :--- |
| `site_title` | The main title used in the header and page titles. | `"My Awesome Static Site"` |
| `md_dir` | The source directory where your Markdown files are stored. | `"md"` |
| `public_dir` | The destination directory for the generated static website. | `"public"` |
| `post_filename`| The required filename for each article's main content. | `"article.md"` |
| `assets_dir` | The name of the subdirectory within each post folder used for media/assets. | `"media"` |
| `default_editor` | The fallback text editor command if the `$EDITOR` environment variable is not set. | `"vim"` |

**Example `config.json`:**

```json
{
    "site_title": "Merazi's blog",
    "md_dir": "md",
    "public_dir": "public",
    "post_filename": "index.md",
    "assets_dir": "files",
    "default_editor": "vim",
    "socials": {
        "GitHub": "https://github.com/merazi",
        "BlueSky": "https://bsky.app/profile/meraz1.bsky.social"
    }
}

```

## ✍️ Creating and Managing Content

Content is organized into subdirectories within the configured md_dir (default: md/). Each subdirectory represents a single post.
Article Structure and Frontmatter

Every article file must start with a YAML-like frontmatter block enclosed by ---. This block is used to set the metadata for the post, including the display title and date.

Required Frontmatter Keys:

- title: The exact title used for the index page hyperlink and the browser tab title.
- date: The date of the post, displayed on the index page (format YYYY-MM-DD).

Example article.md:

```markdown
---
title: My First Article with Custom Title Casing
date: 2025-12-20
---

# Optional: Main On-Page Heading (This is still good for SEO)

This is the rest of the content for your article. Because the title is set in the frontmatter, you can control the text of the main heading independently, or omit it entirely if your Markdown already starts with a list or paragraph.

## Sub-heading
```

## 💻 Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `build` | Generates the static site from all Markdown content into the `public` directory. | `python blogcraft.py build` |
| `new <slug>`| Creates a new content directory and a template `article.md` file (including frontmatter). | `python blogcraft.py new project-launch` |
