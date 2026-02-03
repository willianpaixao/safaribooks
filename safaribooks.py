#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
import traceback
import zipfile
from datetime import UTC, datetime
from html import escape
from multiprocessing import Process, Queue, Value
from pathlib import Path
from random import random
from typing import Any, ClassVar
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from logger import get_logger, get_valid_log_levels, setup_logger


PROJECT_ROOT = Path(__file__).resolve().parent
COOKIES_FILE = PROJECT_ROOT / "cookies.json"

ORLY_BASE_HOST = "oreilly.com"  # PLEASE INSERT URL HERE

SAFARI_BASE_HOST = "learning." + ORLY_BASE_HOST
API_ORIGIN_HOST = "api." + ORLY_BASE_HOST

ORLY_BASE_URL = "https://www." + ORLY_BASE_HOST
SAFARI_BASE_URL = "https://" + SAFARI_BASE_HOST
API_ORIGIN_URL = "https://" + API_ORIGIN_HOST
PROFILE_URL = SAFARI_BASE_URL + "/profile/"

# HTTP Status Codes
HTTP_OK = 200

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "gif"}

# Anti-bot detection threshold (random check)
ANTI_BOT_CHECK_THRESHOLD = 0.8

# DEBUG
USE_PROXY = False
PROXIES = {"https": "https://127.0.0.1:8080"}


class Display:
    """Display class for handling user interface and logging."""

    SH_DEFAULT = "\033[0m" if not sys.platform.startswith("win") else ""
    SH_YELLOW = "\033[33m" if not sys.platform.startswith("win") else ""
    SH_BG_RED = "\033[41m" if not sys.platform.startswith("win") else ""
    SH_BG_YELLOW = "\033[43m" if not sys.platform.startswith("win") else ""

    def __init__(self, book_id: str):
        self.output_dir = ""
        self.output_dir_set = False
        self.book_id = book_id
        self.columns, _ = shutil.get_terminal_size()

        # Allow dynamic assignment of these attributes
        self.book_ad_info: bool | int = False
        self.css_ad_info = Value("i", 0)
        self.images_ad_info = Value("i", 0)
        self.last_request: Any = (None,)
        self.in_error = False
        self.state_status = Value("i", 0)

        # Set up exception handler
        sys.excepthook = self.unhandled_exception

    def set_output_dir(self, output_dir: str) -> None:
        """Set the output directory for downloads.

        Args:
            output_dir: Path to the output directory
        """
        logger = get_logger("SafariBooks")
        logger.info(f"Output directory:\n    {output_dir}")
        self.output_dir = output_dir
        self.output_dir_set = True

    def unregister(self) -> None:
        """Unregister the custom exception handler."""
        sys.excepthook = sys.__excepthook__

    def unhandled_exception(self, exc_type: type, exc_value: BaseException, exc_tb: Any) -> None:
        """Handle unhandled exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception instance
            exc_tb: Traceback object
        """
        logger = get_logger("SafariBooks")
        logger.debug("".join(traceback.format_tb(exc_tb)))
        logger.error(f"Unhandled Exception: {exc_value} (type: {exc_value.__class__.__name__})")
        if self.output_dir_set:
            logger.error(
                f"Please delete the output directory '{self.output_dir}' and restart the program."
            )
        logger.critical("Aborting...")
        self.save_last_request()
        sys.exit(1)

    def save_last_request(self) -> None:
        """Save information about the last request for debugging."""
        logger = get_logger("SafariBooks")
        if any(self.last_request):
            url, data, others, status, headers, text = self.last_request
            logger.debug(
                f"Last request done:\n\tURL: {url}\n\tDATA: {data}\n\tOTHERS: {others}\n\n\t{status}\n{headers}\n\n{text}\n"
            )

    def intro(self) -> None:
        """Display the program intro."""
        output = (
            self.SH_YELLOW
            + (
                r"""
 ██████╗     ██████╗ ██╗  ██╗   ██╗██████╗
██╔═══██╗    ██╔══██╗██║  ╚██╗ ██╔╝╚════██╗
██║   ██║    ██████╔╝██║   ╚████╔╝   ▄███╔╝
██║   ██║    ██╔══██╗██║    ╚██╔╝    ▀▀══╝
╚██████╔╝    ██║  ██║███████╗██║     ██╗
 ╚═════╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝
"""
            )
            + self.SH_DEFAULT
        )
        output += "\n" + "~" * (self.columns // 2)
        self.out(output)

    def out(self, put: str | bytes) -> None:
        """Output a message directly to stdout (for non-logged output).

        Args:
            put: Message to output (string or bytes)
        """
        try:
            # If put is bytes, decode it
            decoded = put.decode("utf-8", "replace") if isinstance(put, bytes) else put
            s = f"\r{' ' * self.columns}\r{decoded}\n"
        except (TypeError, AttributeError):
            s = f"\r{' ' * self.columns}\r{put!s}\n"
        sys.stdout.write(s)

    def parse_description(self, desc: str | None) -> str:
        """Parse HTML description and return text content.

        Args:
            desc: HTML description string or None

        Returns:
            Parsed text content or "n/d" if no description
        """
        if not desc:
            return "n/d"
        try:
            soup = BeautifulSoup(desc, "lxml")
            text = soup.get_text()
            return str(text)
        except Exception as e:
            logger = get_logger("SafariBooks")
            logger.debug(f"Error parsing the description: {e}")
            return "n/d"

    def book_info(self, info: dict[str, Any]) -> None:
        """Display book information.

        Args:
            info: Dictionary containing book metadata
        """
        logger = get_logger("SafariBooks")
        description = self.parse_description(info.get("description")).replace("\n", " ")
        for t in [
            ("Title", info.get("title", "")),
            ("Authors", ", ".join(aut.get("name", "") for aut in info.get("authors", []))),
            ("Identifier", info.get("identifier", "")),
            ("ISBN", info.get("isbn", "")),
            ("Publishers", ", ".join(pub.get("name", "") for pub in info.get("publishers", []))),
            ("Rights", info.get("rights", "")),
            ("Description", description[:500] + "..." if len(description) >= 500 else description),
            ("Release Date", info.get("issued", "")),
            ("URL", info.get("web_url", "")),
        ]:
            logger.warning(f"{self.SH_YELLOW}{t[0]}{self.SH_DEFAULT}: {t[1]}")

    def state(self, origin: int, done: int) -> None:
        """Display progress state.

        Args:
            origin: Total number of items
            done: Number of completed items
        """
        progress = int(done * 100 / origin)
        bar = int(progress * (self.columns - 11) / 100)
        if self.state_status.value < progress:
            self.state_status.value = progress
            sys.stdout.write(
                "\r    "
                + self.SH_BG_YELLOW
                + "["
                + ("#" * bar).ljust(self.columns - 11, "-")
                + "]"
                + self.SH_DEFAULT
                + f"{progress:>4}"
                + "%"
                + ("\n" if progress == 100 else "")
            )

    def done(self, epub_file: str) -> None:
        """Display completion message.

        Args:
            epub_file: Path to the generated EPUB file
        """
        self.info(f"Done: {epub_file}\n\n")

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: Message to log
        """
        logger = get_logger("SafariBooks")
        logger.info(message)

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message to log
        """
        logger = get_logger("SafariBooks")
        logger.error(message)

    def exit(self, message: str) -> None:
        """Log an error message and exit the program.

        Args:
            message: Error message to display before exiting
        """
        logger = get_logger("SafariBooks")
        logger.error(message)
        self.save_last_request()
        sys.exit(1)

    @staticmethod
    def api_error(response: dict[str, Any]) -> str:
        """Format API error messages."""
        message = "API: "
        if "detail" in response and "Not found" in response["detail"]:
            message += (
                "book's not present in Safari Books Online.\n"
                "    The book identifier is the digits that you can find in the URL:\n"
                "    `" + SAFARI_BASE_URL + "/library/view/book-name/XXXXXXXXXXXXX/`"
            )

        else:
            COOKIES_FILE.unlink()
            message += (
                f"Out-of-Session ({response['detail']}).\n"
                if "detail" in response
                else "Out-of-Session.\n"
                + Display.SH_YELLOW
                + "[+]"
                + Display.SH_DEFAULT
                + " Use the `--cred` or `--login` options in order to perform the auth login to Safari."
            )

        return message


class SafariBooks:
    LOGIN_URL = ORLY_BASE_URL + "/member/auth/login/"
    LOGIN_ENTRY_URL = SAFARI_BASE_URL + "/login/unified/?next=/home/"

    API_TEMPLATE = SAFARI_BASE_URL + "/api/v1/book/{0}/"

    BASE_01_HTML = (
        "<!DOCTYPE html>\n"
        '<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xsi:schemaLocation="http://www.w3.org/2002/06/xhtml2/'
        ' http://www.w3.org/MarkUp/SCHEMA/xhtml2.xsd"'
        ' xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head>\n"
        "{0}\n"
        '<style type="text/css">'
        "body{{margin:1em;background-color:transparent!important;}}"
        "#sbo-rt-content *{{text-indent:0pt!important;}}#sbo-rt-content .bq{{margin-right:1em!important;}}"
        "img{{max-width:100%;max-height:100%;height:auto;width:auto;}}"
    )

    KINDLE_HTML = (
        "#sbo-rt-content *{{word-wrap:break-word!important;"
        "word-break:break-word!important;}}#sbo-rt-content table,#sbo-rt-content pre"
        "{{overflow-x:unset!important;overflow:unset!important;"
        "overflow-y:unset!important;white-space:pre-wrap!important;}}"
    )

    BASE_02_HTML = "</style></head>\n<body>{1}</body>\n</html>"

    CONTAINER_XML = (
        '<?xml version="1.0"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        "<rootfiles>"
        '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />'
        "</rootfiles>"
        "</container>"
    )

    # Format: ID, Title, Authors, Description, Subjects, Publisher, Rights, Date, CoverId, MANIFEST, SPINE, CoverUrl, Modified
    CONTENT_OPF = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid" version="3.0">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        "<dc:title>{1}</dc:title>\n"
        "{2}\n"
        "<dc:description>{3}</dc:description>\n"
        "{4}"
        "<dc:publisher>{5}</dc:publisher>\n"
        "<dc:rights>{6}</dc:rights>\n"
        "<dc:language>en-US</dc:language>\n"
        "<dc:date>{7}</dc:date>\n"
        '<dc:identifier id="bookid">{0}</dc:identifier>\n'
        '<meta property="dcterms:modified">{12}</meta>\n'
        "</metadata>\n"
        "<manifest>\n"
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />\n'
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />\n'
        "{9}\n"
        "</manifest>\n"
        '<spine toc="ncx">\n{10}</spine>\n'
        '<guide><reference href="{11}" title="Cover" type="cover" /></guide>\n'
        "</package>"
    )

    # Format: ID, Depth, Title, Author, NAVMAP
    TOC_NCX = (
        '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
        '<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"'
        ' "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        "<head>\n"
        '<meta content="ID:ISBN:{0}" name="dtb:uid"/>\n'
        '<meta content="{1}" name="dtb:depth"/>\n'
        '<meta content="0" name="dtb:totalPageCount"/>\n'
        '<meta content="0" name="dtb:maxPageNumber"/>\n'
        "</head>\n"
        "<docTitle><text>{2}</text></docTitle>\n"
        "<docAuthor><text>{3}</text></docAuthor>\n"
        "<navMap>{4}</navMap>\n"
        "</ncx>"
    )

    # Format: Title, NAV_ITEMS
    NAV_XHTML = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
        '<head>\n<meta charset="utf-8" />\n<title>{0}</title>\n</head>\n'
        '<body>\n<nav epub:type="toc" id="toc">\n'
        "<h1>Table of Contents</h1>\n<ol>\n{1}</ol>\n</nav>\n</body>\n</html>"
    )

    HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": LOGIN_ENTRY_URL,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    def _setup_session(self) -> None:
        """Set up the requests session with headers and proxy settings."""
        self.session = requests.Session()
        if USE_PROXY:  # DEBUG
            self.session.proxies = PROXIES
            self.session.verify = False
        self.session.headers.update(self.HEADERS)
        self.jwt: dict[str, Any] = {}

    def _setup_authentication(self) -> None:
        """Handle user authentication via cookies or login credentials."""
        if not self.args.cred:
            if not COOKIES_FILE.is_file():
                self.logger.error(
                    "Login: unable to find `cookies.json` file.\n"
                    "    Please use the `--cred` or `--login` options to perform the login."
                )
                if self.display.output_dir_set:
                    self.logger.error(
                        f"Please delete the output directory '{self.display.output_dir}' and restart the program."
                    )
                self.logger.critical("Aborting...")
                self.display.save_last_request()
                sys.exit(1)

            with COOKIES_FILE.open() as f:
                self.session.cookies.update(json.load(f))
        else:
            self.logger.warning("Logging into Safari Books Online...")
            self.do_login(*self.args.cred)
            if not self.args.no_cookies:
                with COOKIES_FILE.open("w") as f:
                    json.dump(self.session.cookies.get_dict(), f)

        self.check_login()

    def _fetch_book_metadata(self) -> None:
        """Fetch book information and chapter list from API."""
        self.book_id = self.args.bookid
        self.api_url = f"https://api.oreilly.com/api/v1/book/{self.book_id}/"

        self.logger.info("Retrieving book info...")
        self.book_info = self.get_book_info()
        self.display.book_info(self.book_info)

        self.logger.info("Retrieving book chapters...")
        self.book_chapters = self.get_book_chapters()
        self.chapters_queue = self.book_chapters[:]

        if len(self.book_chapters) > sys.getrecursionlimit():
            sys.setrecursionlimit(len(self.book_chapters))

        self.book_title = self.book_info["title"]
        self.base_url = self.book_info["web_url"]

    def _setup_directories(self) -> None:
        """Create output directories for book content."""
        self.clean_book_title = (
            "".join(self.escape_dirname(self.book_title).split(",")[:2]) + f" ({self.book_id})"
        )

        books_dir = PROJECT_ROOT / "Books"
        if not books_dir.is_dir():
            books_dir.mkdir()

        self.BOOK_PATH = str(books_dir / self.clean_book_title)
        self.display.set_output_dir(self.BOOK_PATH)
        self.css_path = ""
        self.images_path = ""
        self.create_dirs()

    def _initialize_content_collections(self) -> None:
        """Initialize collections for tracking chapters, CSS, and images."""
        self.chapter_title = ""
        self.filename = ""
        self.chapter_stylesheets: list[str] = []
        self.css: list[str] = []
        self.images: list[str] = []

        self.logger.warning(f"Downloading book contents... ({len(self.book_chapters)} chapters)")
        self.BASE_HTML = (
            self.BASE_01_HTML
            + (self.KINDLE_HTML if not self.args.kindle else "")
            + self.BASE_02_HTML
        )
        self.cover: bool | str = False

    def _download_book_content(self) -> None:
        """Download and process all book content (chapters, CSS, images)."""
        # Download chapters
        self.get()

        # Handle cover if not found in chapters
        if not self.cover:
            self.cover = self.get_default_cover() if "cover" in self.book_info else False
            cover_html = self.parse_html(
                BeautifulSoup(
                    f'<div id="sbo-rt-content"><img src="Images/{self.cover}"></div>', "lxml"
                ),
                True,
            )

            self.book_chapters = [
                {"filename": "default_cover.xhtml", "title": "Cover"}
            ] + self.book_chapters

            self.filename = self.book_chapters[0]["filename"]
            self.save_page_html(cover_html)

        # Download CSS files
        self.css_done_queue: Queue[int] = Queue(0)  # WinQueue removed - multiprocessing disabled
        self.logger.warning(f"Downloading book CSSs... ({len(self.css)} files)")
        self.collect_css()

        # Download images
        self.images_done_queue: Queue[int] = Queue(0)  # WinQueue removed - multiprocessing disabled
        self.logger.warning(f"Downloading book images... ({len(self.images)} files)")
        self.collect_images()

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize SafariBooks downloader.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.logger = get_logger("SafariBooks")
        self.display = Display(args.bookid)

        # Show welcome message
        self.logger.info("** Welcome to SafariBooks! **")
        self.display.intro()

        # Setup
        self._setup_session()
        self._setup_authentication()

        # Fetch metadata
        self._fetch_book_metadata()

        # Prepare directories and collections
        self._setup_directories()
        self._initialize_content_collections()

        # Download content
        self._download_book_content()

        # Create EPUB
        self.logger.warning("Creating EPUB file...")
        self.create_epub()

        # Save session cookies
        if not args.no_cookies:
            with COOKIES_FILE.open("w") as f:
                json.dump(self.session.cookies.get_dict(), f)

        # Completion
        self.logger.info(f"Done: {Path(self.BOOK_PATH) / f'{self.book_id}.epub'}\n\n")
        self.display.unregister()

    def exit_with_error(self, error_message: str) -> None:
        """Exit the program with an error message."""
        if not self.display.in_error:
            self.display.in_error = True
        self.logger.error(error_message)

        if self.display.output_dir_set:
            self.logger.error(
                f"Please delete the output directory '{self.display.output_dir}' and restart the program."
            )

        self.logger.critical("Aborting...")
        self.display.save_last_request()
        sys.exit(1)

    def requests_provider(
        self,
        url: str,
        is_post: bool = False,
        data: dict[str, Any] | None = None,
        perform_redirect: bool = True,
        **kwargs: Any,
    ) -> requests.Response | None:
        try:
            response: requests.Response = getattr(self.session, "post" if is_post else "get")(
                url, data=data, allow_redirects=False, **kwargs
            )

            self.display.last_request = (
                url,
                data,
                kwargs,
                response.status_code,
                "\n".join([f"\t{name}: {value}" for name, value in response.headers.items()]),
                response.text,
            )

        except (
            requests.ConnectionError,
            requests.ConnectTimeout,
            requests.RequestException,
        ) as request_exception:
            self.logger.error(str(request_exception))
            return None

        if response.is_redirect and perform_redirect and response.next and response.next.url:
            # Type narrowing: recursive call returns Optional[Response]
            return self.requests_provider(response.next.url, is_post, None, perform_redirect)
            # TODO How about **kwargs?

        return response

    @staticmethod
    def parse_cred(cred: str) -> list[str] | bool:
        if ":" not in cred:
            return False

        sep = cred.index(":")
        new_cred = ["", ""]
        new_cred[0] = cred[:sep].strip("'").strip('"')
        if "@" not in new_cred[0]:
            return False

        new_cred[1] = cred[sep + 1 :]
        return new_cred

    def do_login(self, email: str, password: str) -> None:
        response = self.requests_provider(self.LOGIN_ENTRY_URL)
        if response is None:
            self.exit_with_error("Login: unable to reach Safari Books Online. Try again...")
        assert response is not None  # exit_with_error calls sys.exit

        next_parameter: str | None = None
        try:
            query_part = urlparse(response.request.url).query
            query_string: str = (
                query_part if isinstance(query_part, str) else query_part.decode("utf-8")
            )
            parsed_query = parse_qs(query_string)
            next_parameter = parsed_query["next"][0]

        except (AttributeError, ValueError, IndexError, KeyError):
            self.exit_with_error(
                "Login: unable to complete login on Safari Books Online. Try again..."
            )

        # next_parameter is guaranteed to be str here because exit_with_error exits
        assert next_parameter is not None
        redirect_uri = API_ORIGIN_URL + quote_plus(next_parameter)

        response = self.requests_provider(
            self.LOGIN_URL,
            is_post=True,
            json={"email": email, "password": password, "redirect_uri": redirect_uri},
            perform_redirect=False,
        )

        if response is None:
            self.exit_with_error(
                "Login: unable to perform auth to Safari Books Online.\n    Try again..."
            )
        assert response is not None  # exit_with_error calls sys.exit

        if response.status_code != HTTP_OK:  # TODO To be reviewed
            try:
                error_page = BeautifulSoup(response.text, "lxml")
                error_list = error_page.find("ul", class_="errorlist")
                errors_message = (
                    [li.get_text() for li in error_list.find_all("li")] if error_list else []
                )
                recaptcha = error_page.find("div", class_="g-recaptcha")
                messages = (
                    [
                        f"    `{error}`"
                        for error in errors_message
                        if "password" in error or "email" in error
                    ]
                    if errors_message
                    else []
                ) + (
                    ["    `ReCaptcha required (wait or do logout from the website).`"]
                    if recaptcha
                    else []
                )
                self.exit_with_error(
                    "Login: unable to perform auth login to Safari Books Online.\n"
                    "[*] Details:\n"
                    + "\n".join(messages if messages else ["    Unexpected error!"])
                )
            except Exception as parsing_error:
                self.logger.error(str(parsing_error))
                self.exit_with_error(
                    "Login: your login went wrong and it encountered in an error"
                    " trying to parse the login details of Safari Books Online. Try again..."
                )

        assert response is not None  # Previous check guarantees this
        self.jwt = (
            response.json()
        )  # TODO: save JWT Tokens and use the refresh_token to restore user session
        response = self.requests_provider(self.jwt["redirect_uri"])
        if response is None:
            self.exit_with_error("Login: unable to reach Safari Books Online. Try again...")

    def check_login(self) -> None:
        response = self.requests_provider(PROFILE_URL, perform_redirect=False)

        if response is None:
            self.exit_with_error("Login: unable to reach Safari Books Online. Try again...")

        elif response.status_code != HTTP_OK:
            self.exit_with_error("Authentication issue: unable to access profile page.")

        elif 'user_type":"Expired"' in response.text:
            self.exit_with_error("Authentication issue: account subscription expired.")

        self.logger.warning("Successfully authenticated.")

    def get_book_info(self) -> dict[str, Any]:
        response = self.requests_provider(self.api_url)
        if response is None:
            self.exit_with_error("API: unable to retrieve book info.")
        assert response is not None  # exit_with_error calls sys.exit

        response_data: dict[str, Any] = response.json()
        if not isinstance(response_data, dict) or len(response_data.keys()) == 1:
            self.exit_with_error(self.display.api_error(response_data))

        response_data.pop("last_chapter_read", None)

        for key, value in response_data.items():
            if value is None:
                response_data[key] = "n/a"

        return response_data

    def get_book_chapters(self, page: int = 1) -> list[dict[str, Any]]:
        response = self.requests_provider(urljoin(self.api_url, f"chapter/?page={page}"))
        if response is None:
            self.display.exit("API: unable to retrieve book chapters.")
        assert response is not None  # display.exit calls sys.exit

        response_data: Any = response.json()

        if not isinstance(response_data, dict) or len(response_data.keys()) == 1:
            self.display.exit(self.display.api_error(response_data))

        if "results" not in response_data or not len(response_data["results"]):
            self.display.exit("API: unable to retrieve book chapters.")

        if response_data["count"] > sys.getrecursionlimit():
            sys.setrecursionlimit(response_data["count"])

        result = []
        result.extend(
            [
                c
                for c in response_data["results"]
                if "cover" in c["filename"] or "cover" in c["title"]
            ]
        )
        for c in result:
            del response_data["results"][response_data["results"].index(c)]

        result += response_data["results"]
        return result + (self.get_book_chapters(page + 1) if response_data["next"] else [])

    def get_default_cover(self) -> str | bool:
        response = self.requests_provider(self.book_info["cover"], stream=True)
        if response is None:
            self.display.error(f"Error trying to retrieve the cover: {self.book_info['cover']}")
            return False

        file_ext = response.headers["Content-Type"].split("/")[-1]
        cover_file = Path(self.images_path) / f"default_cover.{file_ext}"
        with cover_file.open("wb") as i:
            for chunk in response.iter_content(1024):
                i.write(chunk)

        return f"default_cover.{file_ext}"

    def get_html(self, url: str) -> BeautifulSoup:
        """Fetch and parse HTML from URL.

        Args:
            url: URL to fetch

        Returns:
            Parsed BeautifulSoup object (exits on error via display.exit())
        """
        response = self.requests_provider(url)
        if response is None or response.status_code != HTTP_OK:
            self.display.exit(
                f"Crawler: error trying to retrieve this page: {self.filename} ({self.chapter_title})\n    From: {url}"
            )
        assert response is not None  # display.exit calls sys.exit

        try:
            soup = BeautifulSoup(response.text, "lxml")
            return soup

        except Exception as parsing_error:
            self.display.error(str(parsing_error))
            self.display.exit(
                f"Crawler: error trying to parse this page: {self.filename} ({self.chapter_title})\n    From: {url}"
            )
            # This line is never reached because display.exit() calls sys.exit()
            # but mypy needs it for type checking
            raise

    @staticmethod
    def url_is_absolute(url: str) -> bool:
        """Check if URL is absolute (has a network location/domain).

        Args:
            url: URL string to check

        Returns:
            True if URL has a netloc (e.g., http://example.com), False otherwise
        """
        return bool(urlparse(url).netloc)

    @staticmethod
    def is_image_link(url: str) -> bool:
        """Check if URL points to an image file based on extension.

        Args:
            url: URL or file path to check

        Returns:
            True if file extension is jpg, jpeg, png, or gif (case-insensitive)
        """
        return Path(url).suffix[1:].lower() in SUPPORTED_IMAGE_FORMATS

    def link_replace(self, link: str | None) -> str | None:
        """Replace and transform links for EPUB format.

        Transforms HTML links to XHTML format and reorganizes image paths.

        Args:
            link: URL or link to transform

        Returns:
            Transformed link suitable for EPUB:
            - Images moved to Images/ directory
            - .html extensions changed to .xhtml
            - Book-specific URLs stripped and recursively processed
            - mailto: links preserved unchanged
        """
        if link and not link.startswith("mailto"):
            if not self.url_is_absolute(link):
                if any(x in link for x in ["cover", "images", "graphics"]) or self.is_image_link(
                    link
                ):
                    image = link.split("/")[-1]
                    return "Images/" + image

                return link.replace(".html", ".xhtml")

            if self.book_id in link:
                return self.link_replace(link.split(self.book_id)[-1])

        return link

    @staticmethod
    def get_cover(soup: BeautifulSoup) -> Any:
        """Extract cover image element from HTML.

        Searches for cover image using case-insensitive matching on multiple attributes.
        Checks img tags directly, then images within divs and links with 'cover' in their attributes.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            BeautifulSoup Tag element if found, None otherwise

        Note:
            Searches for 'cover' (case-insensitive) in:
            - img id, class, name, src, alt attributes
            - div and link container attributes
        """

        # Helper function to check if 'cover' is in any attribute
        def has_cover_in_attrs(tag: Any) -> bool:
            for attr in ["id", "class", "name", "src", "alt"]:
                value = tag.get(attr)
                if value:
                    # Handle both string and list values
                    values = value if isinstance(value, list) else [value]
                    if any("cover" in str(v).lower() for v in values):
                        return True
            return False

        # Try to find img directly with 'cover' in attributes
        for img in soup.find_all("img"):
            if has_cover_in_attrs(img):
                return img

        # Try to find img within div with 'cover' in attributes
        for div in soup.find_all("div"):
            if has_cover_in_attrs(div):
                found_img = div.find("img")
                if found_img is not None:
                    return found_img

        # Try to find img within link with 'cover' in attributes
        for link in soup.find_all("a"):
            if has_cover_in_attrs(link):
                found_img = link.find("img")
                if found_img is not None:
                    return found_img

        return None

    def _check_anti_bot_detection(self, soup: BeautifulSoup) -> None:
        """Check for anti-bot detection and exit if detected."""
        if random() > ANTI_BOT_CHECK_THRESHOLD:
            controls_div = soup.find("div", class_="controls")
            if controls_div and controls_div.find("a"):
                self.display.exit(self.display.api_error({}))

    def _extract_book_content(self, soup: BeautifulSoup) -> Any:
        """Extract the main book content from the page."""
        book_content = soup.find(id="sbo-rt-content")
        if not book_content:
            self.display.exit(
                f"Parser: book content's corrupted or not present: {self.filename} ({self.chapter_title})"
            )
        return book_content

    def _process_css_stylesheets(self, soup: BeautifulSoup) -> str:
        """Process all CSS stylesheets and return page CSS HTML."""
        page_css = ""

        # Process chapter stylesheets
        if len(self.chapter_stylesheets):
            for chapter_css_url in self.chapter_stylesheets:
                if chapter_css_url not in self.css:
                    self.css.append(chapter_css_url)
                    self.logger.info(f"Crawler: found a new CSS at {chapter_css_url}")

                page_css += (
                    f'<link href="Styles/Style{self.css.index(chapter_css_url):0>2}.css" '
                    'rel="stylesheet" type="text/css" />\n'
                )

        # Process stylesheet links
        stylesheet_links = soup.find_all("link", rel="stylesheet")
        if stylesheet_links:
            for s in stylesheet_links:
                href = s.get("href")
                if not href or not isinstance(href, str):
                    continue

                css_url = (
                    urljoin("https:", href) if href[:2] == "//" else urljoin(self.base_url, href)
                )

                if css_url not in self.css:
                    self.css.append(css_url)
                    self.logger.info(f"Crawler: found a new CSS at {css_url}")

                page_css += (
                    f'<link href="Styles/Style{self.css.index(css_url):0>2}.css" '
                    'rel="stylesheet" type="text/css" />\n'
                )

        # Process inline styles
        stylesheets = soup.find_all("style")
        if stylesheets:
            for css in stylesheets:
                data_template = css.get("data-template")
                if data_template and isinstance(data_template, str):
                    css.string = data_template
                    del css["data-template"]

                try:
                    css_str = str(css)
                    page_css += css_str + "\n"
                except Exception as parsing_error:
                    self.display.error(str(parsing_error))
                    self.display.exit(
                        f"Parser: error trying to parse one CSS found in this page: {self.filename} ({self.chapter_title})"
                    )

        return page_css

    def _process_svg_images(self, soup: BeautifulSoup) -> None:
        """Convert SVG image tags to regular img tags."""
        svg_image_tags = soup.find_all("image")
        if svg_image_tags:
            for img in svg_image_tags:
                # Find href attribute (could be href, xlink:href, etc.)
                href = img.get("href") or img.get("xlink:href")
                if href and isinstance(href, str):
                    # Get the SVG parent element
                    svg_parent = img.find_parent("g")
                    if svg_parent:
                        svg_root = svg_parent.find_parent()
                        if svg_root:
                            # Create new img tag
                            new_img = soup.new_tag("img", src=href)
                            # Replace the structure
                            svg_parent.decompose()
                            svg_root.append(new_img)

    def _rewrite_links_in_soup(self, soup: Any) -> None:
        """Rewrite all links in BeautifulSoup object using link_replace."""
        # Process all anchor tags
        for tag in soup.find_all("a", href=True):
            tag["href"] = self.link_replace(tag["href"])

        # Process all img tags
        for tag in soup.find_all("img", src=True):
            tag["src"] = self.link_replace(tag["src"])

        # Process all link tags (CSS, etc.)
        for tag in soup.find_all("link", href=True):
            tag["href"] = self.link_replace(tag["href"])

    def _fix_index_terms(self, soup: Any) -> None:
        """Fix index term anchors to be valid EPUB navigation targets.

        Index terms are marked with empty <a> tags that have data-type="indexterm"
        and an ID attribute. Many EPUB readers cannot navigate to these empty
        inline anchors, resulting in "no block found" errors.

        Strategy:
        1. If parent block has no ID and contains only one index term,
           move the ID to the parent element
        2. Otherwise, wrap the anchor in a <span> with the ID

        Args:
            soup: BeautifulSoup object containing the chapter content
        """
        # Find all index term markers
        index_terms = soup.find_all("a", {"data-type": "indexterm"})

        for term in index_terms:
            term_id = term.get("id")
            if not term_id:
                # No ID to fix
                continue

            # Find the nearest block-level parent element
            parent = term.find_parent(["p", "li", "td", "dd", "dt", "div", "section", "blockquote"])
            if not parent:
                # No suitable parent found, leave as-is
                self.logger.debug(f"No block parent found for index term {term_id}")
                continue

            # Check if we can safely move ID to parent
            parent_id = parent.get("id")
            sibling_index_terms = parent.find_all("a", {"data-type": "indexterm"})

            if not parent_id and len(sibling_index_terms) == 1:
                # Safe to move ID to parent - only one index term and no existing ID
                parent["id"] = term_id
                self.logger.debug(f"Moved index term ID {term_id} to parent {parent.name}")

                # Remove ID from anchor since it's now on parent
                del term["id"]

            else:
                # Not safe to move to parent - wrap in span instead
                # This handles cases where:
                # - Parent already has an ID
                # - Multiple index terms in same paragraph

                # Get the root soup object to create new tags
                # Navigate up to find the BeautifulSoup root
                root_soup = term
                while root_soup.parent is not None:
                    root_soup = root_soup.parent

                wrapper = root_soup.new_tag("span", id=term_id)
                term.wrap(wrapper)

                # Remove ID from anchor since it's now on wrapper
                if term.get("id"):
                    del term["id"]

                self.logger.debug(
                    f"Wrapped index term {term_id} in span "
                    f"(parent has ID: {bool(parent_id)}, "
                    f"siblings: {len(sibling_index_terms)})"
                )

    def _fix_image_dimensions(self, soup: Any) -> None:
        """Remove inline width/height attributes and styles from images.

        O'Reilly's HTML often includes inline width/height attributes or styles
        that override CSS and cause images to overflow the viewport. This method
        removes those attributes to allow our CSS max-width/max-height rules to work.
        """
        for img in soup.find_all("img"):
            # Remove width and height attributes
            if img.get("width"):
                del img["width"]
            if img.get("height"):
                del img["height"]

            # Remove or clean up style attribute if it contains width/height
            style = img.get("style")
            if style and isinstance(style, str):
                # Remove width and height from inline styles
                style_parts = [s.strip() for s in style.split(";") if s.strip()]
                cleaned_parts = [
                    part
                    for part in style_parts
                    if not part.lower().startswith(("width:", "height:", "width ", "height "))
                ]
                if cleaned_parts:
                    img["style"] = "; ".join(cleaned_parts)
                else:
                    del img["style"]

    def _create_cover_page(self, book_content: Any) -> tuple[str, Any]:
        """Create a cover page if cover image is found."""
        # Get the soup object to search in
        search_soup = (
            book_content
            if isinstance(book_content, BeautifulSoup)
            else BeautifulSoup(str(book_content), "lxml")
        )
        is_cover = self.get_cover(search_soup)

        if is_cover is not None:
            page_css = (
                "<style>"
                "body{display:table;position:absolute;margin:0!important;height:100%;width:100%;}"
                "#Cover{display:table-cell;vertical-align:middle;text-align:center;}"
                "#Cover img{max-height:90vh;max-width:90vw;height:auto;width:auto;margin-left:auto;margin-right:auto;}"
                "</style>"
            )
            # Create a new cover div
            cover_soup = BeautifulSoup('<div id="Cover"></div>', "lxml")
            cover_div = cover_soup.find("div", id="Cover")

            if cover_div is not None:
                # Create img tag and append to cover div
                cover_src = is_cover.get("src")
                if cover_src and isinstance(cover_src, str):
                    cover_img = cover_soup.new_tag("img", src=cover_src)
                    cover_div.append(cover_img)
                    self.cover = cover_src
                    return page_css, cover_div

        return "", book_content

    def parse_html(self, soup: BeautifulSoup, first_page: bool = False) -> tuple[str, str]:
        """Parse HTML content and extract book content with CSS.

        Args:
            soup: BeautifulSoup parsed HTML document
            first_page: If True, process as cover page

        Returns:
            Tuple of (page_css, xhtml_content)
        """
        # Check for anti-bot detection
        self._check_anti_bot_detection(soup)

        # Extract main book content
        book_content = self._extract_book_content(soup)

        # Process CSS stylesheets
        page_css = self._process_css_stylesheets(soup)

        # Process SVG images
        self._process_svg_images(soup)

        # Fix image dimensions (remove inline width/height that override CSS)
        self._fix_image_dimensions(book_content)

        # Rewrite links
        self._rewrite_links_in_soup(book_content)

        # Fix index term anchors for EPUB reader compatibility
        self._fix_index_terms(book_content)

        # Handle cover page or regular content
        xhtml_str: str = ""
        try:
            if first_page:
                cover_css, book_content = self._create_cover_page(book_content)
                if cover_css:  # Cover was found and created
                    page_css = cover_css

            xhtml_str = str(book_content)

        except Exception as parsing_error:
            self.display.error(str(parsing_error))
            self.display.exit(
                f"Parser: error trying to parse HTML of this page: {self.filename} ({self.chapter_title})"
            )

        assert xhtml_str is not None  # str() always returns str or display.exit() calls sys.exit
        return page_css, xhtml_str

    @staticmethod
    def escape_dirname(dirname: str, clean_space: bool = False) -> str:
        """Sanitize directory name by removing or replacing illegal characters.

        Makes directory names safe for filesystems by:
        - Handling colons (truncate if far into name, replace with comma on Windows)
        - Removing special characters: < > ? / \\ | * "
        - Optionally cleaning extra spaces

        Args:
            dirname: Directory name to sanitize
            clean_space: If True, replace multiple spaces with single space

        Returns:
            Sanitized directory name safe for all platforms
        """
        if ":" in dirname:
            if dirname.index(":") > 15:
                dirname = dirname.split(":")[0]
            elif sys.platform.startswith("win"):
                dirname = dirname.replace(":", ",")
            # On non-Windows platforms, colon will be replaced with underscore in the loop below

        for ch in [
            "~",
            "#",
            "%",
            "&",
            "*",
            "{",
            "}",
            "\\",
            "<",
            ">",
            "?",
            "/",
            "`",
            "'",
            '"',
            "|",
            "+",
            ":",
        ]:
            if ch in dirname:
                dirname = dirname.replace(ch, "_")

        return dirname if not clean_space else dirname.replace(" ", "")

    def create_dirs(self) -> None:
        book_path = Path(self.BOOK_PATH)
        if book_path.is_dir():
            self.logger.info(f"Book directory already exists: {self.BOOK_PATH}")
        else:
            book_path.mkdir(parents=True)

        oebps = book_path / "OEBPS"
        if not oebps.is_dir():
            self.display.book_ad_info = True
            oebps.mkdir(parents=True)

        css_path = oebps / "Styles"
        if css_path.is_dir():
            self.logger.info(f"CSSs directory already exists: {css_path}")
        else:
            css_path.mkdir(parents=True)
            self.display.css_ad_info.value = 1
        self.css_path = str(css_path)

        images_path = oebps / "Images"
        if images_path.is_dir():
            self.logger.info(f"Images directory already exists: {images_path}")
        else:
            images_path.mkdir(parents=True)
            self.display.images_ad_info.value = 1
        self.images_path = str(images_path)

    def save_page_html(self, contents: tuple[str, str]) -> None:
        self.filename = self.filename.replace(".html", ".xhtml")
        output_file = Path(self.BOOK_PATH) / "OEBPS" / self.filename
        output_file.write_bytes(
            self.BASE_HTML.format(contents[0], contents[1]).encode("utf-8", "xmlcharrefreplace")
        )

    def get(self) -> None:
        len_books = len(self.book_chapters)

        for _ in range(len_books):
            if not len(self.chapters_queue):
                return

            first_page = len_books == len(self.chapters_queue)

            next_chapter = self.chapters_queue.pop(0)
            self.chapter_title = next_chapter["title"]
            self.filename = next_chapter["filename"]

            asset_base_url = next_chapter["asset_base_url"]
            api_v2_detected = False
            if "v2" in next_chapter["content"]:
                asset_base_url = (
                    SAFARI_BASE_URL + f"/api/v2/epubs/urn:orm:book:{self.book_id}/files"
                )
                api_v2_detected = True

            if "images" in next_chapter and len(next_chapter["images"]):
                for img_url in next_chapter["images"]:
                    if api_v2_detected:
                        self.images.append(asset_base_url + "/" + img_url)
                    else:
                        self.images.append(urljoin(next_chapter["asset_base_url"], img_url))

            # Stylesheets
            self.chapter_stylesheets = []
            if "stylesheets" in next_chapter and len(next_chapter["stylesheets"]):
                self.chapter_stylesheets.extend(x["url"] for x in next_chapter["stylesheets"])

            if "site_styles" in next_chapter and len(next_chapter["site_styles"]):
                self.chapter_stylesheets.extend(next_chapter["site_styles"])

            file_path = Path(self.BOOK_PATH) / "OEBPS" / self.filename.replace(".html", ".xhtml")
            if file_path.is_file():
                if (
                    not self.display.book_ad_info
                    and next_chapter
                    not in self.book_chapters[: self.book_chapters.index(next_chapter)]
                ):
                    filename_xhtml = self.filename.replace(".html", ".xhtml")
                    self.logger.info(
                        f"File `{filename_xhtml}` already exists.\n"
                        f"    If you want to download again all the book,\n"
                        f"    please delete the output directory '{self.BOOK_PATH}' and restart the program."
                    )
                    self.display.book_ad_info = 2

            else:
                self.save_page_html(
                    self.parse_html(self.get_html(next_chapter["content"]), first_page)
                )

            self.display.state(len_books, len_books - len(self.chapters_queue))

    def _thread_download_css(self, url: str) -> None:
        css_file = Path(self.css_path) / f"Style{self.css.index(url):0>2}.css"
        if css_file.is_file():
            if not self.display.css_ad_info.value and url not in self.css[: self.css.index(url)]:
                self.logger.info(
                    f"File `{css_file}` already exists.\n"
                    f"    If you want to download again all the CSSs,\n"
                    f"    please delete the output directory '{self.BOOK_PATH}' and restart the program."
                )
                self.display.css_ad_info.value = 1

        else:
            response = self.requests_provider(url)
            if response is None:
                self.display.error(
                    f"Error trying to retrieve this CSS: {css_file}\n    From: {url}"
                )
            else:
                css_file.write_bytes(response.content)

        self.css_done_queue.put(1)
        self.display.state(len(self.css), self.css_done_queue.qsize())

    def _thread_download_images(self, url: str) -> None:
        image_name = url.split("/")[-1]
        image_path = Path(self.images_path) / image_name
        if image_path.is_file():
            if (
                not self.display.images_ad_info.value
                and url not in self.images[: self.images.index(url)]
            ):
                self.logger.info(
                    f"File `{image_name}` already exists.\n"
                    f"    If you want to download again all the images,\n"
                    f"    please delete the output directory '{self.BOOK_PATH}' and restart the program."
                )
                self.display.images_ad_info.value = 1

        else:
            response = self.requests_provider(urljoin(SAFARI_BASE_URL, url), stream=True)
            if response is None:
                self.display.error(
                    f"Error trying to retrieve this image: {image_name}\n    From: {url}"
                )
                return

            with image_path.open("wb") as img:
                for chunk in response.iter_content(1024):
                    img.write(chunk)

        self.images_done_queue.put(1)
        self.display.state(len(self.images), self.images_done_queue.qsize())

    def _start_multiprocessing(self, operation: Any, full_queue: list[str]) -> None:
        if len(full_queue) > 5:
            for i in range(0, len(full_queue), 5):
                self._start_multiprocessing(operation, full_queue[i : i + 5])

        else:
            process_queue = [Process(target=operation, args=(arg,)) for arg in full_queue]
            for proc in process_queue:
                proc.start()

            for proc in process_queue:
                proc.join()

    def collect_css(self) -> None:
        self.display.state_status.value = -1

        # "self._start_multiprocessing" seems to cause problem. Switching to mono-thread download.
        for css_url in self.css:
            self._thread_download_css(css_url)

    def collect_images(self) -> None:
        if self.display.book_ad_info == 2:
            self.logger.info(
                "Some of the book contents were already downloaded.\n"
                "    If you want to be sure that all the images will be downloaded,\n"
                "    please delete the output directory '"
                + self.BOOK_PATH
                + "' and restart the program."
            )

        self.display.state_status.value = -1

        # "self._start_multiprocessing" seems to cause problem. Switching to mono-thread download.
        for image_url in self.images:
            self._thread_download_images(image_url)

    def create_content_opf(self) -> str:
        self.css = next(os.walk(self.css_path))[2]
        self.images = next(os.walk(self.images_path))[2]

        manifest = []
        spine = []
        for c in self.book_chapters:
            c["filename"] = c["filename"].replace(".html", ".xhtml")
            item_id = escape("".join(c["filename"].split(".")[:-1]))
            manifest.append(
                '<item id="{0}" href="{1}" media-type="application/xhtml+xml" />'.format(
                    item_id, c["filename"]
                )
            )
            spine.append(f'<itemref idref="{item_id}"/>')

        for i in set(self.images):
            dot_split = i.split(".")
            head = "img_" + escape("".join(dot_split[:-1]))
            extension = dot_split[-1]
            # Add properties="cover-image" for the cover image (EPUB 3)
            is_cover = isinstance(self.cover, str) and i in self.cover
            properties_attr = ' properties="cover-image"' if is_cover else ""
            manifest.append(
                '<item id="{0}" href="Images/{1}" media-type="image/{2}"{3} />'.format(
                    head, i, "jpeg" if "jp" in extension else extension, properties_attr
                )
            )

        for css_idx in range(len(self.css)):
            manifest.append(
                f'<item id="style_{css_idx:0>2}" href="Styles/Style{css_idx:0>2}.css" media-type="text/css" />'
            )

        authors = "\n".join(
            "<dc:creator>{0}</dc:creator>".format(escape(aut.get("name", "n/d")))
            for aut in self.book_info.get("authors", [])
        )

        subjects = "\n".join(
            "<dc:subject>{0}</dc:subject>".format(escape(sub.get("name", "n/d")))
            for sub in self.book_info.get("subjects", [])
        )

        # EPUB 3 requires dcterms:modified timestamp
        modified_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        return self.CONTENT_OPF.format(
            (self.book_info.get("isbn", self.book_id)),
            escape(self.book_title),
            authors,
            escape(self.book_info.get("description", "")),
            subjects,
            ", ".join(escape(pub.get("name", "")) for pub in self.book_info.get("publishers", [])),
            escape(self.book_info.get("rights", "")),
            self.book_info.get("issued", ""),
            self.cover,
            "\n".join(manifest),
            "\n".join(spine),
            self.book_chapters[0]["filename"].replace(".html", ".xhtml"),
            modified_timestamp,
        )

    @staticmethod
    def parse_toc(
        toc_list: list[dict[str, Any]], count: int = 0, max_count: int = 0
    ) -> tuple[str, int, int]:
        result = ""
        for item in toc_list:
            count += 1
            max_count = max(max_count, int(item["depth"]))

            result += (
                '<navPoint id="{}" playOrder="{}">'
                "<navLabel><text>{}</text></navLabel>"
                '<content src="{}"/>'.format(
                    item["fragment"] if len(item["fragment"]) else item["id"],
                    count,
                    escape(item["label"]),
                    item["href"].replace(".html", ".xhtml").split("/")[-1],
                )
            )

            if item["children"]:
                sub_result, count, max_count = SafariBooks.parse_toc(
                    item["children"], count, max_count
                )
                result += sub_result

            result += "</navPoint>\n"

        return result, count, max_count

    @staticmethod
    def parse_nav_toc(toc_list: list[dict[str, Any]]) -> str:
        """Parse TOC data into HTML5 nav list items for EPUB 3."""
        result = ""
        for item in toc_list:
            href = item["href"].replace(".html", ".xhtml").split("/")[-1]
            label = escape(item["label"])
            if item["children"]:
                children_html = SafariBooks.parse_nav_toc(item["children"])
                result += f'<li>\n<a href="{href}">{label}</a>\n<ol>\n{children_html}</ol>\n</li>\n'
            else:
                result += f'<li><a href="{href}">{label}</a></li>\n'
        return result

    def create_nav_xhtml(self, toc_data: list[dict[str, Any]]) -> str:
        """Create the EPUB 3 navigation document (nav.xhtml)."""
        nav_items = self.parse_nav_toc(toc_data)
        return self.NAV_XHTML.format(escape(self.book_title), nav_items)

    def _fetch_toc_data(self) -> list[dict[str, Any]]:
        """Fetch TOC data from API."""
        response = self.requests_provider(urljoin(self.api_url, "toc/"))
        if response is None:
            self.display.exit(
                "API: unable to retrieve book chapters. "
                "Don't delete any files, just run again this program"
                " in order to complete the `.epub` creation!"
            )
        assert response is not None  # display.exit calls sys.exit

        toc_data_raw: Any = response.json()

        if not isinstance(toc_data_raw, list) and len(toc_data_raw.keys()) == 1:
            self.display.exit(
                self.display.api_error(toc_data_raw)
                + " Don't delete any files, just run again this program"
                " in order to complete the `.epub` creation!"
            )

        # Type narrowing: after the check above, toc_data_raw must be a list
        toc_data: list[dict[str, Any]] = toc_data_raw
        return toc_data

    def create_toc(self, toc_data: list[dict[str, Any]] | None = None) -> str:
        """Create the NCX table of contents."""
        if toc_data is None:
            toc_data = self._fetch_toc_data()

        navmap, _, max_depth = self.parse_toc(toc_data)
        return self.TOC_NCX.format(
            (self.book_info["isbn"] if self.book_info["isbn"] else self.book_id),
            max_depth,
            self.book_title,
            ", ".join(aut.get("name", "") for aut in self.book_info.get("authors", [])),
            navmap,
        )

    def _create_epub_zip(self, epub_path: str) -> None:
        """
        Create EPUB ZIP file with proper structure per EPUB 3.3 spec.

        The mimetype file MUST be:
        1. The first file in the archive
        2. Stored uncompressed (ZIP_STORED)
        3. Not have any extra field data

        All other files are compressed with ZIP_DEFLATED for smaller file size.
        """
        with zipfile.ZipFile(epub_path, "w") as epub:
            # 1. Add mimetype FIRST, uncompressed, no extra field
            book_path = Path(self.BOOK_PATH)
            mimetype_path = book_path / "mimetype"
            epub.write(str(mimetype_path), "mimetype", compress_type=zipfile.ZIP_STORED)

            # 2. Add all other files with compression
            for root, _dirs, files in os.walk(self.BOOK_PATH):
                for file in files:
                    if file == "mimetype":
                        continue  # Already added first
                    if file.endswith(".epub"):
                        continue  # Don't include the epub itself

                    file_path = Path(root) / file
                    arcname = file_path.relative_to(book_path)

                    # Use DEFLATED compression for all other files
                    epub.write(str(file_path), str(arcname), compress_type=zipfile.ZIP_DEFLATED)

    def create_epub(self) -> None:
        book_path = Path(self.BOOK_PATH)
        (book_path / "mimetype").write_text("application/epub+zip")

        meta_info = book_path / "META-INF"
        if meta_info.is_dir():
            self.logger.info(f"META-INF directory already exists: {meta_info}")
        else:
            meta_info.mkdir(parents=True)

        (meta_info / "container.xml").write_bytes(
            self.CONTAINER_XML.encode("utf-8", "xmlcharrefreplace")
        )

        # Fetch TOC data once for both NCX and nav.xhtml
        toc_data = self._fetch_toc_data()

        oebps = book_path / "OEBPS"
        (oebps / "content.opf").write_bytes(
            self.create_content_opf().encode("utf-8", "xmlcharrefreplace")
        )
        (oebps / "toc.ncx").write_bytes(
            self.create_toc(toc_data).encode("utf-8", "xmlcharrefreplace")
        )
        # EPUB 3 navigation document
        (oebps / "nav.xhtml").write_bytes(
            self.create_nav_xhtml(toc_data).encode("utf-8", "xmlcharrefreplace")
        )

        epub_path = book_path / f"{self.book_id}.epub"
        if epub_path.is_file():
            epub_path.unlink()

        self._create_epub_zip(str(epub_path))


# MAIN
if __name__ == "__main__":
    arguments = argparse.ArgumentParser(
        prog="safaribooks.py",
        description="Download and generate an EPUB of your favorite books"
        " from Safari Books Online.",
        add_help=False,
        allow_abbrev=False,
    )

    login_arg_group = arguments.add_mutually_exclusive_group()
    login_arg_group.add_argument(
        "--cred",
        metavar="<EMAIL:PASS>",
        default=False,
        help="Credentials used to perform the auth login on Safari Books Online."
        ' Es. ` --cred "account_mail@mail.com:password01" `.',
    )
    login_arg_group.add_argument(
        "--login",
        action="store_true",
        help="Prompt for credentials used to perform the auth login on Safari Books Online.",
    )

    arguments.add_argument(
        "--no-cookies",
        dest="no_cookies",
        action="store_true",
        help="Prevent your session data to be saved into `cookies.json` file.",
    )
    arguments.add_argument(
        "--kindle",
        dest="kindle",
        action="store_true",
        help="Add some CSS rules that block overflow on `table` and `pre` elements."
        " Use this option if you're going to export the EPUB to E-Readers like Amazon Kindle.",
    )
    arguments.add_argument(
        "--log-level",
        dest="log_level",
        metavar="<LEVEL>",
        default="INFO",
        choices=get_valid_log_levels(),
        help="Set the logging level. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO).",
    )
    arguments.add_argument(
        "--help", action="help", default=argparse.SUPPRESS, help="Show this help message."
    )
    arguments.add_argument(
        "--book-id",
        dest="bookid",
        metavar="<BOOK ID>",
        nargs="+",
        required=True,
        help="Book digits ID(s) that you want to download. You can specify multiple book IDs. "
        "You can find it in the URL (X-es): "
        "`" + SAFARI_BASE_URL + "/library/view/book-name/XXXXXXXXXXXXX/`",
    )

    args_parsed = arguments.parse_args()
    if args_parsed.cred or args_parsed.login:
        print(
            "WARNING: Due to recent changes on ORLY website, \n"
            "the `--cred` and `--login` options are temporarily disabled.\n"
            "    Please use the `cookies.json` file to authenticate your account.\n"
            "    See: https://github.com/willianpaixao/safaribooks/issues/358"
        )
        arguments.exit()

    elif args_parsed.no_cookies:
        arguments.error(
            "invalid option: `--no-cookies` is valid only if you use the `--cred` option"
        )

    # Set up the main logger with the specified log level
    setup_logger("SafariBooks", args_parsed.log_level)

    # Set up main logger for processing multiple books
    main_logger = get_logger("SafariBooks.Main")

    # Process each book ID
    for book_id in args_parsed.bookid:
        # Create a copy of args_parsed with the current book_id
        current_args = argparse.Namespace(**vars(args_parsed))
        current_args.bookid = book_id

        try:
            SafariBooks(current_args)
        except Exception as e:
            main_logger.error(f"Error processing book {book_id}: {e}")
            main_logger.info("Continuing with next book...")
            continue

    sys.exit(0)
