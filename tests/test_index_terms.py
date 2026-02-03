"""Tests for index term anchor fixing in EPUB generation."""

import pytest
from bs4 import BeautifulSoup

from safaribooks import SafariBooks


class TestIndexTermFix:
    """Test the _fix_index_terms() method."""

    @pytest.fixture
    def mock_safaribooks_instance(self):
        """Create a minimal SafariBooks instance for testing."""
        # Mock the necessary attributes
        instance = SafariBooks.__new__(SafariBooks)
        instance.logger = __import__("logging").getLogger("test")
        return instance

    def test_single_index_term_moves_id_to_parent(self, mock_safaribooks_instance):
        """Test that a single index term's ID is moved to parent paragraph."""
        html = '<p>Some text here.<a data-type="indexterm" id="id123"></a></p>'
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Check that parent paragraph now has the ID
        p = soup.find("p")
        assert p.get("id") == "id123"

        # Check that anchor no longer has the ID
        a = soup.find("a", {"data-type": "indexterm"})
        assert a.get("id") is None

    def test_multiple_index_terms_wrapped_in_spans(self, mock_safaribooks_instance):
        """Test that multiple index terms in one paragraph are wrapped."""
        html = (
            "<p>Text with "
            '<a data-type="indexterm" id="id123"></a> and '
            '<a data-type="indexterm" id="id456"></a> markers.</p>'
        )
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Check both are wrapped in spans
        span123 = soup.find("span", id="id123")
        span456 = soup.find("span", id="id456")
        assert span123 is not None
        assert span456 is not None

        # Check anchors no longer have IDs
        for a in soup.find_all("a", {"data-type": "indexterm"}):
            assert a.get("id") is None

    def test_parent_with_existing_id_wraps_in_span(self, mock_safaribooks_instance):
        """Test that index term is wrapped when parent already has an ID."""
        html = '<p id="existing">Text<a data-type="indexterm" id="id123"></a></p>'
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Parent should keep its original ID
        p = soup.find("p")
        assert p.get("id") == "existing"

        # Index term should be wrapped in span
        span = soup.find("span", id="id123")
        assert span is not None

        # Anchor should not have ID
        a = soup.find("a", {"data-type": "indexterm"})
        assert a.get("id") is None

    def test_index_term_without_id_unchanged(self, mock_safaribooks_instance):
        """Test that index terms without IDs are left unchanged."""
        html = '<p>Text<a data-type="indexterm"></a></p>'
        soup = BeautifulSoup(html, "lxml")

        # Count of anchors before
        anchors_before = len(soup.find_all("a"))

        mock_safaribooks_instance._fix_index_terms(soup)

        # Anchor should still exist
        anchors_after = len(soup.find_all("a"))
        assert anchors_before == anchors_after

    def test_index_term_in_list_item(self, mock_safaribooks_instance):
        """Test that index terms work in list items too."""
        html = '<ul><li>Item text<a data-type="indexterm" id="id789"></a></li></ul>'
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Check ID moved to list item
        li = soup.find("li")
        assert li.get("id") == "id789"

    def test_nested_index_term(self, mock_safaribooks_instance):
        """Test index term inside inline element like <em>."""
        html = '<p>Some <em>emphasized<a data-type="indexterm" id="id999"></a></em> text.</p>'
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Should find block parent (p) and handle appropriately
        # Since it's the only index term, ID goes to paragraph
        p = soup.find("p")
        assert p.get("id") == "id999"

    def test_real_world_example(self, mock_safaribooks_instance):
        """Test with actual HTML structure from O'Reilly books."""
        html = """<p class="pagebreak-before less_space">Regardless of the language you need to use in your software, you can practice object-oriented design. The design principles of encapsulation, modularity, and data abstraction can be applied to any application in nearly any language. The goal is to make the design robust, maintainable, and flexible. We should use all the help we can get from the object-oriented camp.<a contenteditable="false" data-primary="object-oriented programming" data-type="indexterm" id="id432"></a><a contenteditable="false" data-primary="object-oriented programming" data-secondary="object-oriented design" data-type="indexterm" id="id433"></a></p>"""
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Multiple index terms should be wrapped
        span432 = soup.find("span", id="id432")
        span433 = soup.find("span", id="id433")
        assert span432 is not None
        assert span433 is not None

        # Parent paragraph should not get an ID (has multiple index terms)
        p = soup.find("p")
        assert p.get("id") is None

    def test_index_term_in_blockquote(self, mock_safaribooks_instance):
        """Test index term in blockquote element."""
        html = '<blockquote><p>Quote text<a data-type="indexterm" id="id555"></a></p></blockquote>'
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # ID should be on the paragraph
        p = soup.find("p")
        assert p.get("id") == "id555"

    def test_index_term_in_table(self, mock_safaribooks_instance):
        """Test index term in table cell."""
        html = (
            '<table><tr><td>Cell content<a data-type="indexterm" id="id888"></a></td></tr></table>'
        )
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # ID should be on the table cell
        td = soup.find("td")
        assert td.get("id") == "id888"

    def test_multiple_paragraphs_each_with_index_term(self, mock_safaribooks_instance):
        """Test multiple paragraphs, each with one index term."""
        html = """
        <div>
            <p>First paragraph<a data-type="indexterm" id="id100"></a></p>
            <p>Second paragraph<a data-type="indexterm" id="id200"></a></p>
            <p>Third paragraph<a data-type="indexterm" id="id300"></a></p>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")

        mock_safaribooks_instance._fix_index_terms(soup)

        # Each paragraph should have its ID
        paragraphs = soup.find_all("p")
        assert paragraphs[0].get("id") == "id100"
        assert paragraphs[1].get("id") == "id200"
        assert paragraphs[2].get("id") == "id300"

        # No spans should be created
        spans = soup.find_all("span")
        assert len(spans) == 0
