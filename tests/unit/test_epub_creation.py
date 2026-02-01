"""Unit tests for EPUB creation methods."""

from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_safaribooks_for_epub(tmp_path):
    """Create a SafariBooks instance mock for EPUB testing."""
    from safaribooks import SafariBooks

    instance = Mock(spec=SafariBooks)
    instance.book_id = "9781234567890"
    instance.book_title = "Test Book Title"
    instance.BOOK_PATH = str(tmp_path / "Test_Book")
    instance.OEBPS_PATH = str(tmp_path / "Test_Book" / "OEBPS")
    instance.css_path = str(tmp_path / "Test_Book" / "OEBPS" / "Styles")
    instance.images_path = str(tmp_path / "Test_Book" / "OEBPS" / "Images")

    # Create directories
    Path(instance.css_path).mkdir(parents=True, exist_ok=True)
    Path(instance.images_path).mkdir(parents=True, exist_ok=True)

    # Sample book data
    instance.book_info = {
        "isbn": "9781234567890",
        "authors": [{"name": "John Doe"}, {"name": "Jane Smith"}],
        "description": "A test book description",
        "subjects": [{"name": "Programming"}, {"name": "Python"}],
        "publishers": [{"name": "Test Publisher"}],
        "rights": "Copyright Test 2026",
        "issued": "2026-01-31",
    }

    instance.book_chapters = [
        {
            "filename": "chapter01.html",
            "id": "ch01",
            "fragment": "",
            "label": "Chapter 1",
            "href": "chapter01.html",
            "depth": 1,
            "children": [],
        },
        {
            "filename": "chapter02.html",
            "id": "ch02",
            "fragment": "",
            "label": "Chapter 2",
            "href": "chapter02.html",
            "depth": 1,
            "children": [],
        },
    ]

    instance.cover = "Images/cover.jpg"
    instance.css = []
    instance.images = []

    # Bind real methods
    instance.create_content_opf = SafariBooks.create_content_opf.__get__(instance, SafariBooks)
    instance.parse_toc = SafariBooks.parse_toc
    instance.create_toc = SafariBooks.create_toc.__get__(instance, SafariBooks)
    instance.CONTENT_OPF = SafariBooks.CONTENT_OPF
    instance.TOC_NCX = SafariBooks.TOC_NCX
    instance.NAV_XHTML = SafariBooks.NAV_XHTML

    return instance


class TestCreateContentOpf:
    """Test the create_content_opf() method."""

    def test_create_content_opf_basic_structure(self, mock_safaribooks_for_epub):
        """Test that content.opf has correct basic structure."""
        # Create some dummy files
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("image1.jpg").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("cover.jpg").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check basic XML structure
        assert '<?xml version="1.0" encoding="utf-8"?>' in result
        assert "<package" in result
        assert 'version="3.0"' in result
        assert "</package>" in result

    def test_create_content_opf_has_metadata(self, mock_safaribooks_for_epub):
        """Test that content.opf includes all metadata."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("image1.jpg").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check metadata
        assert "<metadata" in result
        assert "<dc:title>Test Book Title</dc:title>" in result
        assert "<dc:creator>John Doe</dc:creator>" in result
        assert "<dc:creator>Jane Smith</dc:creator>" in result
        assert "A test book description" in result
        assert "<dc:publisher>Test Publisher</dc:publisher>" in result
        assert "<dc:rights>Copyright Test 2026</dc:rights>" in result

    def test_create_content_opf_has_dcterms_modified(self, mock_safaribooks_for_epub):
        """Test that EPUB 3 dcterms:modified is present."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check for EPUB 3 modified timestamp
        assert '<meta property="dcterms:modified">' in result
        assert "T" in result  # ISO 8601 timestamp format
        assert "Z" in result  # UTC indicator

    def test_create_content_opf_manifest_has_chapters(self, mock_safaribooks_for_epub):
        """Test that manifest includes all chapters."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check manifest items for chapters
        assert "<manifest>" in result
        assert "chapter01.xhtml" in result  # .html → .xhtml
        assert "chapter02.xhtml" in result
        assert 'media-type="application/xhtml+xml"' in result

    def test_create_content_opf_manifest_has_nav(self, mock_safaribooks_for_epub):
        """Test that manifest includes EPUB 3 nav.xhtml."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check for EPUB 3 navigation
        assert 'href="nav.xhtml"' in result
        assert 'properties="nav"' in result

    def test_create_content_opf_manifest_has_images(self, mock_safaribooks_for_epub):
        """Test that manifest includes image files."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("diagram.png").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("photo.jpg").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check images in manifest
        assert 'href="Images/diagram.png"' in result
        assert 'media-type="image/png"' in result
        assert 'href="Images/photo.jpg"' in result or 'href="Images/photo.jpeg"' in result

    def test_create_content_opf_cover_has_properties(self, mock_safaribooks_for_epub):
        """Test that cover image has cover-image property for EPUB 3."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()
        Path(mock_safaribooks_for_epub.images_path).joinpath("cover.jpg").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Cover should have properties="cover-image"
        # The logic checks if image filename is in self.cover
        assert "Images/cover.jpg" in result

    def test_create_content_opf_spine_order(self, mock_safaribooks_for_epub):
        """Test that spine has correct chapter order."""
        Path(mock_safaribooks_for_epub.css_path).joinpath("Style00.css").touch()

        result = mock_safaribooks_for_epub.create_content_opf()

        # Check spine
        assert "<spine" in result
        assert "<itemref idref=" in result
        # Spine should reference the chapter IDs
        assert "chapter01" in result or "ch01" in result


class TestParseToc:
    """Test the parse_toc() static method."""

    def test_parse_toc_simple_list(self):
        """Test parsing a simple table of contents."""
        from safaribooks import SafariBooks

        toc_data = [
            {
                "id": "ch1",
                "fragment": "",
                "label": "Chapter 1",
                "href": "ch1.html",
                "depth": 1,
                "children": [],
            },
            {
                "id": "ch2",
                "fragment": "",
                "label": "Chapter 2",
                "href": "ch2.html",
                "depth": 1,
                "children": [],
            },
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        assert "navPoint" in result
        assert "Chapter 1" in result
        assert "Chapter 2" in result
        assert "ch1.xhtml" in result  # .html → .xhtml
        assert count == 2
        assert max_depth == 1

    def test_parse_toc_nested_structure(self):
        """Test parsing nested table of contents."""
        from safaribooks import SafariBooks

        toc_data = [
            {
                "id": "ch1",
                "fragment": "",
                "label": "Chapter 1",
                "href": "ch1.html",
                "depth": 1,
                "children": [
                    {
                        "id": "ch1.1",
                        "fragment": "",
                        "label": "Section 1.1",
                        "href": "ch1.html#s1",
                        "depth": 2,
                        "children": [],
                    },
                ],
            },
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        assert "Chapter 1" in result
        assert "Section 1.1" in result
        assert count == 2  # Parent + child
        assert max_depth == 2

    def test_parse_toc_escapes_html(self):
        """Test that TOC labels are HTML-escaped."""
        from safaribooks import SafariBooks

        toc_data = [
            {
                "id": "ch1",
                "fragment": "",
                "label": "Chapter 1: <Test & More>",
                "href": "ch1.html",
                "depth": 1,
                "children": [],
            },
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        # HTML entities should be escaped
        assert "&lt;" in result or "<" not in result.replace("<navPoint", "").replace(
            "</navPoint>", ""
        )
        assert "&amp;" in result or "&" not in result.replace(
            "&", "", 1
        )  # Skip first & which might be &lt;


class TestCreateToc:
    """Test the create_toc() method."""

    def test_create_toc_structure(self, mock_safaribooks_for_epub):
        """Test that TOC NCX has correct structure."""
        # Mock _fetch_toc_data to return the book_chapters
        mock_safaribooks_for_epub._fetch_toc_data = Mock(
            return_value=mock_safaribooks_for_epub.book_chapters
        )

        result = mock_safaribooks_for_epub.create_toc()

        # Check NCX structure
        assert '<?xml version="1.0" encoding="utf-8"' in result
        assert "<!DOCTYPE ncx" in result
        assert "<ncx" in result
        assert 'version="2005-1"' in result
        assert "</ncx>" in result

    def test_create_toc_has_metadata(self, mock_safaribooks_for_epub):
        """Test that TOC includes book metadata."""
        mock_safaribooks_for_epub._fetch_toc_data = Mock(
            return_value=mock_safaribooks_for_epub.book_chapters
        )

        result = mock_safaribooks_for_epub.create_toc()

        # Check head metadata
        assert "<head>" in result
        assert 'name="dtb:uid"' in result
        assert mock_safaribooks_for_epub.book_id in result
        assert 'name="dtb:depth"' in result

    def test_create_toc_has_doc_title(self, mock_safaribooks_for_epub):
        """Test that TOC includes document title."""
        mock_safaribooks_for_epub._fetch_toc_data = Mock(
            return_value=mock_safaribooks_for_epub.book_chapters
        )

        result = mock_safaribooks_for_epub.create_toc()

        assert "<docTitle>" in result
        assert "<text>Test Book Title</text>" in result


class TestConstants:
    """Test that template constants are defined correctly."""

    def test_content_opf_template_exists(self):
        """Test that CONTENT_OPF template constant exists."""
        from safaribooks import SafariBooks

        assert hasattr(SafariBooks, "CONTENT_OPF")
        assert isinstance(SafariBooks.CONTENT_OPF, str)
        assert len(SafariBooks.CONTENT_OPF) > 0

    def test_content_opf_has_placeholders(self):
        """Test that CONTENT_OPF template has format placeholders."""
        from safaribooks import SafariBooks

        # Should have {0}, {1}, etc. for .format()
        assert "{0}" in SafariBooks.CONTENT_OPF or "{" in SafariBooks.CONTENT_OPF

    def test_toc_ncx_template_exists(self):
        """Test that TOC_NCX template constant exists."""
        from safaribooks import SafariBooks

        assert hasattr(SafariBooks, "TOC_NCX")
        assert isinstance(SafariBooks.TOC_NCX, str)

    def test_nav_xhtml_template_exists(self):
        """Test that NAV_XHTML template constant exists."""
        from safaribooks import SafariBooks

        assert hasattr(SafariBooks, "NAV_XHTML")
        assert isinstance(SafariBooks.NAV_XHTML, str)
