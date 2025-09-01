#!/usr/bin/env python3
# coding: utf-8
"""
Logging configuration module for SafariBooks downloader.
"""
import sys
import logging
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """A custom formatter that adds colors to log messages."""
    
    # Color codes for different platforms
    SH_DEFAULT = "\033[0m" if "win" not in sys.platform else ""
    SH_YELLOW = "\033[33m" if "win" not in sys.platform else ""
    SH_RED = "\033[31m" if "win" not in sys.platform else ""
    SH_BG_RED = "\033[41m" if "win" not in sys.platform else ""
    SH_BG_YELLOW = "\033[43m" if "win" not in sys.platform else ""
    SH_BLUE = "\033[34m" if "win" not in sys.platform else ""
    SH_GREEN = "\033[32m" if "win" not in sys.platform else ""
    
    # Level to color mapping
    LEVEL_COLORS = {
        logging.DEBUG: SH_BLUE,
        logging.INFO: SH_YELLOW,
        logging.WARNING: SH_BG_YELLOW,
        logging.ERROR: SH_BG_RED,
        logging.CRITICAL: SH_BG_RED,
    }
    
    # Level to prefix mapping
    LEVEL_PREFIXES = {
        logging.DEBUG: "[D]",
        logging.INFO: "[*]",
        logging.WARNING: "[-]", 
        logging.ERROR: "[#]",
        logging.CRITICAL: "[!]",
    }
    
    def format(self, record):
        """Format the log record with colors and prefixes."""
        # Get color and prefix for the log level
        color = self.LEVEL_COLORS.get(record.levelno, self.SH_DEFAULT)
        prefix = self.LEVEL_PREFIXES.get(record.levelno, "[?]")
        
        # Create the formatted message
        formatted_time = self.formatTime(record, self.datefmt)
        colored_prefix = f"{color}{prefix}{self.SH_DEFAULT}"
        
        # For error and critical levels, keep the background color for the entire message
        if record.levelno >= logging.ERROR:
            message = f"[{formatted_time}] {color}{prefix} {record.getMessage()}{self.SH_DEFAULT}"
        else:
            message = f"[{formatted_time}] {colored_prefix} {record.getMessage()}"
        
        return message


def setup_logger(name: str = "SafariBooks", level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with the specified name and level.
    
    Args:
        name: The name of the logger
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    # Create formatter
    formatter = ColoredFormatter(
        fmt="[%(asctime)s] %(message)s",
        datefmt="%d/%b/%Y %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = "SafariBooks") -> logging.Logger:
    """
    Get an existing logger or create a new one if it doesn't exist.
    
    Args:
        name: The name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str, logger_name: str = "SafariBooks") -> None:
    """
    Set the log level for an existing logger.
    
    Args:
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: The name of the logger to modify
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(numeric_level)


def get_valid_log_levels() -> list:
    """Return a list of valid log level names."""
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
