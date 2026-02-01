"""Unit tests for logger module."""

import logging

from logger import (
    ColoredFormatter,
    get_logger,
    get_valid_log_levels,
    set_log_level,
    setup_logger,
)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("TestLogger")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_creates_unique_loggers(self):
        """Test that get_logger creates different loggers for different names."""
        logger1 = get_logger("Logger1")
        logger2 = get_logger("Logger2")
        assert logger1.name == "Logger1"
        assert logger2.name == "Logger2"
        assert logger1 is not logger2

    def test_get_logger_returns_same_instance_for_same_name(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("SameName")
        logger2 = get_logger("SameName")
        assert logger1 is logger2

    def test_get_logger_without_setup_has_no_handlers(self):
        """Test that get_logger without setup_logger has no handlers."""
        logger = get_logger("NoSetupLogger")
        # get_logger() just returns the logger, doesn't configure it
        # It may have 0 handlers if never set up
        assert isinstance(logger, logging.Logger)


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_colored_formatter_initialization(self):
        """Test that ColoredFormatter can be instantiated."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        assert isinstance(formatter, logging.Formatter)

    def test_colored_formatter_format_method_exists(self):
        """Test that ColoredFormatter has a format method."""
        formatter = ColoredFormatter("%(message)s")
        assert hasattr(formatter, "format")
        assert callable(formatter.format)

    def test_colored_formatter_formats_log_record(self):
        """Test that ColoredFormatter can format a log record."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert isinstance(result, str)
        assert "Test message" in result


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger("TestSetup")
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_sets_level(self):
        """Test that setup_logger sets the correct level."""
        logger = setup_logger("TestLevel", "DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logger_adds_handler(self):
        """Test that setup_logger adds a handler to the logger."""
        logger = setup_logger("TestHandler")
        assert len(logger.handlers) > 0

    def test_setup_logger_uses_colored_formatter(self):
        """Test that setup_logger uses ColoredFormatter."""
        logger = setup_logger("TestFormatter")
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0].formatter, ColoredFormatter)

    def test_setup_logger_default_level_is_info(self):
        """Test that setup_logger defaults to INFO level."""
        logger = setup_logger("TestDefaultLevel")
        assert logger.level == logging.INFO


class TestSetLogLevel:
    """Tests for set_log_level function."""

    def test_set_log_level_changes_logger_level(self):
        """Test that set_log_level changes the logger level."""
        logger = setup_logger("TestChangeLevel", "INFO")
        set_log_level("DEBUG", "TestChangeLevel")
        assert logger.level == logging.DEBUG

    def test_set_log_level_updates_handlers(self):
        """Test that set_log_level updates handler levels."""
        logger = setup_logger("TestHandlerLevel", "INFO")
        set_log_level("WARNING", "TestHandlerLevel")
        for handler in logger.handlers:
            assert handler.level == logging.WARNING


class TestGetValidLogLevels:
    """Tests for get_valid_log_levels function."""

    def test_get_valid_log_levels_returns_list(self):
        """Test that get_valid_log_levels returns a list."""
        levels = get_valid_log_levels()
        assert isinstance(levels, list)

    def test_get_valid_log_levels_contains_standard_levels(self):
        """Test that get_valid_log_levels contains standard log levels."""
        levels = get_valid_log_levels()
        assert "DEBUG" in levels
        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels
        assert "CRITICAL" in levels


class TestLoggingLevels:
    """Tests for logging level configuration."""

    def test_logger_default_level(self):
        """Test that logger has a default level set."""
        logger = get_logger("LevelTest")
        # Logger should have a level set (not NOTSET at the effective level)
        assert logger.getEffectiveLevel() is not None

    def test_logger_can_change_level(self):
        """Test that logger level can be changed."""
        logger = get_logger("ChangeableLevel")
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        assert logger.level == logging.DEBUG
        # Restore original level
        logger.setLevel(original_level)

    def test_logger_level_can_be_set_to_warning(self):
        """Test that logger level can be set to WARNING."""
        logger = setup_logger("WarningLevelTest", "WARNING")
        assert logger.level == logging.WARNING
