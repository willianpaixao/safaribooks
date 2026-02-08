"""Rich-based logger configuration for SafariBooks."""

import logging
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

from .constants import EMOJI_MAP, LOG_FORMAT


def setup_rich_logger(
    name: str,
    level: int = logging.INFO,
    show_time: bool = True,
    show_path: bool = False,
) -> logging.Logger:
    """
    Set up a Rich-based logger with emoji support.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        show_time: Show timestamp in logs
        show_path: Show file path in logs

    Returns:
        Configured logger instance
    """
    console = Console(stderr=True)

    # Create Rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=show_time,
        show_path=show_path,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
    )

    # Configure handler
    rich_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Clear any existing handlers
    logger.addHandler(rich_handler)

    return logger


class EmojiLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """
    Logger adapter that adds emojis to log messages.

    Usage:
        logger = setup_rich_logger("SafariBooks")
        emoji_logger = EmojiLoggerAdapter(logger, {})
        emoji_logger.info("Starting download", extra={"emoji": "download"})
    """

    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        """Add emoji prefix to messages based on level or extra data."""
        # Check for explicit emoji in extra
        extra = kwargs.get("extra", {})
        emoji_key = extra.pop("emoji", None) if isinstance(extra, dict) else None

        # Determine emoji
        if emoji_key and emoji_key in EMOJI_MAP:
            emoji = EMOJI_MAP[emoji_key]
        else:
            # Use level-based emoji
            levelno = kwargs.get("levelno", self.logger.level)
            if levelno >= logging.CRITICAL:
                emoji = EMOJI_MAP["critical"]
            elif levelno >= logging.ERROR:
                emoji = EMOJI_MAP["error"]
            elif levelno >= logging.WARNING:
                emoji = EMOJI_MAP["warning"]
            elif levelno >= logging.INFO:
                emoji = EMOJI_MAP["info"]
            elif levelno >= logging.DEBUG:
                emoji = EMOJI_MAP["debug"]
            else:
                emoji = ""

        # Add emoji prefix
        if emoji:
            msg = f"{emoji} {msg}"

        return msg, kwargs
