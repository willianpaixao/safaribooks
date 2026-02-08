"""Tests for async HTTP client."""

from pathlib import Path

import httpx
import pytest
import respx

# Import from installed package
from safaribooks.client import SafariBooksClient
from safaribooks.models import BookInfo, SafariBooksConfig
from safaribooks.utils.exceptions import (
    AuthenticationError,
    BookNotFoundError,
    ValidationError,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return SafariBooksConfig(
        output_dir=Path("/tmp/test_books"),
        cookies_file=Path("/tmp/cookies.json"),
        api_url="https://api.oreilly.com",
        timeout=10,
    )


@pytest.fixture
def cookies():
    """Create test cookies."""
    return {"sessionid": "test_session_123"}


@pytest.fixture
def sample_book_data():
    """Sample book API response."""
    return {
        "identifier": "9781492045304",
        "title": "Test Book Title",
        "isbn": "9781492045304",
        "description": "A test book",
        "authors": [{"name": "Test Author"}],
        "publishers": [{"name": "Test Publisher"}],
        "subjects": [{"name": "Python"}],
        "rights": "All rights reserved",
        "issued": "2024-01-01",
        "language": "en",
        "last_chapter_read": "ch01",  # Should be removed
    }


@pytest.fixture
def sample_chapters_data():
    """Sample chapters API response."""
    return {
        "count": 2,
        "next": None,
        "results": [
            {
                "id": "ch01",
                "filename": "chapter01.xhtml",
                "label": "Chapter 1",
                "href": "chapter01.xhtml",
                "fragment": "",
                "depth": 1,
                "children": [],
            },
            {
                "id": "ch02",
                "filename": "chapter02.xhtml",
                "label": "Chapter 2",
                "href": "chapter02.xhtml",
                "fragment": "",
                "depth": 1,
                "children": [],
            },
        ],
    }


class TestSafariBooksClientInitialization:
    """Test client initialization."""

    @pytest.mark.asyncio
    async def test_client_can_be_created(self, cookies, config):
        """Test that client can be instantiated."""
        async with SafariBooksClient(cookies, config) as client:
            assert client is not None
            assert client._config == config

    @pytest.mark.asyncio
    async def test_client_context_manager(self, cookies, config):
        """Test async context manager."""
        async with SafariBooksClient(cookies, config) as client:
            assert client._client is not None
        # Client should be closed after context


class TestGetBookInfo:
    """Test get_book_info method."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_book_info_fetch(self, cookies, config, sample_book_data):
        """Test successful book info retrieval."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        # Mock the API response
        respx.get(url).mock(return_value=httpx.Response(200, json=sample_book_data))

        async with SafariBooksClient(cookies, config) as client:
            book_info = await client.get_book_info(book_id)

            assert isinstance(book_info, BookInfo)
            assert book_info.identifier == "9781492045304"
            assert book_info.title == "Test Book Title"
            assert len(book_info.authors) == 1
            assert book_info.authors[0].name == "Test Author"

    @pytest.mark.asyncio
    @respx.mock
    async def test_book_info_removes_last_chapter_read(self, cookies, config, sample_book_data):
        """Test that last_chapter_read is removed from response."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        respx.get(url).mock(return_value=httpx.Response(200, json=sample_book_data))

        async with SafariBooksClient(cookies, config) as client:
            book_info = await client.get_book_info(book_id)
            # last_chapter_read should not be in the model
            assert book_info is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_book_info_not_found(self, cookies, config):
        """Test 404 response raises BookNotFoundError."""
        book_id = "invalid_id"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        respx.get(url).mock(return_value=httpx.Response(404))

        async with SafariBooksClient(cookies, config) as client:
            with pytest.raises(BookNotFoundError):
                await client.get_book_info(book_id)

    @pytest.mark.asyncio
    @respx.mock
    async def test_book_info_authentication_error(self, cookies, config):
        """Test 401 response raises AuthenticationError."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        respx.get(url).mock(return_value=httpx.Response(401))

        async with SafariBooksClient(cookies, config) as client:
            with pytest.raises(AuthenticationError):
                await client.get_book_info(book_id)

    @pytest.mark.asyncio
    @respx.mock
    async def test_book_info_invalid_response(self, cookies, config):
        """Test invalid API response raises ValidationError."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        # Mock invalid response (single key dict)
        respx.get(url).mock(return_value=httpx.Response(200, json={"error": "test"}))

        async with SafariBooksClient(cookies, config) as client:
            with pytest.raises(ValidationError):
                await client.get_book_info(book_id)


class TestGetChapters:
    """Test get_chapters method."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_chapters_fetch(self, cookies, config, sample_chapters_data):
        """Test successful chapters retrieval."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/chapter/?page=1"

        respx.get(url).mock(return_value=httpx.Response(200, json=sample_chapters_data))

        async with SafariBooksClient(cookies, config) as client:
            chapters = await client.get_chapters(book_id)

            assert len(chapters) == 2
            assert chapters[0]["id"] == "ch01"
            assert chapters[1]["id"] == "ch02"

    @pytest.mark.asyncio
    @respx.mock
    async def test_chapters_pagination(self, cookies, config):
        """Test pagination handling."""
        book_id = "9781492045304"

        # Mock page 1
        page1_data = {
            "count": 3,
            "next": "https://api.oreilly.com/api/v1/book/123/chapter/?page=2",
            "results": [
                {
                    "id": "ch01",
                    "filename": "ch01.xhtml",
                    "label": "Chapter 1",
                    "href": "ch01.xhtml",
                    "fragment": "",
                    "depth": 1,
                    "children": [],
                }
            ],
        }

        # Mock page 2
        page2_data = {
            "count": 3,
            "next": None,
            "results": [
                {
                    "id": "ch02",
                    "filename": "ch02.xhtml",
                    "label": "Chapter 2",
                    "href": "ch02.xhtml",
                    "fragment": "",
                    "depth": 1,
                    "children": [],
                }
            ],
        }

        respx.get(f"{config.api_url}/api/v1/book/{book_id}/chapter/?page=1").mock(
            return_value=httpx.Response(200, json=page1_data)
        )
        respx.get(f"{config.api_url}/api/v1/book/{book_id}/chapter/?page=2").mock(
            return_value=httpx.Response(200, json=page2_data)
        )

        async with SafariBooksClient(cookies, config) as client:
            chapters = await client.get_chapters(book_id)

            assert len(chapters) == 2
            assert chapters[0]["id"] == "ch01"
            assert chapters[1]["id"] == "ch02"

    @pytest.mark.asyncio
    @respx.mock
    async def test_chapters_no_results(self, cookies, config):
        """Test empty chapters raises BookNotFoundError."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/chapter/?page=1"

        respx.get(url).mock(return_value=httpx.Response(200, json={"count": 0, "results": []}))

        async with SafariBooksClient(cookies, config) as client:
            with pytest.raises(BookNotFoundError):
                await client.get_chapters(book_id)


class TestDownloadContent:
    """Test download_content and download_text methods."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_download_content_bytes(self, cookies, config):
        """Test downloading binary content."""
        url = "https://learning.oreilly.com/image.png"
        content = b"fake image data"

        respx.get(url).mock(return_value=httpx.Response(200, content=content))

        async with SafariBooksClient(cookies, config) as client:
            result = await client.download_content(url)

            assert result == content
            assert isinstance(result, bytes)

    @pytest.mark.asyncio
    @respx.mock
    async def test_download_text(self, cookies, config):
        """Test downloading text content."""
        url = "https://learning.oreilly.com/chapter01.html"
        text = "<html><body>Test</body></html>"

        respx.get(url).mock(return_value=httpx.Response(200, text=text))

        async with SafariBooksClient(cookies, config) as client:
            result = await client.download_text(url)

            assert result == text
            assert isinstance(result, str)


class TestRetryLogic:
    """Test retry behavior."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_network_error(self, cookies, config, sample_book_data):
        """Test retry on network errors."""
        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        # First two requests fail, third succeeds
        route = respx.get(url)
        route.side_effect = [
            httpx.NetworkError("Connection failed"),
            httpx.NetworkError("Connection failed"),
            httpx.Response(200, json=sample_book_data),
        ]

        async with SafariBooksClient(cookies, config) as client:
            # Should succeed after retries
            book_info = await client.get_book_info(book_id)
            assert book_info.identifier == "9781492045304"

        # Verify it was called 3 times
        assert route.call_count == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_exhausted(self, cookies, config):
        """Test that retries eventually fail."""
        from tenacity import RetryError

        book_id = "9781492045304"
        url = f"{config.api_url}/api/v1/book/{book_id}/"

        # All requests fail
        route = respx.get(url)
        route.side_effect = httpx.NetworkError("Connection failed")

        async with SafariBooksClient(cookies, config) as client:
            # After all retries exhausted, tenacity raises RetryError
            with pytest.raises(RetryError):
                await client.get_book_info(book_id)

        # Should have tried 3 times (initial + 2 retries)
        assert route.call_count == 3
