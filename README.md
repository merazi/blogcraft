# pysite: A Simple Python Static Site Generator

**pysite** is a minimal, command-line utility built in Python to convert structured Markdown files into a clean, static HTML website. It includes features for content creation, site generation, and uses the Pico CSS framework for minimal, accessible styling out-of-the-box.

## ✨ Features

* **Configuration File:** Uses `config.json` for easy customization of site title, directory names, and default editor.
* **Markdown to HTML Conversion:** Converts `article.md` files into `index.html` pages.
* **Structured Content:** Respects the directory structure inside the configured content folder (default: `md/`).
* **Asset Handling:** Automatically copies asset directories (images, videos, etc.) to the output structure.
* **Single-File Command:** Includes a `new` command for fast article creation.
* **Editor Integration:** Launches the new article directly in your preferred editor (`$EDITOR` or configured fallback).
* **Minimal Styling:** Uses [Pico CSS](https://picocss.com/) via CDN for a modern, responsive, and classless design.
* **Utility Pages:** Generates `index.html` and `404.html`.

## ⚙️ Configuration (`config.json`)

All key settings for **pysite** are managed in the `config.json` file. You can change these values to customize your project structure and default tools.

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
    "site_title": "My Personal Blog",
    "md_dir": "content",
    "public_dir": "dist",
    "post_filename": "index.md",
    "assets_dir": "files",
    "default_editor": "nano"
}