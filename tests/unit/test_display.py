"""Unit tests for Display class in safaribooks module."""

import logging

import pytest

from safaribooks import Display


class TestDisplayInitialization:
    """Tests for Display class initialization."""

    def test_display_can_be_instantiated(self):
        """Test that Display class can be instantiated."""
        display = Display("9781234567890")
        assert display is not None
        assert isinstance(display, Display)

    def test_display_requires_book_id(self):
        """Test that Display requires a book_id parameter."""
        with pytest.raises(TypeError):
            Display()  # type: ignore[call-arg]  # Should fail without book_id

    def test_display_stores_book_id(self):
        """Test that Display stores the book_id."""
        book_id = "9781234567890"
        display = Display(book_id)
        assert display.book_id == book_id

    def test_display_has_output_dir_attribute(self):
        """Test that Display has output_dir attribute."""
        display = Display("9781234567890")
        assert hasattr(display, "output_dir")
        assert hasattr(display, "output_dir_set")


class TestDisplayMethods:
    """Tests for Display class methods."""

    def test_display_has_intro_method(self):
        """Test that Display has an intro method."""
        display = Display("9781234567890")
        assert hasattr(display, "intro")
        assert callable(display.intro)

    def test_display_has_set_output_dir_method(self):
        """Test that Display has a set_output_dir method."""
        display = Display("9781234567890")
        assert hasattr(display, "set_output_dir")
        assert callable(display.set_output_dir)

    def test_display_intro_can_be_called(self, capsys):
        """Test that intro method can be called."""
        display = Display("9781234567890")
        # This should not raise an exception
        display.intro()
        # intro() prints to stdout (not logger), so check captured output
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_display_set_output_dir_stores_path(self, caplog):
        """Test that set_output_dir stores the output directory."""
        display = Display("9781234567890")
        test_path = "/tmp/test_output"
        with caplog.at_level(logging.INFO):
            display.set_output_dir(test_path)
        assert display.output_dir == test_path
        assert display.output_dir_set is True

    def test_display_has_unregister_method(self):
        """Test that Display has an unregister method."""
        display = Display("9781234567890")
        assert hasattr(display, "unregister")
        assert callable(display.unregister)

    def test_display_has_save_last_request_method(self):
        """Test that Display has a save_last_request method."""
        display = Display("9781234567890")
        assert hasattr(display, "save_last_request")
        assert callable(display.save_last_request)

    def test_display_unregister_can_be_called(self):
        """Test that unregister method can be called."""
        display = Display("9781234567890")
        # Should not raise exception
        display.unregister()
        # Unregister should work silently

    def test_display_save_last_request_can_be_called(self, caplog):
        """Test that save_last_request can be called."""
        display = Display("9781234567890")
        with caplog.at_level(logging.DEBUG):
            display.save_last_request()
        # Should complete without error

    def test_display_out_method(self, capsys):
        """Test that out method prints output."""
        display = Display("9781234567890")
        test_message = "Test output message"
        display.out(test_message)
        captured = capsys.readouterr()
        assert test_message in captured.out

    def test_display_parse_description_with_text(self):
        """Test parse_description with plain text."""
        display = Display("9781234567890")
        result = display.parse_description("Simple description")
        assert "Simple description" in result

    def test_display_parse_description_with_html(self):
        """Test parse_description with HTML content."""
        display = Display("9781234567890")
        html_desc = "<p>HTML <b>description</b></p>"
        result = display.parse_description(html_desc)
        # Should strip HTML tags
        assert "description" in result

    def test_display_parse_description_empty(self):
        """Test parse_description with empty string."""
        display = Display("9781234567890")
        result = display.parse_description("")
        assert isinstance(result, str)

    def test_display_parse_description_none(self):
        """Test parse_description with None."""
        display = Display("9781234567890")
        result = display.parse_description(None)
        # Should handle None safely
        assert result is None or isinstance(result, str)


class TestDisplayStaticMethods:
    """Tests for Display static methods."""

    def test_api_error_static_method_exists(self):
        """Test that api_error static method exists."""
        assert hasattr(Display, "api_error")
        assert callable(Display.api_error)

    def test_api_error_with_not_found(self):
        """Test api_error with 'Not found' response."""
        response = {"detail": "Not found"}
        result = Display.api_error(response)
        assert isinstance(result, str)
        assert "API:" in result


class TestDisplayBookInfo:
    """Tests for book_info Display method."""

    def test_state_method_exists(self):
        """Test that state method exists."""
        display = Display("9781234567890")
        assert hasattr(display, "state")
        assert callable(display.state)

    def test_done_method_exists(self):
        """Test that done method exists."""
        display = Display("9781234567890")
        assert hasattr(display, "done")
        assert callable(display.done)

    def test_book_info_method_exists(self):
        """Test that book_info method exists."""
        display = Display("9781234567890")
        assert hasattr(display, "book_info")
        assert callable(display.book_info)


class TestDisplayAttributes:
    """Tests for Display class attributes."""

    def test_display_has_columns_attribute(self):
        """Test that Display has columns attribute."""
        display = Display("9781234567890")
        assert hasattr(display, "columns")
        # Should be a positive integer
        assert isinstance(display.columns, int)
        assert display.columns > 0

    def test_display_has_book_ad_info_attribute(self):
        """Test that Display has book_ad_info attribute."""
        display = Display("9781234567890")
        assert hasattr(display, "book_ad_info")

    def test_display_has_in_error_attribute(self):
        """Test that Display has in_error attribute."""
        display = Display("9781234567890")
        assert hasattr(display, "in_error")
        assert isinstance(display.in_error, bool)

    def test_display_has_last_request_attribute(self):
        """Test that Display has last_request attribute."""
        display = Display("9781234567890")
        assert hasattr(display, "last_request")

    def test_display_output_dir_starts_empty(self):
        """Test that output_dir starts as empty string."""
        display = Display("9781234567890")
        assert display.output_dir == ""
        assert display.output_dir_set is False
