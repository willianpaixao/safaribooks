"""Constants for Rich display system."""

# Emoji mappings for log levels and operations
EMOJI_MAP = {
    "debug": "🔍",
    "info": "ℹ️",  # noqa: RUF001
    "success": "✓",
    "warning": "⚠️",
    "error": "✗",
    "critical": "🚨",
    "download": "📥",
    "book": "📚",
    "process": "⚙️",
    "chapters": "📥",
    "css": "🎨",
    "images": "🖼️",
    "complete": "✓",
}

# Rich markup styles for different message types
STYLES = {
    "debug": "dim cyan",
    "info": "blue",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "book_title": "bold cyan",
    "book_info": "white",
}

# Log format
LOG_FORMAT = "%(message)s"
DATE_FORMAT = "[%Y-%m-%d %H:%M:%S]"

# Progress bar colors
PROGRESS_COLORS = {
    "complete": "green",
    "finished": "bright_green",
    "in_progress": "cyan",
}
