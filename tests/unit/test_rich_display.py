"""Unit tests for RichDisplay class."""

import pytest

from src.safaribooks.display import RichDisplay


class TestRichDisplay:
    """Test suite for RichDisplay."""

    def test_initialization(self):
        """Test RichDisplay initialization."""
        display = RichDisplay("9781234567890")
        assert display.book_id == "9781234567890"
        assert display.console is not None
        assert display.progress is None
        assert display.output_dir == ""
        assert display.output_dir_set is False

    def test_intro(self, capsys):
        """Test intro() displays ASCII art."""
        display = RichDisplay("test")
        display.intro()
        # Just verify it doesn't crash
        assert True

    def test_book_info(self, capsys):
        """Test book_info() displays metadata."""
        display = RichDisplay("test")
        info = {
            "title": "Test Book",
            "authors": ["John Doe"],
            "publishers": ["Test Publisher"],
            "issued": "2024",
            "isbn": "9781234567890",
        }
        display.book_info(info)
        # Just verify it doesn't crash
        assert True

    def test_progress_system(self):
        """Test multi-task progress system."""
        display = RichDisplay("test")
        display.start_progress(chapters=10, css=5, images=20)

        # Verify progress was started
        assert display.progress is not None
        assert display.task_ids["chapters"] is not None
        assert display.task_ids["css"] is not None
        assert display.task_ids["images"] is not None

        # Update tasks
        display.update_chapters(5)
        display.update_css(2)
        display.update_images(10)

        # Cleanup
        display.finish_progress()
        assert display.progress is None

    def test_state_wrapper(self):
        """Test state() method wrapper."""
        display = RichDisplay("test")
        display.current_task = "chapters"
        display.start_progress(10, 5, 20)

        # Call state wrapper
        display.state(10, 5)

        display.finish_progress()

    def test_set_output_dir(self):
        """Test set_output_dir() method."""
        display = RichDisplay("test")
        display.set_output_dir("/tmp/test")
        assert display.output_dir == "/tmp/test"
        assert display.output_dir_set is True

    def test_error_display(self, capsys):
        """Test error message display."""
        display = RichDisplay("test")
        display.error("Test error message")
        # Just verify it doesn't crash
        assert True

    def test_exit_with_error(self):
        """Test exit_with_error() exits with code 1."""
        display = RichDisplay("test")
        with pytest.raises(SystemExit) as exc_info:
            display.exit_with_error("Fatal error")
        assert exc_info.value.code == 1

    def test_display_attributes(self):
        """Test that Display attributes exist."""
        display = RichDisplay("test")

        # Check all attributes exist
        assert hasattr(display, "output_dir")
        assert hasattr(display, "output_dir_set")
        assert hasattr(display, "columns")
        assert hasattr(display, "book_ad_info")
        assert hasattr(display, "css_ad_info")
        assert hasattr(display, "images_ad_info")
        assert hasattr(display, "last_request")
        assert hasattr(display, "in_error")
        assert hasattr(display, "state_status")

    def test_display_methods(self):
        """Test that Display methods exist."""
        display = RichDisplay("test")

        # Check all methods exist
        assert hasattr(display, "set_output_dir")
        assert hasattr(display, "unregister")
        assert hasattr(display, "save_last_request")
        assert hasattr(display, "parse_description")
        assert hasattr(display, "done")
        assert hasattr(display, "info")
        assert hasattr(display, "exit")
        assert hasattr(display, "api_error")

    def test_parse_description(self):
        """Test parse_description() method."""
        display = RichDisplay("test")

        # Test with None
        assert display.parse_description(None) == "n/d"

        # Test with HTML
        html_desc = "<p>Test <b>description</b> here</p>"
        result = display.parse_description(html_desc)
        assert "Test" in result
        assert "description" in result

    def test_quiet_mode(self, capsys):
        """Test that quiet mode suppresses output."""
        # Create display in quiet mode
        display = RichDisplay("test", quiet=True)

        # These should not produce output
        display.intro()
        display.book_info(
            {
                "title": "Test Book",
                "authors": ["Author"],
                "publishers": ["Publisher"],
            }
        )
        display.out("Test message")
        display.log("Test log")
        display.success("Test success")

        # Verify quiet flag is set
        assert display.quiet is True

        # Verify progress is not started
        display.start_progress(chapters=10, css=5, images=20)
        assert display.progress is None  # Should not be created in quiet mode

    def test_normal_mode(self, capsys):
        """Test that normal mode produces output."""
        # Create display in normal mode (quiet=False)
        display = RichDisplay("test", quiet=False)

        # Verify quiet flag is not set
        assert display.quiet is False

        # These should produce output (we're just checking they don't crash)
        display.intro()
        display.book_info(
            {
                "title": "Test Book",
                "authors": ["Author"],
                "publishers": ["Publisher"],
            }
        )

        # Verify progress is started in normal mode
        display.start_progress(chapters=10, css=5, images=20)
        assert display.progress is not None
        display.finish_progress()
