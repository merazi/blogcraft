import argparse

from controllers import BlogController

def cli():
    """Sets up the command-line interface."""
    parser = argparse.ArgumentParser(
        description="blogcraft: A simple Python static site generator.",
        epilog="Use 'python blogcraft.py build' to generate the site, "
               "or 'python blogcraft.py new <slug>' to create a new article."
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser(
        'build',
        help='Generates the static site from the content directory into the public directory.'
    )

    new_parser = subparsers.add_parser(
        'new',
        help='Creates the folder structure and article template for a new article.'
    )
    new_parser.add_argument(
        'slug',
        type=str,
        help='The URL-friendly slug (e.g., "my-first-post"). This will be the folder name.'
    )

    args = parser.parse_args()

    controller = BlogController()

    if args.command == 'build':
        controller.build()
    elif args.command == 'new':
        controller.new_article(args.slug)


if __name__ == "__main__":
    cli()
