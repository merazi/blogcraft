# pysite: A Simple Python Static Site Generator

**pysite** is a minimal, command-line utility built in Python to convert structured Markdown files into a clean, static HTML website. It includes features for content creation, site generation, and uses the Pico CSS framework for minimal, accessible styling out-of-the-box.

## ✨ Features

* **Markdown to HTML Conversion:** Converts `article.md` files into `index.html` pages.
* **Structured Content:** Respects the directory structure inside the `md/` folder.
* **Asset Handling:** Automatically copies `media/` directories (images, videos, etc.) to the output structure.
* **Single-File Command:** Includes a `new` command for fast article creation.
* **Editor Integration:** Launches the new article directly in your preferred editor (`$EDITOR`).
* **Minimal Styling:** Uses [Pico CSS](https://picocss.com/) via CDN for a modern, responsive, and classless design.
* **Utility Pages:** Generates `index.html` and `404.html`.

## 🚀 Setup and Installation

### Prerequisites

* Python 3.x
* The `markdown` library

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone [YOUR_REPO_URL]
    cd pysite
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 💻 Usage

The `pysite.py` script has two main commands: `new` (for creating content) and `build` (for generating the website).

### 1. Creating a New Article

Use the `new` command followed by the desired URL-friendly slug.

**Usage:**
```bash
python pysite.py new my-first-article
