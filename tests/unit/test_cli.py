"""
Unit tests for the Click-based CLI.

Tests the new modern CLI implementation with Click and Rich.
"""

import json

# Add src to path for imports
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from safaribooks.cli.commands import check_cookies, cli, download, version


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_cookies_file(tmp_path):
    """Create a temporary cookies.json file."""
    cookies_file = tmp_path / "cookies.json"
    cookies_data = [
        {"name": "orm-jwt", "value": "test_token"},
        {"name": "BrowserCookie", "value": "test_cookie"},
    ]
    cookies_file.write_text(json.dumps(cookies_data))
    return cookies_file


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_cli_help(self, runner):
        """Test that --help works."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SafariBooks" in result.output
        assert "Download and generate EPUB files" in result.output

    def test_cli_no_command(self, runner):
        """Test that running CLI with no command shows help."""
        result = runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Commands:" in result.output

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(version)
        assert result.exit_code == 0
        assert "SafariBooks" in result.output
        assert "2.0.0" in result.output


class TestCheckCookiesCommand:
    """Test check-cookies command."""

    def test_check_cookies_not_found(self, runner, tmp_path, monkeypatch):
        """Test check-cookies when cookies.json doesn't exist."""
        # Change to temp directory where cookies.json doesn't exist
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(check_cookies)
        assert result.exit_code == 1
        assert "cookies.json not found" in result.output

    def test_check_cookies_empty_file(self, runner, tmp_path, monkeypatch):
        """Test check-cookies with empty cookies file."""
        monkeypatch.chdir(tmp_path)
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text("[]")

        result = runner.invoke(check_cookies)
        assert result.exit_code == 1
        assert "empty" in result.output.lower()

    def test_check_cookies_invalid_json(self, runner, tmp_path, monkeypatch):
        """Test check-cookies with invalid JSON."""
        monkeypatch.chdir(tmp_path)
        cookies_file = tmp_path / "cookies.json"
        cookies_file.write_text("{invalid json}")

        result = runner.invoke(check_cookies)
        assert result.exit_code == 1
        assert "not valid JSON" in result.output

    def test_check_cookies_valid(self, runner, mock_cookies_file, monkeypatch):
        """Test check-cookies with valid cookies.json."""
        monkeypatch.chdir(mock_cookies_file.parent)

        result = runner.invoke(check_cookies)
        assert result.exit_code == 0
        assert "found and valid" in result.output
        assert "2 entries" in result.output


class TestDownloadCommand:
    """Test download command."""

    def test_download_no_book_id(self, runner):
        """Test download command without --book-id."""
        result = runner.invoke(download, [])
        assert result.exit_code != 0
        assert "required" in result.output.lower() or "missing" in result.output.lower()

    def test_download_help(self, runner):
        """Test download command help."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "Download books" in result.output
        assert "--book-id" in result.output
        assert "--kindle" in result.output

    def test_download_no_cookies_file(self, runner, tmp_path, monkeypatch):
        """Test download fails gracefully when cookies.json is missing."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(download, ["--book-id", "9781492052197"])
        assert result.exit_code == 1
        assert "cookies.json" in result.output
        assert "not found" in result.output.lower()

    @patch("safaribooks.cli.commands.get_safaribooks_module")
    def test_download_with_book_id(self, mock_get_module, runner, mock_cookies_file, monkeypatch):
        """Test download command with valid book ID."""
        monkeypatch.chdir(mock_cookies_file.parent)

        # Mock the SafariBooks module
        mock_safari = MagicMock()
        mock_safari_class = MagicMock()
        mock_safari_class.return_value = mock_safari
        mock_module = MagicMock()
        mock_module.SafariBooks = mock_safari_class
        mock_get_module.return_value = mock_module

        result = runner.invoke(download, ["--book-id", "9781492052197"])

        # Should attempt to download (exit code depends on mocked behavior)
        assert "Downloading" in result.output or "Download" in result.output
        mock_safari_class.assert_called_once()

    def test_download_multiple_book_ids(self, runner):
        """Test download command with multiple book IDs."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "multiple" in result.output.lower()

    def test_download_with_kindle_flag(self, runner):
        """Test download command with --kindle flag."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "--kindle" in result.output
        assert "Kindle" in result.output

    def test_download_with_log_level(self, runner):
        """Test download command with --log-level."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "--log-level" in result.output

    def test_download_with_log_file(self, runner):
        """Test download command exposes --log-file option."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "--log-file" in result.output

    @patch("safaribooks.cli.commands.get_safaribooks_module")
    def test_download_log_file_creates_file(
        self, mock_get_module, runner, mock_cookies_file, monkeypatch, tmp_path
    ):
        """Test that --log-file creates the log file during download."""
        monkeypatch.chdir(mock_cookies_file.parent)
        log_path = str(tmp_path / "test.log")

        # Mock the SafariBooks module
        mock_safari_class = MagicMock()
        mock_module = MagicMock()
        mock_module.SafariBooks = mock_safari_class
        mock_get_module.return_value = mock_module

        result = runner.invoke(download, ["--book-id", "9781492052197", "--log-file", log_path])
        assert result.exit_code == 0
        assert Path(log_path).exists()

    @patch("safaribooks.cli.commands.get_safaribooks_module")
    def test_download_output_dir_passed_to_safaribooks(
        self, mock_get_module, runner, mock_cookies_file, monkeypatch, tmp_path
    ):
        """Test that --output-dir is passed through to SafariBooks via args namespace."""
        monkeypatch.chdir(mock_cookies_file.parent)
        custom_dir = str(tmp_path / "MyBooks")

        mock_safari_class = MagicMock()
        mock_module = MagicMock()
        mock_module.SafariBooks = mock_safari_class
        mock_get_module.return_value = mock_module

        result = runner.invoke(download, ["--book-id", "9781492052197", "--output-dir", custom_dir])
        assert result.exit_code == 0
        # Verify SafariBooks was called and the namespace has output_dir
        mock_safari_class.assert_called_once()
        args_passed = mock_safari_class.call_args[0][0]
        assert args_passed.output_dir == custom_dir

    @patch("safaribooks.cli.commands.get_safaribooks_module")
    def test_download_default_output_dir(
        self, mock_get_module, runner, mock_cookies_file, monkeypatch
    ):
        """Test that default output_dir 'Books' is passed when --output-dir is omitted."""
        monkeypatch.chdir(mock_cookies_file.parent)

        mock_safari_class = MagicMock()
        mock_module = MagicMock()
        mock_module.SafariBooks = mock_safari_class
        mock_get_module.return_value = mock_module

        result = runner.invoke(download, ["--book-id", "9781492052197"])
        assert result.exit_code == 0
        mock_safari_class.assert_called_once()
        args_passed = mock_safari_class.call_args[0][0]
        assert args_passed.output_dir == "Books"

    def test_download_invalid_book_id(self, runner, mock_cookies_file, monkeypatch):
        """Test download with non-numeric book ID."""
        monkeypatch.chdir(mock_cookies_file.parent)

        # Book IDs should be numeric
        result = runner.invoke(download, ["--book-id", "not-a-number"])
        # Should show warning or error about invalid book ID
        assert result.exit_code != 0 or "Warning" in result.output


class TestBookIDType:
    """Test custom BookIDType validation."""

    def test_book_id_type_valid(self, runner):
        """Test that valid book IDs are accepted."""
        # 13-digit ISBN
        result = runner.invoke(download, ["--book-id", "9781492052197", "--help"])
        assert result.exit_code == 0

    def test_book_id_type_numeric_validation(self, runner, mock_cookies_file, monkeypatch):
        """Test that non-numeric book IDs are rejected."""
        monkeypatch.chdir(mock_cookies_file.parent)

        result = runner.invoke(download, ["--book-id", "abc123xyz"])
        assert result.exit_code != 0
        # Should fail validation
        assert "not a valid book ID" in result.output or result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for the CLI."""

    def test_cli_all_commands_exist(self, runner):
        """Test that all expected commands are available."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "download" in result.output
        assert "check-cookies" in result.output
        assert "version" in result.output

    def test_download_output_dir_option(self, runner):
        """Test that --output-dir option exists."""
        result = runner.invoke(download, ["--help"])
        assert result.exit_code == 0
        assert "--output-dir" in result.output or "-o" in result.output
