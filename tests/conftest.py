"""Shared pytest fixtures and configuration for SafariBooks tests."""

import json
from typing import Any
from unittest.mock import Mock

import pytest
import responses


@pytest.fixture
def sample_book_info() -> dict[str, Any]:
    """Sample book metadata from Safari API."""
    return {
        "identifier": "9781491958698",
        "isbn": "9781491958704",
        "title": "Test-Driven Development with Python",
        "authors": [{"name": "Harry J.W. Percival"}],
        "publishers": [{"name": "O'Reilly Media, Inc."}],
        "description": "A comprehensive guide to TDD with Python.",
        "rights": "Copyright © O'Reilly Media, Inc.",
        "issued": "2017-08-18",
        "web_url": "https://learning.oreilly.com/library/view/test-driven-development/9781491958698/",
        "cover": "https://learning.oreilly.com/covers/9781491958698/",
        "subjects": [
            {"name": "Python"},
            {"name": "Testing"},
        ],
    }


@pytest.fixture
def sample_chapter() -> dict[str, Any]:
    """Sample chapter metadata from Safari API."""
    return {
        "filename": "ch01.html",
        "title": "Chapter 1: Getting Started",
        "content": "https://learning.oreilly.com/api/v1/book/9781491958698/chapter/ch01.html",
        "asset_base_url": "https://learning.oreilly.com/api/v1/book/9781491958698/",
        "images": ["images/cover.png", "images/fig1-1.png"],
        "stylesheets": [
            {"url": "https://learning.oreilly.com/files/public/epub-reader/override_v1.css"}
        ],
        "site_styles": [],
        "depth": 1,
        "children": [],
    }


@pytest.fixture
def sample_chapter_html() -> str:
    """Sample chapter HTML content."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="styles/style.css" />
        <style>body { margin: 0; }</style>
    </head>
    <body>
        <div id="sbo-rt-content">
            <h1>Chapter 1</h1>
            <p>This is a test chapter with some content.</p>
            <img src="images/fig1-1.png" alt="Figure 1-1" />
            <a href="ch02.html">Next Chapter</a>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_toc_data() -> list[dict[str, Any]]:
    """Sample table of contents data."""
    return [
        {
            "href": "cover.html",
            "label": "Cover",
            "fragment": "cover",
            "id": "cover",
            "depth": "1",
            "children": [],
        },
        {
            "href": "ch01.html",
            "label": "Chapter 1: Getting Started",
            "fragment": "ch01",
            "id": "ch01",
            "depth": "1",
            "children": [
                {
                    "href": "ch01.html#section1",
                    "label": "Section 1.1",
                    "fragment": "section1",
                    "id": "section1",
                    "depth": "2",
                    "children": [],
                }
            ],
        },
    ]


@pytest.fixture
def mock_responses():
    """Provides responses mock for HTTP requests."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mock_book_api(mock_responses, sample_book_info):
    """Mock Safari Books API for book info endpoint."""
    book_id = sample_book_info["identifier"]
    url = f"https://learning.oreilly.com/api/v1/book/{book_id}/"

    mock_responses.add(
        responses.GET,
        url,
        json=sample_book_info,
        status=200,
    )
    return mock_responses


@pytest.fixture
def mock_chapters_api(mock_responses, sample_chapter):
    """Mock Safari Books API for chapters endpoint."""
    book_id = "9781491958698"
    url = f"https://learning.oreilly.com/api/v1/book/{book_id}/chapter/"

    mock_responses.add(
        responses.GET,
        url,
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [sample_chapter],
        },
        status=200,
    )
    return mock_responses


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    output = tmp_path / "Books" / "Test Book"
    output.mkdir(parents=True)
    return output


@pytest.fixture
def temp_cookies_file(tmp_path):
    """Temporary cookies.json file."""
    cookies_file = tmp_path / "cookies.json"
    cookies_file.write_text(
        json.dumps(
            {
                "BrowserCookie": "test_cookie_value",
                "orm-jwt": "test_jwt_token",
            }
        )
    )
    return cookies_file


@pytest.fixture
def mock_display():
    """Create a mock Display instance for testing."""
    display = Mock()
    display.book_id = "9781234567890"
    display.output_dir = "/tmp/safaribooks_test"
    display.output_dir_set = True
    return display


@pytest.fixture
def mock_args():
    """Create a mock args object for SafariBooks initialization."""
    args = Mock()
    args.bookid = "9781234567890"
    args.log_level = "INFO"
    args.kindle = False
    args.no_cookies = False
    args.cred = None  # Login is disabled, so cred should be None
    return args


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on location."""
    for item in items:
        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Auto-mark unit tests
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
