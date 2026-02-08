# SafariBooks

Download and generate *EPUB* files from [O'Reilly Learning Platform](https://learning.oreilly.com) (formerly Safari Books Online).

**⚠️ Disclaimer**: This tool is for *personal* and *educational* purposes only. Please read [O'Reilly's Terms of Service](https://learning.oreilly.com/terms/) before use.

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/willianpaixao/safaribooks.git
cd safaribooks
pip install -e .

# 2. Extract cookies from your browser (see Cookie Setup below)
# Save them to cookies.json

# 3. Download a book
python safaribooks.py download --book-id 9781492052197

# Or check if cookies are valid first
python safaribooks.py check-cookies
```

---

## Requirements & Setup

### System Requirements

- **Python**: 3.11 or higher
- **pip**: Latest version recommended
- **Operating Systems**: Linux, macOS, Windows

### Installation

```bash
git clone https://github.com/willianpaixao/safaribooks.git
cd safaribooks
pip install -e .
```

---

## Cookie Setup

1. Log in to https://learning.oreilly.com in your browser
2. Open Developer Tools (F12)
3. Go to "Application" tab → "Cookies" → "https://learning.oreilly.com"
4. Copy all cookies and create `cookies.json`:

```json
[
  {
    "name": "orm-jwt",
    "value": "your-jwt-token-here"
  },
  {
    "name": "BrowserCookie",
    "value": "your-cookie-here"
  }
]
```

### Verify Your Cookies

```bash
python safaribooks.py check-cookies
```

**⚠️ Security Note**: The `cookies.json` file contains your session token. Keep it private and don't commit it to version control.

---

## Usage

### Finding the Book ID

The Book ID is in the URL:
```
https://learning.oreilly.com/library/view/book-name/9781492052197/
                                                    └─────┬──────┘
                                                       Book ID
```

### Basic Commands

```bash
# Download a single book
python safaribooks.py download --book-id 9781492052197

# Download multiple books
python safaribooks.py download -b 9781492052197 -b 9781491958698

# Download with Kindle optimization
python safaribooks.py download --book-id 9781492052197 --kindle

# Custom output directory
python safaribooks.py download --book-id 9781492052197 --output-dir ~/Books

# Enable debug logging to a file
python safaribooks.py download --book-id 9781492052197 --log-level debug --log-file safaribooks.log

# Quiet mode (no output except errors)
python safaribooks.py download --book-id 9781492052197 --quiet

# Check cookies validity
python safaribooks.py check-cookies

# Display version
python safaribooks.py version

# Get help
python safaribooks.py --help
python safaribooks.py download --help
```

### Command Reference

```bash
Usage: safaribooks.py [OPTIONS] COMMAND [ARGS]...

Commands:
  download       Download books from O'Reilly Learning
  check-cookies  Verify that cookies.json exists and is valid
  version        Display the version of SafariBooks

Options:
  --help  Show this message and exit.
```

#### Download Command

```bash
Usage: safaribooks.py download [OPTIONS]

Options:
  -b, --book-id BOOK_ID       Book ID(s) to download (required, repeatable)
  --kindle                    Optimize CSS for Kindle e-readers
  --log-file FILE             Write log output to a file (disabled by default)
  --log-level [debug|info|warning|error|critical]
                              Set logging level (default: INFO)
  -o, --output-dir DIRECTORY  Directory to save books (default: Books/)
  -q, --quiet                 Suppress all output except errors (useful for scripts)
  --help                      Show this help message
```

---

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, testing, code quality, and project structure.
