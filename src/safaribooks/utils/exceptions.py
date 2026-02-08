"""Custom exception hierarchy for SafariBooks."""


class SafariBooksError(Exception):
    """Base exception for all SafariBooks errors."""


class AuthenticationError(SafariBooksError):
    """Raised when authentication fails or session is invalid."""


class BookNotFoundError(SafariBooksError):
    """Raised when book ID is invalid or not found."""


class DownloadError(SafariBooksError):
    """Raised when download operation fails."""


class ParsingError(SafariBooksError):
    """Raised when HTML/XML parsing fails."""


class EPUBGenerationError(SafariBooksError):
    """Raised when EPUB creation fails."""


class NetworkError(SafariBooksError):
    """Raised when network/HTTP request fails."""


class ValidationError(SafariBooksError):
    """Raised when data validation fails."""
