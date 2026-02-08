"""Unit tests for HTML parser."""

import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from safaribooks.parser import CoverExtractor, HTMLParser, LinkRewriter


class TestLinkRewriter:
    """Test LinkRewriter class."""

    def test_rewrite_html_to_xhtml(self):
        """Test HTML to XHTML conversion."""
        rewriter = LinkRewriter("123", "https://example.com")
        assert rewriter.rewrite("page.html") == "page.xhtml"
        assert rewriter.rewrite("chapter1.html") == "chapter1.xhtml"

    def test_rewrite_image_to_images_dir(self):
        """Test image links are moved to Images/ directory."""
        rewriter = LinkRewriter("123", "https://example.com")
        assert rewriter.rewrite("cover/image.jpg") == "Images/image.jpg"
        assert rewriter.rewrite("images/fig1.png") == "Images/fig1.png"
        assert rewriter.rewrite("graphics/diagram.gif") == "Images/diagram.gif"

    def test_rewrite_preserves_mailto(self):
        """Test mailto links are preserved."""
        rewriter = LinkRewriter("123", "https://example.com")
        assert rewriter.rewrite("mailto:test@example.com") == "mailto:test@example.com"

    def test_rewrite_strips_book_id_from_absolute_url(self):
        """Test book ID is stripped from absolute URLs."""
        rewriter = LinkRewriter("9781234567890", "https://learning.oreilly.com")
        url = "https://learning.oreilly.com/library/view/book/9781234567890/chapter1.html"
        assert rewriter.rewrite(url) == "/chapter1.xhtml"

    def test_rewrite_none_returns_none(self):
        """Test None input returns None."""
        rewriter = LinkRewriter("123", "https://example.com")
        assert rewriter.rewrite(None) is None

    def test_url_is_absolute(self):
        """Test absolute URL detection."""
        assert LinkRewriter.url_is_absolute("https://example.com/page") is True
        assert LinkRewriter.url_is_absolute("http://example.com") is True
        assert LinkRewriter.url_is_absolute("relative/path") is False
        assert LinkRewriter.url_is_absolute("page.html") is False

    def test_is_image_link(self):
        """Test image link detection."""
        assert LinkRewriter.is_image_link("image.jpg") is True
        assert LinkRewriter.is_image_link("photo.JPG") is True
        assert LinkRewriter.is_image_link("diagram.png") is True
        assert LinkRewriter.is_image_link("graphic.gif") is True
        assert LinkRewriter.is_image_link("document.pdf") is False
        assert LinkRewriter.is_image_link("page.html") is False

    def test_rewrite_links_in_soup(self):
        """Test rewriting links in BeautifulSoup object."""
        html = """
        <div>
            <a href="page.html">Link</a>
            <img src="images/fig1.png" />
            <link href="style.css" rel="stylesheet" />
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        rewriter = LinkRewriter("123", "https://example.com")

        rewriter.rewrite_links_in_soup(soup)

        assert soup.find("a")["href"] == "page.xhtml"
        assert soup.find("img")["src"] == "Images/fig1.png"


class TestCoverExtractor:
    """Test CoverExtractor class."""

    def test_extract_cover_from_img_with_id(self):
        """Test extracting cover from img tag with cover ID."""
        html = '<img id="cover-image" src="cover.jpg" />'
        soup = BeautifulSoup(html, "lxml")

        cover = CoverExtractor.extract_cover(soup)

        assert cover is not None
        assert cover.name == "img"
        assert cover.get("src") == "cover.jpg"

    def test_extract_cover_from_img_with_class(self):
        """Test extracting cover from img tag with cover class."""
        html = '<img class="book-cover" src="cover.jpg" />'
        soup = BeautifulSoup(html, "lxml")

        cover = CoverExtractor.extract_cover(soup)

        assert cover is not None
        assert cover.get("src") == "cover.jpg"

    def test_extract_cover_from_div_container(self):
        """Test extracting cover from img inside div with cover class."""
        html = '<div class="cover"><img src="cover.jpg" /></div>'
        soup = BeautifulSoup(html, "lxml")

        cover = CoverExtractor.extract_cover(soup)

        assert cover is not None
        assert cover.name == "img"

    def test_extract_cover_returns_none_if_not_found(self):
        """Test returns None when no cover is found."""
        html = '<img src="regular-image.jpg" />'
        soup = BeautifulSoup(html, "lxml")

        cover = CoverExtractor.extract_cover(soup)

        assert cover is None

    def test_create_cover_page(self):
        """Test creating cover page HTML."""
        html = '<img id="cover" src="cover.jpg" />'
        soup = BeautifulSoup(html, "lxml")
        cover_img = soup.find("img")

        css, cover_div = CoverExtractor.create_cover_page(soup, cover_img)

        assert css != ""
        assert "body{display:table" in css
        assert cover_div is not None
        assert cover_div.find("img") is not None
        assert cover_div.find("img")["src"] == "cover.jpg"

    def test_create_cover_page_returns_original_if_no_cover(self):
        """Test returns original content if no cover image."""
        html = "<div>Original content</div>"
        soup = BeautifulSoup(html, "lxml")

        css, content = CoverExtractor.create_cover_page(soup, None)

        assert css == ""
        assert content == soup


class TestHTMLParser:
    """Test HTMLParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = HTMLParser(
            book_id="123",
            base_url="https://example.com",
            css_list=[],
            images_list=[],
        )

        assert parser.book_id == "123"
        assert parser.base_url == "https://example.com"
        assert isinstance(parser.link_rewriter, LinkRewriter)
        assert isinstance(parser.cover_extractor, CoverExtractor)

    def test_extract_book_content(self):
        """Test extracting book content from page."""
        html = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <h1>Chapter 1</h1>
                    <p>Content here</p>
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        content = parser._extract_book_content(soup)

        assert content is not None
        assert content.get("id") == "sbo-rt-content"

    def test_extract_book_content_raises_if_missing(self):
        """Test raises ValueError if content element is missing."""
        html = "<html><body><div>No content</div></body></html>"
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        with pytest.raises(ValueError, match="Book content not found"):
            parser._extract_book_content(soup)

    def test_fix_image_dimensions(self):
        """Test removing image width/height attributes."""
        html = """
        <div>
            <img src="img.jpg" width="500" height="300" style="width:500px;height:300px;" />
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        parser._fix_image_dimensions(soup)

        img = soup.find("img")
        assert img.get("width") is None
        assert img.get("height") is None
        assert "width" not in img.get("style", "")
        assert "height" not in img.get("style", "")

    def test_process_css_stylesheets_with_link_tags(self):
        """Test processing CSS stylesheet link tags."""
        html = """
        <html>
            <head>
                <link href="https://example.com/style.css" rel="stylesheet" />
            </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        css_list = []
        parser = HTMLParser("123", "https://example.com", css_list, [])

        page_css = parser._process_css_stylesheets(soup)

        assert "https://example.com/style.css" in css_list
        assert 'href="Styles/Style00.css"' in page_css

    def test_process_css_stylesheets_with_inline_styles(self):
        """Test processing inline style tags."""
        html = """
        <html>
            <head>
                <style>body { margin: 0; }</style>
            </head>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        page_css = parser._process_css_stylesheets(soup)

        assert "<style>" in page_css
        assert "body" in page_css

    def test_fix_index_terms_moves_id_to_parent(self):
        """Test index term ID is moved to parent when safe."""
        html = """
        <p><a data-type="indexterm" id="term1"></a>Text</p>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        parser._fix_index_terms(soup)

        p = soup.find("p")
        assert p.get("id") == "term1"
        a = soup.find("a")
        assert a.get("id") is None

    def test_fix_index_terms_wraps_in_span_when_not_safe(self):
        """Test index term is wrapped in span when parent has ID."""
        html = """
        <p id="para1"><a data-type="indexterm" id="term1"></a>Text</p>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        parser._fix_index_terms(soup)

        span = soup.find("span", id="term1")
        assert span is not None
        a = soup.find("a")
        assert a.get("id") is None

    def test_parse_basic_content(self):
        """Test parsing basic HTML content."""
        html = """
        <html>
            <body>
                <div id="sbo-rt-content">
                    <h1>Chapter Title</h1>
                    <p>Content here</p>
                    <img src="images/fig1.png" width="500" />
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "lxml")
        parser = HTMLParser("123", "https://example.com", [], [])

        _page_css, xhtml = parser.parse(soup)

        assert "Chapter Title" in xhtml
        assert "Content here" in xhtml
        # Link should be rewritten
        assert "Images/fig1.png" in xhtml
        # Width attribute should be removed
        assert 'width="500"' not in xhtml


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
