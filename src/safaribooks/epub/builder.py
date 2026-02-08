"""
EPUB Builder module - Responsible for generating EPUB files from book content.
"""

import os
import zipfile
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class EPUBBuilder:
    """
    Builds EPUB 3.0 files from book metadata and content.

    This class handles:
    - Rendering EPUB metadata files (content.opf, toc.ncx, nav.xhtml)
    - Creating proper EPUB ZIP structure
    - Managing TOC (Table of Contents) generation
    """

    def __init__(
        self,
        book_id: str,
        book_title: str,
        book_info: dict[str, Any],
        book_chapters: list[dict[str, Any]],
        book_path: str,
        css_path: str,
        images_path: str,
        cover: str | None = None,
    ):
        """
        Initialize the EPUB builder.

        Args:
            book_id: Unique book identifier (ISBN or O'Reilly ID)
            book_title: Book title
            book_info: Complete book metadata dict
            book_chapters: List of chapter dicts with filename, title, etc.
            book_path: Path to book output directory
            css_path: Path to CSS files directory
            images_path: Path to images directory
            cover: Cover image filename (optional)
        """
        self.book_id = book_id
        self.book_title = book_title
        self.book_info = book_info
        self.book_chapters = book_chapters
        self.book_path = Path(book_path)
        self.css_path = Path(css_path)
        self.images_path = Path(images_path)
        self.cover = cover

        # Initialize Jinja2 template environment
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(enabled_extensions=("xml", "xhtml", "j2")),
        )

        # File lists (populated during build)
        self.css_files: list[str] = []
        self.image_files: list[str] = []

    def build(self, toc_data: list[dict[str, Any]]) -> str:
        """
        Build the complete EPUB file.

        Args:
            toc_data: Table of contents data from API

        Returns:
            Path to the generated .epub file
        """
        # Create directory structure
        self._create_structure()

        # Generate and write metadata files
        self._write_mimetype()
        self._write_container_xml()
        self._write_content_opf()
        self._write_toc_ncx(toc_data)
        self._write_nav_xhtml(toc_data)

        # Create final EPUB ZIP
        epub_path = self.book_path / f"{self.book_id}.epub"
        if epub_path.exists():
            epub_path.unlink()

        self._create_epub_zip(str(epub_path))
        return str(epub_path)

    def _create_structure(self) -> None:
        """Create EPUB directory structure if needed."""
        meta_info = self.book_path / "META-INF"
        if not meta_info.is_dir():
            meta_info.mkdir(parents=True, exist_ok=True)

        oebps = self.book_path / "OEBPS"
        if not oebps.is_dir():
            oebps.mkdir(parents=True, exist_ok=True)

    def _write_mimetype(self) -> None:
        """Write the mimetype file (must be uncompressed in final ZIP)."""
        (self.book_path / "mimetype").write_text("application/epub+zip")

    def _write_container_xml(self) -> None:
        """Write META-INF/container.xml."""
        template = self.env.get_template("container.xml.j2")
        content = template.render()
        (self.book_path / "META-INF" / "container.xml").write_bytes(
            content.encode("utf-8", "xmlcharrefreplace")
        )

    def _write_content_opf(self) -> None:
        """Write OEBPS/content.opf with book metadata and manifest."""
        # Scan for CSS and image files
        self.css_files = next(os.walk(self.css_path))[2] if self.css_path.exists() else []
        self.image_files = next(os.walk(self.images_path))[2] if self.images_path.exists() else []

        # Build manifest and spine
        manifest_items = self._build_manifest()
        spine_items = self._build_spine()

        # Build authors and subjects
        authors = "\n".join(
            "<dc:creator>{0}</dc:creator>".format(escape(aut.get("name", "n/d")))
            for aut in self.book_info.get("authors", [])
        )

        subjects = "\n".join(
            "<dc:subject>{0}</dc:subject>".format(escape(sub.get("name", "n/d")))
            for sub in self.book_info.get("subjects", [])
        )

        # EPUB 3 requires dcterms:modified timestamp
        modified_timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Get cover URL (first chapter)
        cover_url = (
            self.book_chapters[0]["filename"].replace(".html", ".xhtml")
            if self.book_chapters
            else "cover.xhtml"
        )

        # Render template
        template = self.env.get_template("content.opf.j2")
        content = template.render(
            isbn=self.book_info.get("isbn", self.book_id),
            title=self.book_title,  # Jinja2 will auto-escape
            authors=authors,  # Already contains escaped XML
            description=self.book_info.get("description", ""),  # Jinja2 will auto-escape
            subjects=subjects,  # Already contains escaped XML
            publisher=", ".join(
                pub.get("name", "") for pub in self.book_info.get("publishers", [])
            ),  # Jinja2 will auto-escape
            rights=self.book_info.get("rights", ""),  # Jinja2 will auto-escape
            date=self.book_info.get("issued", ""),
            manifest="\n".join(manifest_items),  # Already contains escaped XML
            spine="\n".join(spine_items),  # Already contains escaped XML
            cover_url=cover_url,
            modified=modified_timestamp,
        )

        (self.book_path / "OEBPS" / "content.opf").write_bytes(
            content.encode("utf-8", "xmlcharrefreplace")
        )

    def _build_manifest(self) -> list[str]:
        """Build manifest items for content.opf."""
        manifest = []

        # Add chapters
        for chapter in self.book_chapters:
            filename = chapter["filename"].replace(".html", ".xhtml")
            item_id = escape("".join(filename.split(".")[:-1]))
            manifest.append(
                f'<item id="{item_id}" href="{filename}" media-type="application/xhtml+xml" />'
            )

        # Add images
        for img in set(self.image_files):
            dot_split = img.split(".")
            head = "img_" + escape("".join(dot_split[:-1]))
            extension = dot_split[-1]
            # Add properties="cover-image" for the cover image (EPUB 3)
            is_cover = isinstance(self.cover, str) and img in self.cover
            properties_attr = ' properties="cover-image"' if is_cover else ""
            manifest.append(
                '<item id="{0}" href="Images/{1}" media-type="image/{2}"{3} />'.format(
                    head, img, "jpeg" if "jp" in extension else extension, properties_attr
                )
            )

        # Add CSS files
        for css_idx in range(len(self.css_files)):
            manifest.append(
                f'<item id="style_{css_idx:0>2}" href="Styles/Style{css_idx:0>2}.css" media-type="text/css" />'
            )

        return manifest

    def _build_spine(self) -> list[str]:
        """Build spine items (reading order) for content.opf."""
        spine = []
        for chapter in self.book_chapters:
            filename = chapter["filename"].replace(".html", ".xhtml")
            item_id = escape("".join(filename.split(".")[:-1]))
            spine.append(f'<itemref idref="{item_id}"/>')
        return spine

    def _write_toc_ncx(self, toc_data: list[dict[str, Any]]) -> None:
        """Write OEBPS/toc.ncx (NCX table of contents for EPUB 2 compatibility)."""
        navmap, _, max_depth = self._parse_toc(toc_data)

        template = self.env.get_template("toc.ncx.j2")
        content = template.render(
            isbn=self.book_info.get("isbn", self.book_id),
            depth=max_depth,
            title=self.book_title,
            author=", ".join(aut.get("name", "") for aut in self.book_info.get("authors", [])),
            navmap=navmap,
        )

        (self.book_path / "OEBPS" / "toc.ncx").write_bytes(
            content.encode("utf-8", "xmlcharrefreplace")
        )

    def _write_nav_xhtml(self, toc_data: list[dict[str, Any]]) -> None:
        """Write OEBPS/nav.xhtml (EPUB 3 navigation document)."""
        nav_items = self._parse_nav_toc(toc_data)

        template = self.env.get_template("nav.xhtml.j2")
        content = template.render(
            title=self.book_title, nav_items=nav_items
        )  # Jinja2 auto-escapes title

        (self.book_path / "OEBPS" / "nav.xhtml").write_bytes(
            content.encode("utf-8", "xmlcharrefreplace")
        )

    @staticmethod
    def _parse_toc(
        toc_list: list[dict[str, Any]], count: int = 0, max_count: int = 0
    ) -> tuple[str, int, int]:
        """
        Parse TOC data into NCX navMap format (EPUB 2 compatibility).

        Args:
            toc_list: List of TOC items from API
            count: Current play order counter
            max_count: Maximum depth encountered

        Returns:
            Tuple of (navmap_xml, final_count, max_depth)
        """
        result = ""
        for item in toc_list:
            count += 1
            max_count = max(max_count, int(item["depth"]))

            result += (
                '<navPoint id="{}" playOrder="{}">'
                "<navLabel><text>{}</text></navLabel>"
                '<content src="{}"/>'.format(
                    item["fragment"] if len(item["fragment"]) else item["id"],
                    count,
                    escape(item["label"]),
                    item["href"].replace(".html", ".xhtml").split("/")[-1],
                )
            )

            if item["children"]:
                sub_result, count, max_count = EPUBBuilder._parse_toc(
                    item["children"], count, max_count
                )
                result += sub_result

            result += "</navPoint>\n"

        return result, count, max_count

    @staticmethod
    def _parse_nav_toc(toc_list: list[dict[str, Any]]) -> str:
        """
        Parse TOC data into HTML5 nav list items for EPUB 3.

        Args:
            toc_list: List of TOC items from API

        Returns:
            HTML list items as string
        """
        result = ""
        for item in toc_list:
            href = item["href"].replace(".html", ".xhtml").split("/")[-1]
            label = escape(item["label"])
            if item["children"]:
                children_html = EPUBBuilder._parse_nav_toc(item["children"])
                result += f'<li>\n<a href="{href}">{label}</a>\n<ol>\n{children_html}</ol>\n</li>\n'
            else:
                result += f'<li><a href="{href}">{label}</a></li>\n'
        return result

    def _create_epub_zip(self, epub_path: str) -> None:
        """
        Create EPUB ZIP file with proper structure per EPUB 3.3 spec.

        The mimetype file MUST be:
        1. The first file in the archive
        2. Stored uncompressed (ZIP_STORED)
        3. Not have any extra field data

        All other files are compressed with ZIP_DEFLATED for smaller file size.

        Args:
            epub_path: Path where the .epub file should be created
        """
        with zipfile.ZipFile(epub_path, "w") as epub:
            # 1. Add mimetype FIRST, uncompressed, no extra field
            mimetype_path = self.book_path / "mimetype"
            epub.write(str(mimetype_path), "mimetype", compress_type=zipfile.ZIP_STORED)

            # 2. Add all other files with compression
            for root, _dirs, files in os.walk(self.book_path):
                for file in files:
                    if file == "mimetype":
                        continue  # Already added first
                    if file.endswith(".epub"):
                        continue  # Don't include the epub itself

                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.book_path)

                    # Use DEFLATED compression for all other files
                    epub.write(str(file_path), str(arcname), compress_type=zipfile.ZIP_DEFLATED)
