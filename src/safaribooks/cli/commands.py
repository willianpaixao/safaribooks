"""
Click-based CLI commands for SafariBooks.

This module provides a modern, user-friendly CLI using Click with:
- Better help messages and documentation
- Input validation and error handling
- Progress bars and visual feedback (via Rich)
- Subcommands for different operations
"""

import sys
from pathlib import Path
from types import ModuleType

import click
from rich.console import Console

from logger import get_logger, get_valid_log_levels, setup_logger


# Initialize Rich console for pretty output
console = Console()


# Custom Click types
class BookIDType(click.ParamType):
    """Custom Click type for validating Book IDs."""

    name = "book_id"

    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> str:
        """Validate that the book ID is a valid format."""
        # Book IDs are typically 13-digit ISBNs
        if not value.isdigit():
            self.fail(f"{value!r} is not a valid book ID (must be digits only)", param, ctx)
        if len(value) != 13:
            # Warn but don't fail - some books may have different ID lengths
            console.print(
                f"[yellow]Warning:[/yellow] Book ID {value} is not 13 digits. "
                f"This may or may not work.",
                style="yellow",
            )
        return value


BOOK_ID = BookIDType()


def get_safaribooks_module() -> ModuleType:
    """
    Dynamically import the SafariBooks class.

    This avoids circular imports and allows the CLI to be used independently.
    """
    # Add parent directory to path to import safaribooks.py
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Import safaribooks.py as a module
    # pylint: disable=import-outside-toplevel
    import importlib.util  # noqa: PLC0415

    safaribooks_path = project_root / "safaribooks.py"
    spec = importlib.util.spec_from_file_location("safaribooks", safaribooks_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load safaribooks.py from {safaribooks_path}")

    safaribooks = importlib.util.module_from_spec(spec)
    sys.modules["safaribooks"] = safaribooks
    spec.loader.exec_module(safaribooks)

    return safaribooks


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    SafariBooks - Download and generate EPUB files from O'Reilly Learning.

    SafariBooks allows you to download books from O'Reilly's Safari Books Online
    (now O'Reilly Learning) platform and convert them to EPUB format for offline reading.

    \b
    Authentication:
    - Requires a valid cookies.json file from an authenticated browser session
    - See: https://github.com/willianpaixao/safaribooks for instructions

    \b
    Examples:
      # Download a single book
      safaribooks download --book-id 9781492052197

      # Download multiple books
      safaribooks download --book-id 9781492052197 9781491958698

      # Download with Kindle formatting
      safaribooks download --book-id 9781492052197 --kindle

      # Enable debug logging
      safaribooks download --book-id 9781492052197 --log-level DEBUG
    """
    # If no subcommand is given, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        ctx.exit()


@cli.command()
@click.option(
    "--book-id",
    "-b",
    "book_ids",
    type=BOOK_ID,
    multiple=True,
    required=True,
    help="Book ID(s) to download. Can be specified multiple times for multiple books. "
    "Find the ID in the URL: https://learning.oreilly.com/library/view/book-name/XXXXXXXXXXXXX/",
)
@click.option(
    "--kindle",
    is_flag=True,
    default=False,
    help="Add CSS rules optimized for Kindle e-readers (prevents overflow on tables/code blocks).",
)
@click.option(
    "--log-level",
    type=click.Choice(get_valid_log_levels(), case_sensitive=False),
    default="INFO",
    show_default=True,
    help="Set the logging level for detailed output.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("Books"),
    show_default=True,
    help="Directory to save downloaded books.",
)
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to a log file. When provided, logging output is written to this file "
    "(created if it doesn't exist). When omitted, logging is disabled.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Suppress all output except errors. Useful for scripting and automation.",
)
def download(
    book_ids: tuple[str, ...],
    kindle: bool,
    log_level: str,
    output_dir: Path,
    log_file: Path | None,
    quiet: bool,
) -> None:
    """
    Download books from O'Reilly Learning and generate EPUB files.

    This command downloads the specified book(s) from O'Reilly Learning,
    including all chapters, images, and styles, and generates a valid EPUB file.

    \b
    Requirements:
    - A valid cookies.json file from an authenticated browser session
    - Sufficient disk space for downloaded content

    \b
    Examples:
      # Download a single book
      safaribooks download --book-id 9781492052197

      # Download multiple books
      safaribooks download -b 9781492052197 -b 9781491958698

      # Download with Kindle optimization
      safaribooks download --book-id 9781492052197 --kindle

      # Save to custom directory
      safaribooks download --book-id 9781492052197 --output-dir ~/Documents/Books
    """
    # Set up logging: file-based if --log-file is given, otherwise disabled (NullHandler)
    setup_logger("SafariBooks", log_level, log_file=str(log_file) if log_file else None)
    logger = get_logger("SafariBooks.CLI")

    # Check for cookies.json
    cookies_file = Path("cookies.json")
    if not cookies_file.exists():
        console.print(
            "[bold red]Error:[/bold red] cookies.json file not found!\n\n"
            "SafariBooks requires a cookies.json file to authenticate with O'Reilly Learning.\n"
            "Please follow the instructions at:\n"
            "  https://github.com/willianpaixao/safaribooks#authentication\n",
            style="red",
        )
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Import SafariBooks module
    safaribooks = get_safaribooks_module()

    # Create a namespace object compatible with the old argparse interface
    # This allows us to use the existing SafariBooks class without modification
    import argparse  # noqa: PLC0415

    # Process each book
    epub_paths: list[Path] = []
    for idx, book_id in enumerate(book_ids, start=1):
        if not quiet:
            logger.debug(f"Processing book {idx}/{len(book_ids)}: {book_id}")

        # Create a separate args object for each book (the constructor expects a single book ID)
        current_args = argparse.Namespace(
            bookid=book_id,  # Single book ID (not a list)
            kindle=kindle,
            log_level=log_level,
            output_dir=str(output_dir),
            quiet=quiet,
            cred=False,
            login=False,
            no_cookies=False,
        )

        try:
            sb = safaribooks.SafariBooks(current_args)
            epub_path = Path(sb.BOOK_PATH) / f"{sb.book_id}.epub"
            epub_paths.append(epub_path)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception(f"Failed to download book {book_id}")
            console.print(
                f"[bold red]✗[/bold red] Failed to download book {book_id}: {e}",
                style="red",
            )
            continue

    if not quiet and epub_paths:
        console.print()
        from rich.markup import escape  # noqa: PLC0415

        for ep in epub_paths:
            console.print(
                f"[bold green]✓ Download complete![/bold green] [green]{escape(str(ep))}[/green]",
            )
        console.print()


@cli.command()
def version() -> None:
    """Display the version of SafariBooks."""
    # Read version from pyproject.toml or hardcode
    console.print("[bold cyan]SafariBooks[/bold cyan] version 2.0.0-alpha.1")


@cli.command()
def check_cookies() -> None:
    """
    Verify that cookies.json exists and is valid.

    This command checks if the cookies.json file exists and contains
    the required authentication cookies for O'Reilly Learning.
    """
    import json  # noqa: PLC0415

    cookies_file = Path("cookies.json")

    if not cookies_file.exists():
        console.print(
            "[bold red]✗ cookies.json not found![/bold red]\n\n"
            "Please create a cookies.json file with your O'Reilly Learning cookies.\n"
            "See: https://github.com/willianpaixao/safaribooks#authentication",
            style="red",
        )
        sys.exit(1)

    try:
        with cookies_file.open(encoding="utf-8") as f:
            cookies = json.load(f)

        if not cookies:
            console.print("[bold yellow]⚠ cookies.json is empty![/bold yellow]", style="yellow")
            sys.exit(1)

        # Check for required cookies (adjust based on actual requirements)
        # O'Reilly typically uses cookies like 'orm-jwt', 'BrowserCookie', etc.
        console.print(
            f"[bold green]✓ cookies.json found and valid![/bold green]\n"
            f"  File: {cookies_file.absolute()}\n"
            f"  Cookies: {len(cookies)} entries",
            style="green",
        )

    except json.JSONDecodeError as e:
        console.print(
            f"[bold red]✗ cookies.json is not valid JSON![/bold red]\n  Error: {e}",
            style="red",
        )
        sys.exit(1)


# Entry point for the CLI
def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
