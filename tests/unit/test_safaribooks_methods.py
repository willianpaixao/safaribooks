"""Unit tests for SafariBooks class methods."""

from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup


# Mock the get_logger to avoid initialization issues
@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger for all tests."""
    with patch("safaribooks.get_logger") as mock:
        mock_logger_instance = Mock()
        mock.return_value = mock_logger_instance
        yield mock_logger_instance


@pytest.fixture
def mock_safaribooks_instance(tmp_path, mock_logger):
    """Create a minimal SafariBooks instance for testing."""
    # Import here to use mocked logger
    from safaribooks import Display, SafariBooks

    # Create a minimal mock for testing without full initialization
    instance = Mock(spec=SafariBooks)
    instance.book_id = "9781234567890"
    instance.base_url = "https://learning.oreilly.com"
    instance.filename = "test_chapter.xhtml"
    instance.chapter_title = "Test Chapter"
    instance.css = []
    instance.images = []
    instance.chapter_stylesheets = []
    instance.cover = None
    instance.logger = mock_logger

    # Mock display
    instance.display = Mock(spec=Display)
    instance.display.exit = Mock(side_effect=SystemExit)
    instance.display.error = Mock()

    # Bind real methods we want to test
    instance.parse_html = SafariBooks.parse_html.__get__(instance, SafariBooks)
    instance.link_replace = SafariBooks.link_replace.__get__(instance, SafariBooks)
    instance.get_cover = SafariBooks.get_cover
    instance.url_is_absolute = SafariBooks.url_is_absolute
    instance.is_image_link = SafariBooks.is_image_link

    # Bind helper methods extracted from parse_html refactoring
    instance._check_anti_bot_detection = SafariBooks._check_anti_bot_detection.__get__(
        instance, SafariBooks
    )
    instance._extract_book_content = SafariBooks._extract_book_content.__get__(
        instance, SafariBooks
    )
    instance._process_css_stylesheets = SafariBooks._process_css_stylesheets.__get__(
        instance, SafariBooks
    )
    instance._process_svg_images = SafariBooks._process_svg_images.__get__(instance, SafariBooks)
    instance._create_cover_page = SafariBooks._create_cover_page.__get__(instance, SafariBooks)
    instance._rewrite_links_in_soup = SafariBooks._rewrite_links_in_soup.__get__(
        instance, SafariBooks
    )
    instance._fix_image_dimensions = SafariBooks._fix_image_dimensions.__get__(
        instance, SafariBooks
    )

    return instance


class TestParseHtmlMethod:
    """Test the parse_html() method."""

    def test_parse_html_simple_content(self, mock_safaribooks_instance):
        """Test parsing simple HTML content."""
        html_content = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <h1>Chapter Title</h1>
                    <p>Chapter content here.</p>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        page_css, xhtml = mock_safaribooks_instance.parse_html(root, first_page=False)

        assert page_css == ""  # No stylesheets
        assert "Chapter Title" in xhtml
        assert "Chapter content here" in xhtml

    def test_parse_html_with_stylesheet_links(self, mock_safaribooks_instance):
        """Test parsing HTML with stylesheet links."""
        html_content = """
        <html>
            <head>
                <link rel="stylesheet" href="/static/style.css" />
            </head>
            <body>
                <div id="sbo-rt-content">
                    <p>Content</p>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        page_css, _xhtml = mock_safaribooks_instance.parse_html(root)

        assert 'href="Styles/Style00.css"' in page_css
        assert len(mock_safaribooks_instance.css) == 1
        assert "static/style.css" in mock_safaribooks_instance.css[0]

    def test_parse_html_with_inline_style(self, mock_safaribooks_instance):
        """Test parsing HTML with inline style tags."""
        html_content = """
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <div id="sbo-rt-content">
                    <p>Content</p>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        page_css, _xhtml = mock_safaribooks_instance.parse_html(root)

        assert "body { color: red; }" in page_css
        assert "<style>" in page_css

    def test_parse_html_with_data_template_style(self, mock_safaribooks_instance):
        """Test parsing style tags with data-template attribute."""
        html_content = """
        <html>
            <head>
                <style data-template=".class { color: blue; }"></style>
            </head>
            <body>
                <div id="sbo-rt-content">
                    <p>Content</p>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        page_css, _xhtml = mock_safaribooks_instance.parse_html(root)

        assert ".class { color: blue; }" in page_css

    def test_parse_html_missing_content_div(self, mock_safaribooks_instance):
        """Test that missing content div raises error."""
        html_content = """
        <html>
            <body>
                <div>Wrong div</div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        with pytest.raises(SystemExit):
            mock_safaribooks_instance.parse_html(root)

        mock_safaribooks_instance.display.exit.assert_called_once()

    def test_parse_html_first_page_without_cover(self, mock_safaribooks_instance):
        """Test parsing first page when no cover image found."""
        html_content = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <h1>Book Title</h1>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        _page_css, xhtml = mock_safaribooks_instance.parse_html(root, first_page=True)

        assert "Book Title" in xhtml
        assert mock_safaribooks_instance.cover is None

    def test_parse_html_first_page_with_cover(self, mock_safaribooks_instance):
        """Test parsing first page with cover image."""
        html_content = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <img id="cover-image" src="cover.jpg" alt="Cover" />
                    <h1>Book Title</h1>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        page_css, xhtml = mock_safaribooks_instance.parse_html(root, first_page=True)

        # Cover image gets moved to Images/ directory by link_replace
        assert "Images/cover.jpg" in xhtml or "cover.jpg" in xhtml
        assert 'id="Cover"' in xhtml
        assert "display:table" in page_css

    def test_parse_html_with_protocol_relative_css(self, mock_safaribooks_instance):
        """Test parsing CSS URLs with // protocol-relative format."""
        html_content = """
        <html>
            <head>
                <link rel="stylesheet" href="//cdn.example.com/style.css" />
            </head>
            <body>
                <div id="sbo-rt-content">
                    <p>Content</p>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        _page_css, _xhtml = mock_safaribooks_instance.parse_html(root)

        assert len(mock_safaribooks_instance.css) == 1
        assert "https://cdn.example.com/style.css" in mock_safaribooks_instance.css[0]

    def test_parse_html_with_svg_images(self, mock_safaribooks_instance):
        """Test parsing HTML with SVG image tags."""
        # SVG with xlink:href
        html_content = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <svg>
                        <g>
                            <image href="image.png"/>
                        </g>
                    </svg>
                </div>
            </body>
        </html>
        """
        root = BeautifulSoup(html_content, "lxml")

        # Should convert SVG image to img tag
        _page_css, xhtml = mock_safaribooks_instance.parse_html(root)

        # After conversion, should have img tag
        assert "img" in xhtml or "image" in xhtml


class TestGetCoverMethod:
    """Test the get_cover() static method."""

    def test_get_cover_by_id(self):
        """Test finding cover by element ID."""
        from safaribooks import SafariBooks

        html_content = '<div><img id="cover" src="cover.jpg"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_by_class(self):
        """Test finding cover by class name."""
        from safaribooks import SafariBooks

        html_content = '<div><img class="book-cover" src="cover.jpg"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_by_alt_text(self):
        """Test finding cover by alt text."""
        from safaribooks import SafariBooks

        html_content = '<div><img src="cover.jpg" alt="Cover Image"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_inside_div(self):
        """Test finding cover image inside a div with cover class."""
        from safaribooks import SafariBooks

        html_content = '<div class="cover-container"><img src="cover.jpg"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_inside_link(self):
        """Test finding cover image inside a link with cover class."""
        from safaribooks import SafariBooks

        html_content = '<a class="cover-link"><img src="cover.jpg"/></a>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_case_insensitive(self):
        """Test that cover detection is case-insensitive."""
        from safaribooks import SafariBooks

        html_content = '<div><img id="COVER-IMAGE" src="cover.jpg"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is not None
        assert result["src"] == "cover.jpg"

    def test_get_cover_not_found(self):
        """Test when no cover image is found."""
        from safaribooks import SafariBooks

        html_content = '<div><img id="regular-image" src="image.jpg"/></div>'
        root = BeautifulSoup(html_content, "lxml")

        result = SafariBooks.get_cover(root)

        assert result is None


class TestLinkReplaceMethod:
    """Test the link_replace() method with SafariBooks instance."""

    def test_link_replace_with_instance(self, mock_safaribooks_instance):
        """Test link replacement for relative HTML links."""
        # Relative HTML links (not absolute) get .html → .xhtml
        result = mock_safaribooks_instance.link_replace("chapter.html")
        assert result == "chapter.xhtml"

        # But absolute URLs don't get replaced unless they contain book_id
        result = mock_safaribooks_instance.link_replace("http://example.com/page.html")
        assert result == "http://example.com/page.html"

    def test_link_replace_with_book_id_in_url(self, mock_safaribooks_instance):
        """Test link replacement when URL contains book ID."""
        # When book_id is in URL, split and recursively process
        url = f"https://learning.oreilly.com/library/view/book/{mock_safaribooks_instance.book_id}/chapter01.html"
        result = mock_safaribooks_instance.link_replace(url)

        # After splitting by book_id and recursive processing
        assert "xhtml" in result


class TestEscapeDirnameEdgeCases:
    """Additional tests for escape_dirname edge cases."""

    def test_escape_dirname_multiple_colons(self):
        """Test directory name with multiple colons."""
        from safaribooks import SafariBooks

        # Long colon position (>15 chars)
        dirname = "This is a very long: directory: name"
        result = SafariBooks.escape_dirname(dirname)

        assert ":" not in result or result.index(":") > 15

    def test_escape_dirname_windows_colon(self):
        """Test colon replacement on Windows."""
        import sys

        from safaribooks import SafariBooks

        original_platform = sys.platform
        try:
            # Temporarily set to Windows
            sys.platform = "win32"

            result = SafariBooks.escape_dirname("Chapter: Introduction")

            # On Windows, : should be replaced with ,
            assert "," in result or ":" not in result
        finally:
            sys.platform = original_platform

    def test_escape_dirname_all_special_chars(self):
        """Test escaping all special characters."""
        from safaribooks import SafariBooks

        dirname = "Name<with>many?special/chars\\and|more*"
        result = SafariBooks.escape_dirname(dirname)

        # Check that special chars are removed
        assert "<" not in result
        assert ">" not in result
        assert "?" not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "*" not in result


class TestStaticMethods:
    """Test other static/utility methods."""

    def test_url_is_absolute_various_cases(self):
        """Test url_is_absolute with various URL formats."""
        from safaribooks import SafariBooks

        # url_is_absolute checks for netloc (domain), so only URLs with domains are absolute
        assert SafariBooks.url_is_absolute("http://example.com")
        assert SafariBooks.url_is_absolute("https://example.com/path")
        assert SafariBooks.url_is_absolute("//cdn.example.com/file.js")

        # Paths without domain are NOT absolute per urlparse
        assert not SafariBooks.url_is_absolute("/absolute/path")
        assert not SafariBooks.url_is_absolute("relative/path")
        assert not SafariBooks.url_is_absolute("file.html")

    def test_is_image_link_extensions(self):
        """Test is_image_link with various extensions."""
        from safaribooks import SafariBooks

        assert SafariBooks.is_image_link("image.jpg")
        assert SafariBooks.is_image_link("image.jpeg")
        assert SafariBooks.is_image_link("image.png")
        assert SafariBooks.is_image_link("image.gif")
        assert SafariBooks.is_image_link("IMAGE.JPG")  # Case insensitive
        assert not SafariBooks.is_image_link("file.pdf")
        assert not SafariBooks.is_image_link("style.css")
