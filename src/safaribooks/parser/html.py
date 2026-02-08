"""HTML parser for O'Reilly Safari book content."""

from pathlib import Path
from random import random
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


# Constants
ANTI_BOT_CHECK_THRESHOLD = 0.8
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "gif"}

# CSS files that should be excluded (known to cause formatting issues)
EXCLUDED_CSS_FILES = {
    "override_v1.css",  # Contains white-space: nowrap !important; which breaks code blocks
}

# CSS fixes for common formatting issues
CSS_FIXES = {
    # Fix: override_v1.css incorrectly sets white-space: nowrap !important
    # This breaks code blocks by forcing one word per line
    r"pre\s*\{\s*white-space:\s*nowrap\s*!important\s*;\s*\}": "pre { white-space: pre-wrap !important; }",
    # Fix: publisher CSS sometimes sets overflow: hidden on containers,
    # which clips images and content that extends beyond the container
    r"overflow\s*:\s*hidden": "overflow: visible",
}


class LinkRewriter:
    """Handles link rewriting for EPUB format."""

    def __init__(self, book_id: str, base_url: str):
        """Initialize link rewriter.

        Args:
            book_id: Book identifier for URL matching
            base_url: Base URL for resolving relative links
        """
        self.book_id = book_id
        self.base_url = base_url

    @staticmethod
    def url_is_absolute(url: str) -> bool:
        """Check if URL is absolute (has a network location/domain).

        Args:
            url: URL string to check

        Returns:
            True if URL has a netloc (e.g., http://example.com), False otherwise
        """
        return bool(urlparse(url).netloc)

    @staticmethod
    def is_image_link(url: str) -> bool:
        """Check if URL points to an image file based on extension.

        Args:
            url: URL or file path to check

        Returns:
            True if file extension is jpg, jpeg, png, or gif (case-insensitive)
        """
        return Path(url).suffix[1:].lower() in SUPPORTED_IMAGE_FORMATS

    def rewrite(self, link: str | None) -> str | None:
        """Replace and transform links for EPUB format.

        Transforms HTML links to XHTML format and reorganizes image paths.

        Args:
            link: URL or link to transform

        Returns:
            Transformed link suitable for EPUB:
            - Images moved to Images/ directory
            - .html extensions changed to .xhtml
            - Book-specific URLs stripped and recursively processed
            - mailto: links preserved unchanged
        """
        if link and not link.startswith("mailto"):
            if not self.url_is_absolute(link):
                if any(x in link for x in ["cover", "images", "graphics"]) or self.is_image_link(
                    link
                ):
                    image = link.split("/")[-1]
                    return "Images/" + image

                return link.replace(".html", ".xhtml")

            if self.book_id in link:
                return self.rewrite(link.split(self.book_id)[-1])

        return link

    def rewrite_links_in_soup(self, soup: Any) -> None:
        """Rewrite all links in BeautifulSoup object.

        Args:
            soup: BeautifulSoup object to process
        """
        # Process all anchor tags
        for tag in soup.find_all("a", href=True):
            tag["href"] = self.rewrite(tag["href"])

        # Process all img tags
        for tag in soup.find_all("img", src=True):
            tag["src"] = self.rewrite(tag["src"])

        # Process all link tags (CSS, etc.)
        for tag in soup.find_all("link", href=True):
            tag["href"] = self.rewrite(tag["href"])


class CoverExtractor:
    """Extracts cover images from HTML content."""

    @staticmethod
    def extract_cover(soup: BeautifulSoup) -> Any:
        """Extract cover image element from HTML.

        Searches for cover image using case-insensitive matching on multiple attributes.
        Checks img tags directly, then images within divs and links with 'cover' in their attributes.

        Args:
            soup: BeautifulSoup parsed HTML document

        Returns:
            BeautifulSoup Tag element if found, None otherwise

        Note:
            Searches for 'cover' (case-insensitive) in:
            - img id, class, name, src, alt attributes
            - div and link container attributes
        """

        # Helper function to check if 'cover' is in any attribute
        def has_cover_in_attrs(tag: Any) -> bool:
            for attr in ["id", "class", "name", "src", "alt"]:
                value = tag.get(attr)
                if value:
                    # Handle both string and list values
                    values = value if isinstance(value, list) else [value]
                    if any("cover" in str(v).lower() for v in values):
                        return True
            return False

        # Try to find img directly with 'cover' in attributes
        for img in soup.find_all("img"):
            if has_cover_in_attrs(img):
                return img

        # Try to find img within div with 'cover' in attributes
        for div in soup.find_all("div"):
            if has_cover_in_attrs(div):
                found_img = div.find("img")
                if found_img is not None:
                    return found_img

        # Try to find img within link with 'cover' in attributes
        for link in soup.find_all("a"):
            if has_cover_in_attrs(link):
                found_img = link.find("img")
                if found_img is not None:
                    return found_img

        return None

    @staticmethod
    def create_cover_page(book_content: Any, cover_image: Any) -> tuple[str, Any]:
        """Create a cover page from cover image.

        Args:
            book_content: Original book content
            cover_image: Cover image element

        Returns:
            Tuple of (cover_css, cover_div) if cover found, ("", book_content) otherwise
        """
        if cover_image is None:
            return "", book_content

        page_css = (
            "<style>"
            "body{display:table;position:absolute;margin:0!important;height:100%;width:100%;}"
            "#Cover{display:table-cell;vertical-align:middle;text-align:center;}"
            "#Cover img{max-height:90vh;max-width:90vw;height:auto;width:auto;margin-left:auto;margin-right:auto;}"
            "</style>"
        )

        # Create a new cover div
        cover_soup = BeautifulSoup('<div id="Cover"></div>', "lxml")
        cover_div = cover_soup.find("div", id="Cover")

        if cover_div is not None:
            # Create img tag and append to cover div
            cover_src = cover_image.get("src")
            if cover_src and isinstance(cover_src, str):
                cover_img = cover_soup.new_tag("img", src=cover_src)
                cover_div.append(cover_img)
                return page_css, cover_div

        return "", book_content


class HTMLParser:
    """Parser for O'Reilly Safari book HTML content."""

    def __init__(
        self,
        book_id: str,
        base_url: str,
        css_list: list[str],
        images_list: list[str],
        chapter_stylesheets: list[str] | None = None,
    ):
        """Initialize HTML parser.

        Args:
            book_id: Book identifier
            base_url: Base URL for resolving relative links
            css_list: List to track CSS files found
            images_list: List to track images found
            chapter_stylesheets: Optional list of chapter-specific stylesheets
        """
        self.book_id = book_id
        self.base_url = base_url
        self.css = css_list
        self.images = images_list
        self.chapter_stylesheets = chapter_stylesheets or []

        # Initialize helper classes
        self.link_rewriter = LinkRewriter(book_id, base_url)
        self.cover_extractor = CoverExtractor()

    def _check_anti_bot_detection(self, soup: BeautifulSoup) -> None:
        """Check for anti-bot detection.

        Args:
            soup: BeautifulSoup object to check

        Raises:
            RuntimeError: If anti-bot detection is detected
        """
        if random() > ANTI_BOT_CHECK_THRESHOLD:
            controls_div = soup.find("div", class_="controls")
            if controls_div and controls_div.find("a"):
                raise RuntimeError("Anti-bot detection detected")

    def _extract_book_content(self, soup: BeautifulSoup) -> Any:
        """Extract the main book content from the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Book content element

        Raises:
            ValueError: If book content is not found
        """
        book_content = soup.find(id="sbo-rt-content")
        if not book_content:
            raise ValueError("Book content not found (missing #sbo-rt-content element)")
        return book_content

    def _process_css_stylesheets(self, soup: BeautifulSoup) -> str:
        """Process all CSS stylesheets and return page CSS HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            HTML string containing CSS link tags and inline styles
        """
        page_css = ""

        # Process chapter stylesheets
        if len(self.chapter_stylesheets):
            for chapter_css_url in self.chapter_stylesheets:
                if chapter_css_url not in self.css:
                    self.css.append(chapter_css_url)

                page_css += (
                    f'<link href="Styles/Style{self.css.index(chapter_css_url):0>2}.css" '
                    'rel="stylesheet" type="text/css" />\n'
                )

        # Process stylesheet links
        stylesheet_links = soup.find_all("link", rel="stylesheet")
        if stylesheet_links:
            for s in stylesheet_links:
                href = s.get("href")
                if not href or not isinstance(href, str):
                    continue

                css_url = (
                    urljoin("https:", href) if href[:2] == "//" else urljoin(self.base_url, href)
                )

                if css_url not in self.css:
                    self.css.append(css_url)

                page_css += (
                    f'<link href="Styles/Style{self.css.index(css_url):0>2}.css" '
                    'rel="stylesheet" type="text/css" />\n'
                )

        # Process inline styles
        stylesheets = soup.find_all("style")
        if stylesheets:
            for css in stylesheets:
                data_template = css.get("data-template")
                if data_template and isinstance(data_template, str):
                    css.string = data_template
                    del css["data-template"]

                css_str = str(css)
                page_css += css_str + "\n"

        return page_css

    def _process_svg_images(self, soup: BeautifulSoup) -> None:
        """Convert SVG image tags to regular img tags.

        Args:
            soup: BeautifulSoup object to process
        """
        svg_image_tags = soup.find_all("image")
        if svg_image_tags:
            for img in svg_image_tags:
                # Find href attribute (could be href, xlink:href, etc.)
                href = img.get("href") or img.get("xlink:href")
                if href and isinstance(href, str):
                    # Get the SVG parent element
                    svg_parent = img.find_parent("g")
                    if svg_parent:
                        svg_root = svg_parent.find_parent()
                        if svg_root:
                            # Create new img tag
                            new_img = soup.new_tag("img", src=href)
                            # Replace the structure
                            svg_parent.decompose()
                            svg_root.append(new_img)

    def _fix_image_dimensions(self, soup: Any) -> None:
        """Remove inline width/height attributes and styles from images.

        O'Reilly's HTML often includes inline width/height attributes or styles
        that override CSS and cause images to overflow the viewport. This method
        removes those attributes to allow our CSS max-width/max-height rules to work.

        Args:
            soup: BeautifulSoup object to process
        """
        for img in soup.find_all("img"):
            # Remove width and height attributes
            if img.get("width"):
                del img["width"]
            if img.get("height"):
                del img["height"]

            # Remove or clean up style attribute if it contains width/height
            style = img.get("style")
            if style and isinstance(style, str):
                # Remove width and height from inline styles
                style_parts = [s.strip() for s in style.split(";") if s.strip()]
                cleaned_parts = [
                    part
                    for part in style_parts
                    if not part.lower().startswith(("width:", "height:", "width ", "height "))
                ]
                if cleaned_parts:
                    img["style"] = "; ".join(cleaned_parts)
                else:
                    del img["style"]

    def _fix_index_terms(self, soup: Any) -> None:
        """Fix index term anchors to be valid EPUB navigation targets.

        Index terms are marked with empty <a> tags that have data-type="indexterm"
        and an ID attribute. Many EPUB readers cannot navigate to these empty
        inline anchors, resulting in "no block found" errors.

        Strategy:
        1. If parent block has no ID and contains only one index term,
           move the ID to the parent element
        2. Otherwise, wrap the anchor in a <span> with the ID

        Args:
            soup: BeautifulSoup object containing the chapter content
        """
        # Find all index term markers
        index_terms = soup.find_all("a", {"data-type": "indexterm"})

        for term in index_terms:
            term_id = term.get("id")
            if not term_id:
                # No ID to fix
                continue

            # Find the nearest block-level parent element
            parent = term.find_parent(["p", "li", "td", "dd", "dt", "div", "section", "blockquote"])
            if not parent:
                # No suitable parent found, leave as-is
                continue

            # Check if we can safely move ID to parent
            parent_id = parent.get("id")
            sibling_index_terms = parent.find_all("a", {"data-type": "indexterm"})

            if not parent_id and len(sibling_index_terms) == 1:
                # Safe to move ID to parent - only one index term and no existing ID
                parent["id"] = term_id

                # Remove ID from anchor since it's now on parent
                del term["id"]

            else:
                # Not safe to move to parent - wrap in span instead
                # This handles cases where:
                # - Parent already has an ID
                # - Multiple index terms in same paragraph

                # Get the root soup object to create new tags
                # Navigate up to find the BeautifulSoup root
                root_soup = term
                while root_soup.parent is not None:
                    root_soup = root_soup.parent

                wrapper = root_soup.new_tag("span", id=term_id)
                term.wrap(wrapper)

                # Remove ID from anchor since it's now on wrapper
                if term.get("id"):
                    del term["id"]

    def parse(self, soup: BeautifulSoup, first_page: bool = False) -> tuple[str, str]:
        """Parse HTML content and extract book content with CSS.

        Args:
            soup: BeautifulSoup parsed HTML document
            first_page: If True, process as cover page

        Returns:
            Tuple of (page_css, xhtml_content)

        Raises:
            RuntimeError: If anti-bot detection is detected
            ValueError: If book content is not found or corrupted
        """
        # Check for anti-bot detection
        self._check_anti_bot_detection(soup)

        # Extract main book content
        book_content = self._extract_book_content(soup)

        # Process CSS stylesheets
        page_css = self._process_css_stylesheets(soup)

        # Process SVG images
        self._process_svg_images(soup)

        # Fix image dimensions (remove inline width/height that override CSS)
        self._fix_image_dimensions(book_content)

        # Rewrite links
        self.link_rewriter.rewrite_links_in_soup(book_content)

        # Fix index term anchors for EPUB reader compatibility
        self._fix_index_terms(book_content)

        # Handle cover page or regular content
        if first_page:
            cover_image = self.cover_extractor.extract_cover(book_content)
            if cover_image:
                cover_css, book_content = self.cover_extractor.create_cover_page(
                    book_content, cover_image
                )
                if cover_css:  # Cover was found and created
                    page_css = cover_css

        xhtml_str = str(book_content)

        return page_css, xhtml_str


def should_exclude_css(css_url: str) -> bool:
    """Check if a CSS file should be excluded based on known issues.

    Args:
        css_url: URL or filename of the CSS file

    Returns:
        True if the CSS file should be excluded, False otherwise
    """
    filename = css_url.split("/")[-1]
    return filename in EXCLUDED_CSS_FILES


def fix_css_content(css_content: str) -> str:
    """Fix known CSS formatting issues.

    Applies regex-based fixes for common CSS problems that break EPUB rendering.

    Args:
        css_content: Raw CSS content as string

    Returns:
        Fixed CSS content
    """
    import re  # noqa: PLC0415

    fixed_content = css_content

    for pattern, replacement in CSS_FIXES.items():
        fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.IGNORECASE)

    return fixed_content
