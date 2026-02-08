# Changelog

All notable changes to SafariBooks will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-07

### Added
- **Click-based CLI** with subcommands: `download`, `check-cookies`, `version`
- **Rich terminal display** with concurrent progress bars, download speed, and ETA
- **Async HTTP client** (httpx) with automatic retry and exponential backoff
- **Modular HTML parser** with CSS exclusion rules and code block formatting fixes
- **Jinja2-based EPUB builder** producing EPUB 3.3 compliant output
- **Pydantic data models** for API responses and configuration
- `--log-file FILE` flag to write logs to a file (logging is off by default)
- `--output-dir DIR` / `-o` flag to choose where books are saved (default: `Books`)
- `--quiet` / `-q` flag to suppress all terminal output except errors
- `--kindle` flag to optimize CSS for Kindle e-readers
- Input validation for book IDs (must be numeric, warns on non-standard lengths)
- 180+ unit and integration tests

### Changed

### Removed

### Fixed

[2.0.0]: https://github.com/willianpaixao/safaribooks/releases/tag/v2.0.0
