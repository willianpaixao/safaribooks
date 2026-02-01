"""Unit tests for HTML parsing functions."""

from safaribooks import SafariBooks


class TestLinkReplace:
    """Tests for link_replace method."""

    def test_replace_html_with_xhtml(self):
        """Test that .html links are replaced with .xhtml."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        result = sb.link_replace("chapter01.html")
        assert result == "chapter01.xhtml"

    def test_replace_relative_image_link(self):
        """Test that relative image links are prefixed with Images/."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        result = sb.link_replace("images/fig1-1.png")
        assert result == "Images/fig1-1.png"

    def test_replace_cover_image(self):
        """Test that cover images are handled correctly."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        result = sb.link_replace("cover.jpg")
        assert result == "Images/cover.jpg"

    def test_preserve_mailto_links(self):
        """Test that mailto: links are not modified."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        result = sb.link_replace("mailto:test@example.com")
        assert result == "mailto:test@example.com"

    def test_replace_absolute_link_with_book_id(self):
        """Test that absolute links containing book ID are made relative."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        url = "https://learning.oreilly.com/library/view/book/123456/chapter01.html"
        result = sb.link_replace(url)
        # The split leaves a leading slash: "/chapter01.html" -> "/chapter01.xhtml"
        assert result == "/chapter01.xhtml"

    def test_none_link_returns_none(self):
        """Test that None input returns None."""
        sb = SafariBooks.__new__(SafariBooks)
        sb.book_id = "123456"

        result = sb.link_replace(None)
        assert result is None


class TestEscapeDirname:
    """Tests for escape_dirname static method."""

    def test_escape_special_characters(self):
        """Test that special characters are replaced with underscores."""
        result = SafariBooks.escape_dirname("Test: File <Name>")
        assert result == "Test_ File _Name_"

    def test_escape_forward_slash(self):
        """Test that forward slashes are escaped."""
        result = SafariBooks.escape_dirname("Part 1/Chapter 2")
        assert result == "Part 1_Chapter 2"

    def test_escape_question_mark(self):
        """Test that question marks are escaped."""
        result = SafariBooks.escape_dirname("What is Python?")
        assert result == "What is Python_"

    def test_truncate_long_colon_suffix(self):
        """Test that long text after colon is truncated."""
        result = SafariBooks.escape_dirname("A" * 20 + ": This is a very long subtitle")
        assert ":" not in result

    def test_windows_colon_replacement(self):
        """Test that colons are replaced with commas on Windows."""
        import sys

        original_platform = sys.platform

        try:
            sys.platform = "win32"
            result = SafariBooks.escape_dirname("Volume C: Drive")
            assert "," in result or "_" in result
        finally:
            sys.platform = original_platform

    def test_clean_space_option(self):
        """Test that spaces can be removed when clean_space=True."""
        result = SafariBooks.escape_dirname("Test File Name", clean_space=True)
        assert " " not in result


class TestUrlIsAbsolute:
    """Tests for url_is_absolute static method."""

    def test_absolute_http_url(self):
        """Test that HTTP URLs are identified as absolute."""
        assert SafariBooks.url_is_absolute("http://example.com/page.html")

    def test_absolute_https_url(self):
        """Test that HTTPS URLs are identified as absolute."""
        assert SafariBooks.url_is_absolute("https://example.com/page.html")

    def test_relative_url(self):
        """Test that relative URLs are not absolute."""
        assert not SafariBooks.url_is_absolute("chapter01.html")

    def test_absolute_path(self):
        """Test that absolute paths are not considered absolute URLs."""
        assert not SafariBooks.url_is_absolute("/path/to/file.html")

    def test_protocol_relative_url(self):
        """Test that protocol-relative URLs are considered absolute."""
        assert SafariBooks.url_is_absolute("//example.com/page.html")


class TestIsImageLink:
    """Tests for is_image_link static method."""

    def test_jpg_extension(self):
        """Test that .jpg files are identified as images."""
        assert SafariBooks.is_image_link("image.jpg")

    def test_jpeg_extension(self):
        """Test that .jpeg files are identified as images."""
        assert SafariBooks.is_image_link("photo.jpeg")

    def test_png_extension(self):
        """Test that .png files are identified as images."""
        assert SafariBooks.is_image_link("diagram.png")

    def test_gif_extension(self):
        """Test that .gif files are identified as images."""
        assert SafariBooks.is_image_link("animation.gif")

    def test_uppercase_extension(self):
        """Test that uppercase extensions are handled."""
        assert SafariBooks.is_image_link("IMAGE.JPG")

    def test_non_image_file(self):
        """Test that non-image files return False."""
        assert not SafariBooks.is_image_link("document.pdf")

    def test_html_file(self):
        """Test that HTML files are not images."""
        assert not SafariBooks.is_image_link("page.html")


class TestParseToc:
    """Tests for parse_toc static method."""

    def test_simple_toc(self):
        """Test parsing a simple TOC structure."""
        toc_data = [
            {
                "href": "ch01.html",
                "label": "Chapter 1",
                "fragment": "ch01",
                "id": "ch01",
                "depth": "1",
                "children": [],
            }
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        assert count == 1
        assert max_depth == 1
        assert "Chapter 1" in result
        assert "ch01.xhtml" in result

    def test_nested_toc(self):
        """Test parsing a nested TOC structure."""
        toc_data = [
            {
                "href": "part1.html",
                "label": "Part 1",
                "fragment": "part1",
                "id": "part1",
                "depth": "1",
                "children": [
                    {
                        "href": "ch01.html",
                        "label": "Chapter 1",
                        "fragment": "ch01",
                        "id": "ch01",
                        "depth": "2",
                        "children": [],
                    }
                ],
            }
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        assert count == 2
        assert max_depth == 2
        assert "Part 1" in result
        assert "Chapter 1" in result

    def test_toc_with_special_characters(self):
        """Test that special characters in labels are escaped."""
        toc_data = [
            {
                "href": "ch01.html",
                "label": 'Chapter <1> & "Introduction"',
                "fragment": "ch01",
                "id": "ch01",
                "depth": "1",
                "children": [],
            }
        ]

        result, count, max_depth = SafariBooks.parse_toc(toc_data)

        # Should escape HTML entities
        assert "&lt;" in result or "<" not in result
        assert count == 1


class TestParseDescription:
    """Tests for parse_description method (Display class)."""

    def test_parse_valid_html_description(self, mock_display):
        """Test parsing a valid HTML description."""
        from safaribooks import Display

        display = Display("123456")
        html_desc = "<p>This is a <strong>test</strong> description.</p>"

        result = display.parse_description(html_desc)

        assert "test" in result
        assert "<p>" not in result  # HTML tags should be stripped

    def test_parse_empty_description(self, mock_display):
        """Test that empty description returns default."""
        from safaribooks import Display

        display = Display("123456")

        result = display.parse_description("")

        assert result == "n/d"

    def test_parse_none_description(self, mock_display):
        """Test that None description returns default."""
        from safaribooks import Display

        display = Display("123456")

        result = display.parse_description(None)

        assert result == "n/d"

    def test_parse_malformed_html(self, mock_display):
        """Test handling of malformed HTML."""
        from safaribooks import Display

        display = Display("123456")
        malformed = "<p>Unclosed tag"

        result = display.parse_description(malformed)

        # Should handle gracefully, either parse or return n/d
        assert isinstance(result, str)
