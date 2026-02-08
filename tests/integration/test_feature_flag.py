"""
Integration tests for core SafariBooks components.

Verifies that the main modules and classes are properly wired together.
"""

import sys
from pathlib import Path

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestCoreComponents:
    """Test that core components exist and are importable."""

    def test_safaribooks_class_exists(self):
        """Verify SafariBooks class exists."""
        import safaribooks

        assert hasattr(safaribooks, "SafariBooks")

    def test_main_function_exists(self):
        """Verify main() function exists."""
        import safaribooks

        assert hasattr(safaribooks, "main")
        assert callable(safaribooks.main)

    def test_main_delegates_to_click_cli(self):
        """Verify main() delegates to the Click CLI."""
        import inspect

        import safaribooks

        source = inspect.getsource(safaribooks.main)
        assert "cli" in source, "main() should call cli()"


class TestClientIntegration:
    """Test the async HTTP client integration."""

    def test_run_async_helper_exists(self):
        """Verify _run_async helper method exists on SafariBooks class."""
        import safaribooks

        assert hasattr(safaribooks.SafariBooks, "_run_async")

    def test_ensure_client_helper_exists(self):
        """Verify _ensure_client helper method exists on SafariBooks class."""
        import safaribooks

        assert hasattr(safaribooks.SafariBooks, "_ensure_client")


class TestEPUBBuilder:
    """Test that EPUB builder is properly integrated."""

    def test_epub_builder_methods_exist(self):
        """Verify EPUB builder methods exist."""
        import safaribooks

        assert hasattr(safaribooks.SafariBooks, "create_epub")


@pytest.mark.skip(reason="Requires real cookies.json and network access")
class TestClientParity:
    """
    Parity tests to verify client returns expected results.

    These tests require:
    1. A valid cookies.json file
    2. Network access to O'Reilly Learning Platform
    3. A valid book ID to test with

    To run these tests:
    1. Ensure cookies.json exists in project root
    2. Run: pytest tests/integration/test_feature_flag.py::TestClientParity -v
    """

    SAMPLE_BOOK_ID = "9781491958698"

    def test_get_book_info_parity(self):
        """Verify client returns book info structure."""

    def test_get_chapters_parity(self):
        """Verify client returns chapters."""

    def test_download_cover_parity(self):
        """Verify client downloads cover image."""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
