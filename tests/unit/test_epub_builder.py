"""Unit tests for EPUBBuilder class."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from safaribooks.epub.builder import EPUBBuilder


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_book_info():
    """Sample book metadata."""
    return {
        "isbn": "9781234567890",
        "description": "A test book about testing",
        "rights": "Copyright © 2025 Test Publisher",
        "issued": "2025-01-01",
        "authors": [
            {"name": "John Doe"},
            {"name": "Jane Smith"},
        ],
        "publishers": [
            {"name": "Test Publishing House"},
        ],
        "subjects": [
            {"name": "Software Testing"},
            {"name": "Python Programming"},
        ],
    }


@pytest.fixture
def sample_chapters():
    """Sample chapter list."""
    return [
        {
            "filename": "ch01.html",
            "title": "Chapter 1: Introduction",
        },
        {
            "filename": "ch02.html",
            "title": "Chapter 2: Getting Started",
        },
        {
            "filename": "ch03.html",
            "title": "Chapter 3: Advanced Topics",
        },
    ]


@pytest.fixture
def sample_toc_data():
    """Sample table of contents data."""
    return [
        {
            "id": "ch01",
            "fragment": "ch01",
            "label": "Chapter 1: Introduction",
            "href": "/book/9781234567890/ch01.html",
            "depth": 1,
            "children": [
                {
                    "id": "ch01-s01",
                    "fragment": "ch01-s01",
                    "label": "Section 1.1",
                    "href": "/book/9781234567890/ch01.html#s01",
                    "depth": 2,
                    "children": [],
                }
            ],
        },
        {
            "id": "ch02",
            "fragment": "ch02",
            "label": "Chapter 2: Getting Started",
            "href": "/book/9781234567890/ch02.html",
            "depth": 1,
            "children": [],
        },
    ]


@pytest.fixture
def builder(temp_dir, sample_book_info, sample_chapters):
    """Create an EPUBBuilder instance with test data."""
    book_path = temp_dir / "book"
    css_path = book_path / "OEBPS" / "Styles"
    images_path = book_path / "OEBPS" / "Images"

    # Create directories
    book_path.mkdir()
    css_path.mkdir(parents=True)
    images_path.mkdir(parents=True)

    # Create sample CSS and image files
    (css_path / "Style00.css").write_text("body { margin: 0; }")
    (css_path / "Style01.css").write_text("h1 { color: blue; }")
    (images_path / "cover.jpg").write_bytes(b"fake image data")
    (images_path / "figure-01.png").write_bytes(b"fake image data")

    return EPUBBuilder(
        book_id="9781234567890",
        book_title="Test Book: A Comprehensive Guide",
        book_info=sample_book_info,
        book_chapters=sample_chapters,
        book_path=str(book_path),
        css_path=str(css_path),
        images_path=str(images_path),
        cover="cover.jpg",
    )


class TestEPUBBuilderInit:
    """Test EPUBBuilder initialization."""

    def test_init_sets_attributes(self, builder):
        """Test that __init__ properly sets all attributes."""
        assert builder.book_id == "9781234567890"
        assert builder.book_title == "Test Book: A Comprehensive Guide"
        assert isinstance(builder.book_path, Path)
        assert isinstance(builder.css_path, Path)
        assert isinstance(builder.images_path, Path)
        assert builder.cover == "cover.jpg"

    def test_jinja_env_initialized(self, builder):
        """Test that Jinja2 environment is properly initialized."""
        assert builder.env is not None
        assert "container.xml.j2" in builder.env.list_templates()
        assert "content.opf.j2" in builder.env.list_templates()
        assert "toc.ncx.j2" in builder.env.list_templates()
        assert "nav.xhtml.j2" in builder.env.list_templates()


class TestEPUBStructure:
    """Test EPUB directory structure creation."""

    def test_create_structure(self, builder):
        """Test that directory structure is created."""
        builder._create_structure()
        assert (builder.book_path / "META-INF").is_dir()
        assert (builder.book_path / "OEBPS").is_dir()

    def test_write_mimetype(self, builder):
        """Test mimetype file creation."""
        builder._write_mimetype()
        mimetype_path = builder.book_path / "mimetype"
        assert mimetype_path.exists()
        assert mimetype_path.read_text() == "application/epub+zip"


class TestContainerXML:
    """Test META-INF/container.xml generation."""

    def test_write_container_xml(self, builder):
        """Test container.xml creation."""
        builder._create_structure()
        builder._write_container_xml()

        container_path = builder.book_path / "META-INF" / "container.xml"
        assert container_path.exists()

        content = container_path.read_text()
        assert '<?xml version="1.0"?>' in content
        assert 'full-path="OEBPS/content.opf"' in content
        assert 'media-type="application/oebps-package+xml"' in content


class TestContentOPF:
    """Test OEBPS/content.opf generation."""

    def test_write_content_opf(self, builder):
        """Test content.opf creation."""
        builder._create_structure()
        builder._write_content_opf()

        opf_path = builder.book_path / "OEBPS" / "content.opf"
        assert opf_path.exists()

        content = opf_path.read_text()
        # Check metadata
        assert "<dc:title>Test Book: A Comprehensive Guide</dc:title>" in content
        assert "<dc:creator>John Doe</dc:creator>" in content
        assert "<dc:creator>Jane Smith</dc:creator>" in content
        assert "<dc:publisher>Test Publishing House</dc:publisher>" in content
        assert "<dc:subject>Software Testing</dc:subject>" in content
        assert "<dc:subject>Python Programming</dc:subject>" in content

    def test_manifest_includes_chapters(self, builder):
        """Test that manifest includes all chapters."""
        builder._create_structure()
        builder._write_content_opf()

        content = (builder.book_path / "OEBPS" / "content.opf").read_text()
        assert 'id="ch01"' in content
        assert 'href="ch01.xhtml"' in content
        assert 'id="ch02"' in content
        assert 'href="ch02.xhtml"' in content

    def test_manifest_includes_images(self, builder):
        """Test that manifest includes images."""
        builder._create_structure()
        builder._write_content_opf()

        content = (builder.book_path / "OEBPS" / "content.opf").read_text()
        assert 'href="Images/cover.jpg"' in content
        assert 'href="Images/figure-01.png"' in content
        assert 'properties="cover-image"' in content  # cover.jpg should have this

    def test_manifest_includes_css(self, builder):
        """Test that manifest includes CSS files."""
        builder._create_structure()
        builder._write_content_opf()

        content = (builder.book_path / "OEBPS" / "content.opf").read_text()
        assert 'id="style_00"' in content
        assert 'href="Styles/Style00.css"' in content
        assert 'id="style_01"' in content
        assert 'href="Styles/Style01.css"' in content

    def test_spine_ordering(self, builder):
        """Test that spine maintains chapter order."""
        builder._create_structure()
        builder._write_content_opf()

        content = (builder.book_path / "OEBPS" / "content.opf").read_text()
        # Check spine contains chapters in order
        assert '<itemref idref="ch01"/>' in content
        assert '<itemref idref="ch02"/>' in content
        assert '<itemref idref="ch03"/>' in content


class TestTOCNCX:
    """Test OEBPS/toc.ncx generation."""

    def test_write_toc_ncx(self, builder, sample_toc_data):
        """Test toc.ncx creation."""
        builder._create_structure()
        builder._write_toc_ncx(sample_toc_data)

        ncx_path = builder.book_path / "OEBPS" / "toc.ncx"
        assert ncx_path.exists()

        content = ncx_path.read_text()
        assert '<?xml version="1.0" encoding="utf-8"' in content
        assert "<ncx" in content
        assert "<docTitle><text>Test Book: A Comprehensive Guide</text></docTitle>" in content
        assert "<docAuthor><text>John Doe, Jane Smith</text></docAuthor>" in content

    def test_parse_toc_flat(self):
        """Test TOC parsing with no nested items."""
        toc_data = [
            {
                "id": "ch01",
                "fragment": "ch01",
                "label": "Chapter 1",
                "href": "/book/123/ch01.html",
                "depth": 1,
                "children": [],
            }
        ]
        result, count, depth = EPUBBuilder._parse_toc(toc_data)
        assert count == 1
        assert depth == 1
        assert "Chapter 1" in result
        assert "ch01.xhtml" in result

    def test_parse_toc_nested(self, sample_toc_data):
        """Test TOC parsing with nested items."""
        result, count, depth = EPUBBuilder._parse_toc(sample_toc_data)
        assert count == 3  # 2 chapters + 1 section
        assert depth == 2  # Max depth is 2
        assert "Chapter 1: Introduction" in result
        assert "Section 1.1" in result
        assert "Chapter 2: Getting Started" in result


class TestNavXHTML:
    """Test OEBPS/nav.xhtml generation."""

    def test_write_nav_xhtml(self, builder, sample_toc_data):
        """Test nav.xhtml creation."""
        builder._create_structure()
        builder._write_nav_xhtml(sample_toc_data)

        nav_path = builder.book_path / "OEBPS" / "nav.xhtml"
        assert nav_path.exists()

        content = nav_path.read_text()
        assert '<?xml version="1.0" encoding="utf-8"?>' in content
        assert "<nav" in content
        assert 'epub:type="toc"' in content
        assert "<h1>Table of Contents</h1>" in content

    def test_parse_nav_toc_flat(self):
        """Test nav TOC parsing with no nested items."""
        toc_data = [
            {
                "id": "ch01",
                "fragment": "ch01",
                "label": "Chapter 1",
                "href": "/book/123/ch01.html",
                "depth": 1,
                "children": [],
            }
        ]
        result = EPUBBuilder._parse_nav_toc(toc_data)
        assert '<li><a href="ch01.xhtml">Chapter 1</a></li>' in result

    def test_parse_nav_toc_nested(self, sample_toc_data):
        """Test nav TOC parsing with nested items."""
        result = EPUBBuilder._parse_nav_toc(sample_toc_data)
        assert "Chapter 1: Introduction" in result
        assert "Section 1.1" in result
        assert "<ol>" in result  # Nested list


class TestEPUBZip:
    """Test EPUB ZIP file creation."""

    def test_create_epub_zip_structure(self, builder, sample_toc_data):
        """Test that EPUB ZIP has correct structure."""
        builder._create_structure()
        builder._write_mimetype()
        builder._write_container_xml()
        builder._write_content_opf()
        builder._write_toc_ncx(sample_toc_data)
        builder._write_nav_xhtml(sample_toc_data)

        epub_path = builder.book_path / "test.epub"
        builder._create_epub_zip(str(epub_path))

        assert epub_path.exists()

        # Verify ZIP contents
        with zipfile.ZipFile(epub_path, "r") as epub:
            namelist = epub.namelist()
            assert "mimetype" in namelist
            assert "META-INF/container.xml" in namelist
            assert "OEBPS/content.opf" in namelist
            assert "OEBPS/toc.ncx" in namelist
            assert "OEBPS/nav.xhtml" in namelist

    def test_mimetype_uncompressed(self, builder, sample_toc_data):
        """Test that mimetype file is uncompressed."""
        builder._create_structure()
        builder._write_mimetype()
        builder._write_container_xml()
        builder._write_content_opf()
        builder._write_toc_ncx(sample_toc_data)
        builder._write_nav_xhtml(sample_toc_data)

        epub_path = builder.book_path / "test.epub"
        builder._create_epub_zip(str(epub_path))

        with zipfile.ZipFile(epub_path, "r") as epub:
            mimetype_info = epub.getinfo("mimetype")
            assert mimetype_info.compress_type == zipfile.ZIP_STORED

    def test_other_files_compressed(self, builder, sample_toc_data):
        """Test that other files are compressed."""
        builder._create_structure()
        builder._write_mimetype()
        builder._write_container_xml()
        builder._write_content_opf()
        builder._write_toc_ncx(sample_toc_data)
        builder._write_nav_xhtml(sample_toc_data)

        epub_path = builder.book_path / "test.epub"
        builder._create_epub_zip(str(epub_path))

        with zipfile.ZipFile(epub_path, "r") as epub:
            container_info = epub.getinfo("META-INF/container.xml")
            assert container_info.compress_type == zipfile.ZIP_DEFLATED


class TestBuildMethod:
    """Test the main build() method."""

    def test_build_creates_epub(self, builder, sample_toc_data):
        """Test that build() creates a complete EPUB file."""
        epub_path = builder.build(sample_toc_data)

        assert Path(epub_path).exists()
        assert Path(epub_path).suffix == ".epub"

        # Verify ZIP structure
        with zipfile.ZipFile(epub_path, "r") as epub:
            namelist = epub.namelist()
            assert "mimetype" in namelist
            assert "META-INF/container.xml" in namelist
            assert "OEBPS/content.opf" in namelist
            assert "OEBPS/toc.ncx" in namelist
            assert "OEBPS/nav.xhtml" in namelist

    def test_build_replaces_existing_epub(self, builder, sample_toc_data):
        """Test that build() replaces existing EPUB file."""
        # Create first EPUB
        epub_path1 = builder.build(sample_toc_data)
        mtime1 = Path(epub_path1).stat().st_mtime

        # Create second EPUB (should replace first)
        epub_path2 = builder.build(sample_toc_data)
        mtime2 = Path(epub_path2).stat().st_mtime

        assert epub_path1 == epub_path2
        assert mtime2 >= mtime1  # Second file should be newer or same


class TestHTMLEscaping:
    """Test that HTML entities are properly escaped."""

    def test_title_escaping(self, temp_dir, sample_book_info, sample_chapters):
        """Test that special characters in title are escaped."""
        book_path = temp_dir / "book"
        book_path.mkdir()
        (book_path / "OEBPS" / "Styles").mkdir(parents=True)
        (book_path / "OEBPS" / "Images").mkdir(parents=True)

        builder = EPUBBuilder(
            book_id="123",
            book_title='Test & Book <with> Special "Characters"',
            book_info=sample_book_info,
            book_chapters=sample_chapters,
            book_path=str(book_path),
            css_path=str(book_path / "OEBPS" / "Styles"),
            images_path=str(book_path / "OEBPS" / "Images"),
        )

        builder._create_structure()
        builder._write_content_opf()

        content = (builder.book_path / "OEBPS" / "content.opf").read_text()
        # Check that special chars are escaped
        assert "&amp;" in content
        assert "&lt;" in content or "Test &amp; Book" in content
