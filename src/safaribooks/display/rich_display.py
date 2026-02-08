"""Rich-based display system for SafariBooks."""

import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from .constants import EMOJI_MAP, PROGRESS_COLORS


class RichDisplay:
    """
    Rich-based display system for SafariBooks.

    Provides beautiful progress bars, tables, and formatted output
    using the Rich library.
    """

    # Class-level constants for compatibility with legacy Display
    SH_DEFAULT = ""  # Rich doesn't need ANSI codes
    SH_YELLOW = ""
    SH_BG_RED = ""
    SH_BG_YELLOW = ""

    def __init__(self, book_id: str, quiet: bool = False):
        """
        Initialize RichDisplay.

        Args:
            book_id: The book ID being processed
            quiet: If True, suppress all output except errors
        """
        self.console = Console()
        self.book_id = book_id
        self.quiet = quiet
        self.progress: Progress | None = None
        self._status: Any = None
        self.task_ids: dict[str, int | None] = {
            "chapters": None,
            "css": None,
            "images": None,
        }
        self.current_task: str | None = None
        self.task_totals: dict[str, int] = {}

        # Legacy Display compatibility attributes
        self.output_dir = ""
        self.output_dir_set = False
        self.columns, _ = __import__("shutil").get_terminal_size()
        self.book_ad_info: bool | int = False
        from multiprocessing import Value  # noqa: PLC0415

        self.css_ad_info = Value("i", 0)
        self.images_ad_info = Value("i", 0)
        self.last_request: Any = (None,)
        self.in_error = False
        self.state_status = Value("i", 0)

        # Set up exception handler
        sys.excepthook = self.unhandled_exception

    def intro(self) -> None:
        """Display ASCII art logo."""
        if self.quiet:
            return

    def book_info(self, info: dict[str, Any]) -> None:
        """
        Display book metadata in a Rich Table.

        Args:
            info: Dictionary containing book metadata
        """
        if self.quiet:
            return

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Title
        title = info.get("title", "N/A")
        table.add_row(f"{EMOJI_MAP['book']} Title", title)

        # Authors - handle both str items and dict items ({"name": "..."})
        authors = info.get("authors", [])
        if isinstance(authors, list) and authors:
            author_str = ", ".join(
                aut.get("name", "") if isinstance(aut, dict) else str(aut) for aut in authors
            )
        else:
            author_str = str(authors) if authors else "N/A"
        table.add_row("👤 Author", author_str)

        # Publisher - handle both str items and dict items ({"name": "..."})
        publishers = info.get("publishers", [])
        if isinstance(publishers, list) and publishers:
            first = publishers[0]
            publisher = first.get("name", "") if isinstance(first, dict) else str(first)
        else:
            publisher = str(publishers) if publishers else "N/A"
        table.add_row("🏢 Publisher", publisher)

        # Year
        issued = info.get("issued", "N/A")
        if issued and issued != "N/A":
            table.add_row("📅 Published", str(issued))

        # ISBN
        isbn = info.get("isbn", self.book_id)
        table.add_row("🔖 ISBN", isbn)

        panel = Panel(
            table,
            title="[bold green]Book Information[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

        # Start a spinner while chapters/CSS/images are being fetched
        self._status = self.console.status(
            "[bold green]Downloading book contents...",
            spinner="dots",
        )
        self._status.start()

    def _stop_status(self) -> None:
        """Stop the status spinner if it's running."""
        if self._status is not None:
            self._status.stop()
            self._status = None

    def start_progress(
        self,
        chapters: int = 0,
        css: int = 0,
        images: int = 0,
    ) -> None:
        """
        Initialize multi-task progress display.

        Args:
            chapters: Total number of chapters
            css: Total number of CSS files
            images: Total number of images
        """
        self._stop_status()

        if self.quiet:
            return

        self.task_totals = {
            "chapters": chapters,
            "css": css,
            "images": images,
        }

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(
                complete_style=PROGRESS_COLORS["complete"],
                finished_style=PROGRESS_COLORS["finished"],
            ),
            TaskProgressColumn(),
            TextColumn("{task.completed}/{task.total}"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

        self.progress.start()

        # Add tasks
        if chapters > 0:
            self.task_ids["chapters"] = self.progress.add_task(
                f"{EMOJI_MAP['chapters']} Chapters",
                total=chapters,
            )

        if css > 0:
            self.task_ids["css"] = self.progress.add_task(
                f"{EMOJI_MAP['css']} CSS",
                total=css,
            )

        if images > 0:
            self.task_ids["images"] = self.progress.add_task(
                f"{EMOJI_MAP['images']} Images",
                total=images,
            )

    def update_chapters(self, completed: int, advance: int | None = None) -> None:
        """
        Update chapter download progress.

        Args:
            completed: Total completed chapters
            advance: Number to advance (alternative to completed)
        """
        if self.progress and self.task_ids["chapters"] is not None:
            if advance is not None:
                self.progress.advance(self.task_ids["chapters"], advance)
            else:
                self.progress.update(self.task_ids["chapters"], completed=completed)

    def update_css(self, completed: int, advance: int | None = None) -> None:
        """
        Update CSS download progress.

        Args:
            completed: Total completed CSS files
            advance: Number to advance (alternative to completed)
        """
        if self.progress and self.task_ids["css"] is not None:
            if advance is not None:
                self.progress.advance(self.task_ids["css"], advance)
            else:
                self.progress.update(self.task_ids["css"], completed=completed)

    def update_images(self, completed: int, advance: int | None = None) -> None:
        """
        Update image download progress.

        Args:
            completed: Total completed images
            advance: Number to advance (alternative to completed)
        """
        if self.progress and self.task_ids["images"] is not None:
            if advance is not None:
                self.progress.advance(self.task_ids["images"], advance)
            else:
                self.progress.update(self.task_ids["images"], completed=completed)

    def finish_progress(self) -> None:
        """Complete and cleanup progress display."""
        if self.progress:
            self.progress.stop()
            self.progress = None

    def state(self, origin: int, done: int) -> None:
        """
        Update progress for the current active task.

        Args:
            origin: Total items
            done: Completed items
        """
        if self.current_task and self.progress:
            task_id = self.task_ids.get(self.current_task)
            if task_id is not None:
                self.progress.update(task_id, completed=done, total=origin)

    def set_current_task(self, task_name: str) -> None:
        """
        Set the current active task for legacy state() calls.

        Args:
            task_name: Name of task ("chapters", "css", or "images")
        """
        self.current_task = task_name

    def out(self, message: str) -> None:
        """
        Display a regular message.

        Args:
            message: Message to display
        """
        if self.quiet:
            return
        self.console.print(message)

    def log(self, message: str) -> None:
        """
        Display a log message with info styling.

        Args:
            message: Message to display
        """
        if self.quiet:
            return
        self.console.print(f"{EMOJI_MAP['info']} {message}")

    def error(self, message: str) -> None:
        """
        Display error message with Rich formatting.

        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]{EMOJI_MAP['error']} Error:[/bold red] {message}")

    def exit_with_error(self, message: str) -> None:
        """
        Display error and exit.

        Args:
            message: Error message to display before exiting
        """
        self.console.print(f"\n[bold red]{EMOJI_MAP['error']} Fatal Error:[/bold red] {message}\n")
        sys.exit(1)

    def unhandled_exception(self, e_type: type, e_val: BaseException, e_tb: Any) -> None:
        """
        Display unhandled exception with Rich traceback.

        Args:
            e_type: Exception type
            e_val: Exception value
            e_tb: Exception traceback
        """
        from rich.traceback import Traceback  # noqa: PLC0415

        self.console.print("\n[bold red]Unhandled Exception:[/bold red]\n")
        traceback = Traceback.from_exception(e_type, e_val, e_tb, show_locals=True)
        self.console.print(traceback)

    def success(self, message: str) -> None:
        """
        Display success message.

        Args:
            message: Success message to display
        """
        if self.quiet:
            return
        self.console.print(f"[bold green]{EMOJI_MAP['success']} {message}[/bold green]")

    # Legacy Display compatibility methods

    def set_output_dir(self, output_dir: str) -> None:
        """
        Set the output directory for downloads (legacy compatibility).

        Args:
            output_dir: Path to the output directory
        """
        from logger import get_logger  # noqa: PLC0415

        get_logger("SafariBooks").debug(f"Output directory: {output_dir}")
        self.output_dir = output_dir
        self.output_dir_set = True

    def unregister(self) -> None:
        """Clean up display resources and unregister the custom exception handler."""
        self._stop_status()
        if self.progress is not None:
            self.progress.stop()
            self.progress = None
        sys.excepthook = sys.__excepthook__

    def save_last_request(self) -> None:
        """Save information about the last request for debugging (legacy compatibility)."""
        from logger import get_logger  # noqa: PLC0415

        logger = get_logger("SafariBooks")
        if any(self.last_request):
            url, data, others, status, headers, text = self.last_request
            logger.debug(
                f"Last request done:\n\tURL: {url}\n\tDATA: {data}\n\tOTHERS: {others}\n\n\t{status}\n{headers}\n\n{text}\n"
            )

    def parse_description(self, desc: str | None) -> str:
        """
        Parse HTML description and return text content (legacy compatibility).

        Args:
            desc: HTML description string or None

        Returns:
            Parsed text content or "n/d" if no description
        """
        if not desc:
            return "n/d"
        try:
            from bs4 import BeautifulSoup  # noqa: PLC0415

            soup = BeautifulSoup(desc, "lxml")
            text = soup.get_text()
            return str(text)
        except Exception as e:
            from logger import get_logger  # noqa: PLC0415

            logger = get_logger("SafariBooks")
            logger.debug(f"Error parsing the description: {e}")
            return "n/d"

    def done(self, epub_file: str) -> None:
        """
        Display completion message (legacy compatibility).

        Args:
            epub_file: Path to the generated EPUB file
        """
        if not self.quiet:
            self.success(f"Done: {epub_file}\n\n")

    def info(self, message: str) -> None:
        """
        Log an info message (legacy compatibility).

        Args:
            message: Message to log
        """
        if not self.quiet:
            from logger import get_logger  # noqa: PLC0415

            logger = get_logger("SafariBooks")
            logger.info(message)

    def exit(self, message: str) -> None:
        """
        Log an error message and exit the program (legacy compatibility).

        Args:
            message: Error message to display before exiting
        """
        from logger import get_logger  # noqa: PLC0415

        logger = get_logger("SafariBooks")
        logger.error(message)
        self.save_last_request()
        sys.exit(1)

    @staticmethod
    def api_error(response: dict[str, Any]) -> str:
        """Format API error messages."""
        from pathlib import Path  # noqa: PLC0415

        safari_base_url = "https://learning.oreilly.com"
        cookies_file = Path(__file__).resolve().parent.parent.parent.parent / "cookies.json"

        message = "API: "
        if "detail" in response and "Not found" in response["detail"]:
            message += (
                "book's not present in Safari Books Online.\n"
                "    The book identifier is the digits that you can find in the URL:\n"
                "    `" + safari_base_url + "/library/view/book-name/XXXXXXXXXXXXX/`"
            )
        else:
            if cookies_file.exists():
                cookies_file.unlink()
            message += (
                f"Out-of-Session ({response['detail']}).\n"
                if "detail" in response
                else "Out-of-Session.\n"
                " [+] Use the `--cred` or `--login` options in order to perform the auth login to Safari."
            )

        return message
