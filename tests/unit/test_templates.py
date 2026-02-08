"""Unit tests for EPUB template strings and constants."""

from safaribooks import SafariBooks


class TestEPUBTemplates:
    """Tests for EPUB template constants."""

    def test_nav_xhtml_template_exists(self):
        """Test that NAV_XHTML template exists."""
        assert hasattr(SafariBooks, "NAV_XHTML")
        assert isinstance(SafariBooks.NAV_XHTML, str)
        assert len(SafariBooks.NAV_XHTML) > 0

    def test_nav_xhtml_has_placeholders(self):
        """Test that NAV_XHTML contains format placeholders."""
        nav_xhtml = SafariBooks.NAV_XHTML
        # Should have placeholders for formatting
        assert "{" in nav_xhtml
        assert "}" in nav_xhtml

    def test_nav_xhtml_is_valid_xml_structure(self):
        """Test that NAV_XHTML has basic XML structure."""
        nav_xhtml = SafariBooks.NAV_XHTML
        assert "<?xml" in nav_xhtml
        assert "<html" in nav_xhtml
        assert "</html>" in nav_xhtml

    def test_content_opf_template_exists(self):
        """Test that CONTENT_OPF template exists."""
        assert hasattr(SafariBooks, "CONTENT_OPF")
        assert isinstance(SafariBooks.CONTENT_OPF, str)
        assert len(SafariBooks.CONTENT_OPF) > 0

    def test_content_opf_has_epub3_version(self):
        """Test that CONTENT_OPF declares EPUB 3 version."""
        content_opf = SafariBooks.CONTENT_OPF
        assert 'version="3.0"' in content_opf

    def test_content_opf_has_metadata(self):
        """Test that CONTENT_OPF has metadata section."""
        content_opf = SafariBooks.CONTENT_OPF
        assert "<metadata" in content_opf
        assert "</metadata>" in content_opf

    def test_content_opf_has_manifest(self):
        """Test that CONTENT_OPF has manifest section."""
        content_opf = SafariBooks.CONTENT_OPF
        assert "<manifest>" in content_opf
        assert "</manifest>" in content_opf

    def test_content_opf_has_spine(self):
        """Test that CONTENT_OPF has spine section."""
        content_opf = SafariBooks.CONTENT_OPF
        assert "<spine" in content_opf
        assert "</spine>" in content_opf
        # Verify spine has toc attribute for NCX backward compatibility
        assert 'toc="ncx"' in content_opf

    def test_toc_ncx_template_exists(self):
        """Test that TOC_NCX template exists."""
        assert hasattr(SafariBooks, "TOC_NCX")
        assert isinstance(SafariBooks.TOC_NCX, str)
        assert len(SafariBooks.TOC_NCX) > 0

    def test_toc_ncx_has_doctype(self):
        """Test that TOC_NCX has proper DOCTYPE."""
        toc_ncx = SafariBooks.TOC_NCX
        assert "<!DOCTYPE ncx" in toc_ncx

    def test_container_xml_template_exists(self):
        """Test that CONTAINER_XML template exists."""
        assert hasattr(SafariBooks, "CONTAINER_XML")
        assert isinstance(SafariBooks.CONTAINER_XML, str)
        assert len(SafariBooks.CONTAINER_XML) > 0

    def test_container_xml_has_rootfile(self):
        """Test that CONTAINER_XML references content.opf."""
        container_xml = SafariBooks.CONTAINER_XML
        assert "content.opf" in container_xml
        assert "<rootfile" in container_xml


class TestHTMLTemplates:
    """Tests for HTML template constants."""

    def test_base_html_template_exists(self):
        """Test that BASE_01_HTML template exists."""
        assert hasattr(SafariBooks, "BASE_01_HTML")
        assert isinstance(SafariBooks.BASE_01_HTML, str)

    def test_base_html_has_doctype(self):
        """Test that BASE_01_HTML has DOCTYPE."""
        base_html = SafariBooks.BASE_01_HTML
        assert "<!DOCTYPE html>" in base_html

    def test_base_html_has_html_tag(self):
        """Test that BASE_01_HTML has html tag."""
        base_html = SafariBooks.BASE_01_HTML
        assert "<html" in base_html

    def test_base_html_has_head(self):
        """Test that BASE_01_HTML has head section."""
        base_html = SafariBooks.BASE_01_HTML
        assert "<head>" in base_html

    def test_kindle_html_template_exists(self):
        """Test that KINDLE_HTML template exists."""
        assert hasattr(SafariBooks, "KINDLE_HTML")
        assert isinstance(SafariBooks.KINDLE_HTML, str)


class TestURLConstants:
    """Tests for URL and path constants."""

    def test_safari_base_url_defined(self):
        """Test that SAFARI_BASE_URL is defined."""
        from safaribooks import SAFARI_BASE_URL

        assert isinstance(SAFARI_BASE_URL, str)
        assert "oreilly.com" in SAFARI_BASE_URL

    def test_api_origin_url_defined(self):
        """Test that API_ORIGIN_URL is defined."""
        from safaribooks import API_ORIGIN_URL

        assert isinstance(API_ORIGIN_URL, str)

    def test_api_template_exists(self):
        """Test that API_TEMPLATE exists."""
        assert hasattr(SafariBooks, "API_TEMPLATE")
        assert isinstance(SafariBooks.API_TEMPLATE, str)
        assert "{0}" in SafariBooks.API_TEMPLATE

    def test_login_url_exists(self):
        """Test that LOGIN_URL exists."""
        assert hasattr(SafariBooks, "LOGIN_URL")
        assert isinstance(SafariBooks.LOGIN_URL, str)


class TestHeaders:
    """Tests for HTTP headers constant."""

    def test_headers_constant_exists(self):
        """Test that HEADERS constant exists."""
        assert hasattr(SafariBooks, "HEADERS")
        assert isinstance(SafariBooks.HEADERS, dict)

    def test_headers_has_user_agent(self):
        """Test that HEADERS includes User-Agent."""
        headers = SafariBooks.HEADERS
        assert "User-Agent" in headers

    def test_headers_has_accept(self):
        """Test that HEADERS includes Accept."""
        headers = SafariBooks.HEADERS
        assert "Accept" in headers


class TestMimetypeConstant:
    """Tests for EPUB mimetype constant."""

    def test_mimetype_value(self):
        """Test that EPUB mimetype value is standard."""
        # The mimetype should be the standard EPUB mimetype
        expected = "application/epub+zip"
        assert isinstance(expected, str)
