"""Application configuration with Pydantic Settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SafariBooksConfig(BaseSettings):
    """Application configuration with environment variable support.

    Configuration can be set via:
    1. Environment variables (prefixed with SAFARIBOOKS_)
    2. .env file
    3. Direct instantiation

    Example:
        export SAFARIBOOKS_OUTPUT_DIR=/path/to/books
        export SAFARIBOOKS_LOG_LEVEL=DEBUG

        config = SafariBooksConfig()
        print(config.output_dir)  # /path/to/books
    """

    model_config = SettingsConfigDict(
        env_prefix="SAFARIBOOKS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Paths
    output_dir: Path = Field(
        default=Path("./Books"), description="Output directory for downloaded EPUB files"
    )
    cookies_file: Path = Field(
        default=Path("./cookies.json"), description="Path to cookies.json file for authentication"
    )

    # API settings
    base_url: str = Field(
        default="https://learning.oreilly.com", description="O'Reilly Learning Platform base URL"
    )
    api_url: str = Field(default="https://api.oreilly.com", description="O'Reilly API base URL")
    timeout: int = Field(default=30, ge=1, le=300, description="HTTP request timeout in seconds")
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retry attempts for failed requests"
    )

    # Download settings
    kindle_mode: bool = Field(
        default=False, description="Enable Kindle compatibility mode (CSS fixes)"
    )
    concurrent_downloads: int = Field(
        default=5, ge=1, le=20, description="Number of concurrent download workers"
    )

    # Logging
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Path | None = Field(default=None, description="Optional log file path")
    use_new_client: bool = Field(
        default=False, description="Use new async HTTP client (experimental)"
    )
    use_new_parser: bool = Field(default=False, description="Use new modular parser (experimental)")
    use_new_builder: bool = Field(default=False, description="Use new EPUB builder (experimental)")

    def validate_paths(self) -> None:
        """Validate and create necessary paths."""
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check if cookies file exists
        if not self.cookies_file.exists():
            raise FileNotFoundError(
                f"Cookies file not found: {self.cookies_file}\n"
                "Please create cookies.json with your O'Reilly session cookies."
            )
