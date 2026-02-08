"""Async HTTP client for O'Reilly Safari API."""

from typing import Any

import httpx
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..models import BookInfo, SafariBooksConfig
from ..utils.exceptions import (
    AuthenticationError,
    BookNotFoundError,
    NetworkError,
)
from ..utils.exceptions import (
    ValidationError as SafariBooksValidationError,
)


class SafariBooksClient:
    """Async HTTP client for O'Reilly Safari Books API.

    This client handles all HTTP communication with the O'Reilly API,
    including authentication, retry logic, and response validation.

    Example:
        async with SafariBooksClient(cookies, config) as client:
            book_info = await client.get_book_info("9781492045304")
            chapters = await client.get_chapters("9781492045304")
    """

    def __init__(self, cookies: dict[str, str], config: SafariBooksConfig):
        """Initialize the async HTTP client.

        Args:
            cookies: Session cookies for authentication
            config: Application configuration
        """
        self._config = config
        self._client = httpx.AsyncClient(
            cookies=cookies,
            timeout=config.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "SafariBooks/2.0",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> "SafariBooksClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
    )
    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response

        Raises:
            NetworkError: On network/connection errors
            AuthenticationError: On 401 Unauthorized
            BookNotFoundError: On 404 Not Found
        """
        try:
            response = await self._client.request(method, url, **kwargs)

            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Session expired. Please update cookies.json with fresh session cookies."
                )

            # Handle not found errors
            if response.status_code == 404:
                raise BookNotFoundError(f"Resource not found: {url}")

            # Raise for other HTTP errors
            response.raise_for_status()

            return response

        except (AuthenticationError, BookNotFoundError):
            # Re-raise our custom exceptions without wrapping
            raise
        except httpx.HTTPStatusError as e:
            raise NetworkError(f"HTTP error {e.response.status_code}: {e}") from e
        except (httpx.NetworkError, httpx.TimeoutException):
            # These will be retried by tenacity
            raise
        except Exception as e:
            raise NetworkError(f"Unexpected error: {e}") from e

    async def get_book_info(self, book_id: str) -> BookInfo:
        """Fetch book metadata from API.

        Args:
            book_id: Book identifier (ISBN or numeric ID)

        Returns:
            Validated BookInfo object

        Raises:
            AuthenticationError: If session is invalid
            BookNotFoundError: If book ID is not found
            NetworkError: On network/HTTP errors
            SafariBooksValidationError: If API response is invalid
        """
        url = f"{self._config.api_url}/api/v1/book/{book_id}/"

        response = await self._request("GET", url)
        data = response.json()

        # Validate response structure
        if not isinstance(data, dict) or len(data) <= 1:
            raise SafariBooksValidationError(f"Invalid API response for book {book_id}: {data}")

        # Remove unnecessary fields
        data.pop("last_chapter_read", None)

        # Replace None values with "n/a"
        for key, value in data.items():
            if value is None:
                data[key] = "n/a"

        if (
            "cover" in data
            and data["cover"]
            and isinstance(data["cover"], str)
            and "api.oreilly.com/library/cover/" in data["cover"]
        ):
            # Extract book ID from the URL
            cover_url = data["cover"]
            # Transform: https://api.oreilly.com/library/cover/9781617294648/
            #         -> https://learning.oreilly.com/covers/9781617294648/400w/
            book_id_in_url = cover_url.rstrip("/").split("/")[-1]
            data["cover"] = f"https://learning.oreilly.com/covers/{book_id_in_url}/400w/"

        # Validate and parse with Pydantic
        try:
            return BookInfo.model_validate(data)  # type: ignore[no-any-return]
        except ValidationError as e:
            raise SafariBooksValidationError(f"Invalid book data: {e}") from e

    async def get_chapters(
        self,
        book_id: str,
        start_page: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch all chapters for a book (handles pagination).

        Args:
            book_id: Book identifier
            start_page: Starting page number (default: 1)

        Returns:
            List of chapter dictionaries

        Raises:
            AuthenticationError: If session is invalid
            BookNotFoundError: If book has no chapters
            NetworkError: On network/HTTP errors
        """
        base_url = f"{self._config.api_url}/api/v1/book/{book_id}/"
        all_chapters: list[dict[str, Any]] = []
        page = start_page

        while True:
            url = f"{base_url}chapter/?page={page}"
            response = await self._request("GET", url)
            data = response.json()

            # Validate response structure
            if not isinstance(data, dict) or len(data) <= 1:
                raise SafariBooksValidationError(f"Invalid chapter response: {data}")

            if "results" not in data or not data["results"]:
                if page == start_page:
                    raise BookNotFoundError(f"No chapters found for book {book_id}")
                break  # No more pages

            all_chapters.extend(data["results"])

            # Check if there are more pages
            if not data.get("next"):
                break

            page += 1

        return all_chapters

    async def download_content(self, url: str) -> bytes:
        """Download content (chapter HTML, CSS, images).

        Args:
            url: Content URL

        Returns:
            Raw content bytes

        Raises:
            NetworkError: On download errors
        """
        response = await self._request("GET", url)
        return response.content  # type: ignore[no-any-return]

    async def download_text(self, url: str) -> str:
        """Download text content (HTML, CSS, JSON).

        Args:
            url: Content URL

        Returns:
            Text content as string

        Raises:
            NetworkError: On download errors
        """
        response = await self._request("GET", url)
        return response.text  # type: ignore[no-any-return]
