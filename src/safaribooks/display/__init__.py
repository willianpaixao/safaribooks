"""
Rich-based display system for SafariBooks.

This module provides beautiful, modern terminal output using the Rich library,
including progress bars, tables, and formatted text.
"""

from .constants import EMOJI_MAP, STYLES
from .rich_display import RichDisplay
from .rich_logger import EmojiLoggerAdapter, setup_rich_logger


__all__ = [
    "EMOJI_MAP",
    "STYLES",
    "EmojiLoggerAdapter",
    "RichDisplay",
    "setup_rich_logger",
]
