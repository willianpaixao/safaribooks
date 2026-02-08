"""Pydantic models for chapter/content metadata."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Chapter(BaseModel):
    """Single chapter or section of a book.

    Represents a single downloadable unit of content from
    the O'Reilly API.
    """

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
    )

    # Identification
    id: str = Field(..., description="Chapter unique identifier")
    filename: str = Field(..., description="Output filename (e.g., ch01.xhtml)")

    # Content
    label: str = Field(..., description="Chapter title/label")
    content: HttpUrl | None = Field(None, description="URL to chapter HTML content")
    href: str = Field(..., description="Relative path for EPUB TOC")
    fragment: str = Field(default="", description="URL fragment/anchor")

    # Asset references
    asset_base_url: HttpUrl | None = None
    images: list[str] = Field(default_factory=list, description="Image URLs in chapter")
    stylesheets: list[dict[str, str]] = Field(
        default_factory=list, description="CSS stylesheets used in chapter"
    )
    site_styles: list[str] = Field(default_factory=list, description="Site-wide CSS")

    # Navigation
    depth: int = Field(default=1, ge=1, le=10, description="Nesting level in TOC")
    children: list["Chapter"] = Field(default_factory=list, description="Nested sub-chapters")

    def has_children(self) -> bool:
        """Check if chapter has sub-chapters."""
        return len(self.children) > 0

    def get_xhtml_filename(self) -> str:
        """Get the XHTML filename for EPUB."""
        if self.filename.endswith(".xhtml"):
            return self.filename
        return self.filename.replace(".html", ".xhtml")


# Enable forward references for recursive Chapter model
Chapter.model_rebuild()
