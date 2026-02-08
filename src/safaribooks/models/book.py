"""Pydantic models for book metadata."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Author(BaseModel):
    """Book author information."""

    model_config = ConfigDict(frozen=True)

    name: str


class Publisher(BaseModel):
    """Publisher information."""

    model_config = ConfigDict(frozen=True)

    name: str


class Subject(BaseModel):
    """Book subject/tag information."""

    model_config = ConfigDict(frozen=True)

    name: str


class BookInfo(BaseModel):
    """Complete book metadata from Safari API.

    This model validates and structures the book information
    returned from the O'Reilly API.
    """

    # Required fields
    identifier: str = Field(..., description="Book ISBN or unique ID")
    title: str = Field(..., description="Book title")

    # Optional metadata
    isbn: str | None = None
    description: str | None = None
    rights: str | None = None
    issued: str | None = None  # Can be parsed to date if needed
    format: str | None = None
    language: str | None = Field(default="en", description="Book language code")

    # Related entities
    authors: list[Author] = Field(default_factory=list)
    publishers: list[Publisher] = Field(default_factory=list)
    subjects: list[Subject] = Field(default_factory=list)

    # Content metadata
    archive_id: str | None = None
    duration_seconds: int | None = None
    number_of_pages: int | None = None

    # URLs
    web_url: HttpUrl | None = None
    cover: HttpUrl | None = None

    model_config = ConfigDict(
        frozen=True,  # Immutable
        validate_assignment=True,
        use_enum_values=True,
    )

    @field_validator("duration_seconds", "number_of_pages", mode="before")
    @classmethod
    def handle_na_values(cls, v: Any) -> int | None:
        """Convert 'n/a' string to None for integer fields."""
        if v is None or v in {"n/a", ""}:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        if isinstance(v, int):
            return v
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    def get_author_names(self) -> list[str]:
        """Get list of author names."""
        return [author.name for author in self.authors]

    def get_publisher_names(self) -> list[str]:
        """Get list of publisher names."""
        return [publisher.name for publisher in self.publishers]

    def get_subject_names(self) -> list[str]:
        """Get list of subject names."""
        return [subject.name for subject in self.subjects]
