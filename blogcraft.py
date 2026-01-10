import argparse
import textwrap

from controllers import BlogController

def cli():
    """Sets up the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="blogcraft",
        description=textwrap.dedent("""\
            blogcraft - A minimal static site generator.

            Transforms Markdown files into a static HTML website with:
              - Syntax highlighting
              - RSS feed generation
              - Responsive styling
            """),
        epilog=textwrap.dedent("""\
            examples:
              $ python blogcraft.py new my-awesome-feature
              $ python blogcraft.py build

            See config.json for site configuration.
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', required=True, title="commands")

    subparsers.add_parser(
        'build',
        help='Compile the static website from Markdown content.',
        description='Generates the static site. Cleans the public directory, copies assets, and renders Markdown to HTML.'
    )

    new_parser = subparsers.add_parser(
        'new',
        help='Create a new article template.',
        description='Creates a new content directory with a template article.md file.'
    )
    new_parser.add_argument(
        'slug',
        type=str,
        help='The URL-friendly identifier for the post (e.g., "hello-world"). Used as the folder name.'
    )

    args = parser.parse_args()

    controller = BlogController()

    if args.command == 'build':
        controller.build()
    elif args.command == 'new':
        controller.new_article(args.slug)


if __name__ == "__main__":
    cli()
