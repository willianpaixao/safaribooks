# SafariBooks

Download and generate *EPUB* files from [O'Reilly Learning Platform](https://learning.oreilly.com) (formerly Safari Books Online).

**⚠️ Disclaimer**: This tool is for *personal* and *educational* purposes only. Please read [O'Reilly's Terms of Service](https://learning.oreilly.com/terms/) before use.

<a href='https://ko-fi.com/Y8Y0MPEGU' target='_blank'><img height='80' style='border:0px;height:60px;' src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com'/></a>

## ⚠️ Important Notes

- **Login via `--cred` no longer works** due to O'Reilly API changes
- **Manual cookie extraction required** (see [Cookie Setup](#cookie-setup) below)
- **Still fully functional** for downloading books with valid cookies

---

## Table of Contents

  * [Quick Start](#quick-start)
  * [Requirements & Setup](#requirements--setup)
  * [Cookie Setup](#cookie-setup)
  * [Usage](#usage)
  * [Development Setup](#development-setup-for-contributors)
  * [Testing](#testing)
  * [Single Sign-On (SSO), Company, University Login](https://github.com/willianpaixao/safaribooks/issues/150#issuecomment-555423085)
  * [Calibre EPUB conversion](#calibre-epub-conversion)
  * [Example: Download *Test-Driven Development with Python, 2nd Edition*](#download-test-driven-development-with-python-2nd-edition)
  * [Example: Use or not the `--kindle` option](#use-or-not-the---kindle-option)
  * [Documentation](#documentation)

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
python3 safaribooks.py <BOOK_ID>

# Example:
python3 safaribooks.py 9781491958698
```

---

## Requirements & Setup

### System Requirements

- **Python**: 3.11 or higher
- **pip**: Latest version recommended
- **Operating Systems**: Linux, macOS, Windows

### Installation Options

#### Option 1: Recommended

```bash
# Clone repository
git clone https://github.com/willianpaixao/safaribooks.git
cd safaribooks

# Install with pip
pip install -e .

# Or install with development tools
pip install -e ".[development]"
```

#### Option 2: Virtual Environment (Best Practice)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install
pip install -e .
```

### Dependencies

The program requires only 2 core dependencies:

```python
lxml>=5.0.0      # HTML/XML parsing
requests>=2.31.0 # HTTP client
```

---

## Cookie Setup

Since direct login is disabled, you must extract cookies from your browser:

### Method 1: Browser Developer Tools

1. Log in to https://learning.oreilly.com in your browser
2. Open Developer Tools (F12)
3. Go to "Application" tab → "Cookies" → "https://learning.oreilly.com"
4. Copy relevant cookies and create `cookies.json`:

```json
{
  "orm-jwt": "your-jwt-token-here",
  "sessionid": "your-session-id-here"
}
```

### Method 2: Browser Extension

Use a cookie export extension like "EditThisCookie" or "Cookie-Editor" to export cookies from `learning.oreilly.com`.

**⚠️ Security Note**: The `cookies.json` file contains your session token. Keep it private and don't commit it to version control.

## Usage:
It's really simple to use, just choose a book from the library and replace in the following command:
  * X-es with its ID,
  * `email:password` with your own.

```shell
$ python3 safaribooks.py --cred "account_mail@mail.com:password01" XXXXXXXXXXXXX
```

The ID is the digits that you find in the URL of the book description page:
`https://www.safaribooksonline.com/library/view/book-name/XXXXXXXXXXXXX/`
Like: `https://www.safaribooksonline.com/library/view/test-driven-development-with/9781491958698/`

#### Program options:
```shell
$ python3 safaribooks.py --help
usage: safaribooks.py [--cred <EMAIL:PASS> | --login] [--no-cookies]
                      [--kindle] [--preserve-log] [--help]
                      <BOOK ID>

Download and generate an EPUB of your favorite books from Safari Books Online.

positional arguments:
  <BOOK ID>            Book digits ID that you want to download. You can find
                       it in the URL (X-es):
                       `https://learning.oreilly.com/library/view/book-
                       name/XXXXXXXXXXXXX/`

optional arguments:
  --cred <EMAIL:PASS>  Credentials used to perform the auth login on Safari
                       Books Online. Es. ` --cred
                       "account_mail@mail.com:password01" `.
  --login              Prompt for credentials used to perform the auth login
                       on Safari Books Online.
  --no-cookies         Prevent your session data to be saved into
                       `cookies.json` file.
  --kindle             Add some CSS rules that block overflow on `table` and
                       `pre` elements. Use this option if you're going to
                       export the EPUB to E-Readers like Amazon Kindle.
  --preserve-log       Leave the `info_XXXXXXXXXXXXX.log` file even if there
                       isn't any error.
  --help               Show this help message.
```

The first time you use the program, you'll have to specify your Safari Books Online account credentials (look [`here`](/../../issues/15) for special character).
The next times you'll download a book, before session expires, you can omit the credential, because the program save your session cookies in a file called `cookies.json`.
For **SSO**, please use the `sso_cookies.py` program in order to create the `cookies.json` file from the SSO cookies retrieved by your browser session (please follow [`these steps`](/../../issues/150#issuecomment-555423085)).

Pay attention if you use a shared PC, because everyone that has access to your files can steal your session.
If you don't want to cache the cookies, just use the `--no-cookies` option and provide all time your credential through the `--cred` option or the more safe `--login` one: this will prompt you for credential during the script execution.

You can configure proxies by setting on your system the environment variable `HTTPS_PROXY` or using the `USE_PROXY` directive into the script.

#### Calibre EPUB conversion
**Important**: since the script only download HTML pages and create a raw EPUB, many of the CSS and XML/HTML directives are wrong for an E-Reader. To ensure best quality of the output, I suggest you to always convert the `EPUB` obtained by the script to standard-`EPUB` with [Calibre](https://calibre-ebook.com/).
You can also use the command-line version of Calibre with `ebook-convert`, e.g.:
```bash
$ ebook-convert "XXXX/safaribooks/Books/Test-Driven Development with Python 2nd Edition (9781491958698)/9781491958698.epub" "XXXX/safaribooks/Books/Test-Driven Development with Python 2nd Edition (9781491958698)/9781491958698_CLEAR.epub"
```
After the execution, you can read the `9781491958698_CLEAR.epub` in every E-Reader and delete all other files.

The program offers also an option to ensure best compatibilities for who wants to export the `EPUB` to E-Readers like Amazon Kindle: `--kindle`, it blocks overflow on `table` and `pre` elements (see [example](#use-or-not-the---kindle-option)).
In this case, I suggest you to convert the `EPUB` to `AZW3` with Calibre or to `MOBI`, remember in this case to select `Ignore margins` in the conversion options:

![Calibre IgnoreMargins](https://github.com/lorenzodifuccia/cloudflare/raw/master/Images/safaribooks/safaribooks_calibre_IgnoreMargins.png "Select Ignore margins")

## Examples:
  * ## Download [Test-Driven Development with Python, 2nd Edition](https://www.safaribooksonline.com/library/view/test-driven-development-with/9781491958698/):
    ```shell
    $ python3 safaribooks.py --cred "my_email@gmail.com:MyPassword1!" 9781491958698

           ____     ___         _
          / __/__ _/ _/__ _____(_)
         _\ \/ _ `/ _/ _ `/ __/ /
        /___/\_,_/_/ \_,_/_/ /_/
          / _ )___  ___  / /__ ___
         / _  / _ \/ _ \/  '_/(_-<
        /____/\___/\___/_/\_\/___/

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    [-] Logging into Safari Books Online...
    [*] Retrieving book info...
    [-] Title: Test-Driven Development with Python, 2nd Edition
    [-] Authors: Harry J.W. Percival
    [-] Identifier: 9781491958698
    [-] ISBN: 9781491958704
    [-] Publishers: O'Reilly Media, Inc.
    [-] Rights: Copyright © O'Reilly Media, Inc.
    [-] Description: By taking you through the development of a real web application
    from beginning to end, the second edition of this hands-on guide demonstrates the
    practical advantages of test-driven development (TDD) with Python. You’ll learn
    how to write and run tests before building each part of your app, and then develop
    the minimum amount of code required to pass those tests. The result? Clean code
    that works.In the process, you’ll learn the basics of Django, Selenium, Git,
    jQuery, and Mock, along with curre...
    [-] Release Date: 2017-08-18
    [-] URL: https://learning.oreilly.com/library/view/test-driven-development-with/9781491958698/
    [*] Retrieving book chapters...
    [*] Output directory:
        /XXXX/safaribooks/Books/Test-Driven Development with Python 2nd Edition (9781491958698)
    [-] Downloading book contents... (53 chapters)
        [#####################################################################] 100%
    [-] Downloading book CSSs... (2 files)
        [#####################################################################] 100%
    [-] Downloading book images... (142 files)
        [#####################################################################] 100%
    [-] Creating EPUB file...
    [*] Done: /XXXX/safaribooks/Books/Test-Driven Development with Python 2nd Edition
    (9781491958698)/9781491958698.epub

        If you like it, please * this project on GitHub to make it known:
            https://github.com/willianpaixao/safaribooks
        e don't forget to renew your Safari Books Online subscription:
            https://learning.oreilly.com

    [!] Bye!!
    ```
     The result will be (opening the `EPUB` file with Calibre):

    ![Book Appearance](https://github.com/lorenzodifuccia/cloudflare/raw/master/Images/safaribooks/safaribooks_example01_TDD.png "Book opened with Calibre")

  * ## Use or not the `--kindle` option:
    ```bash
    $ python3 safaribooks.py --kindle 9781491958698
    ```
    On the right, the book created with `--kindle` option, on the left without (default):

    ![NoKindle Option](https://github.com/lorenzodifuccia/cloudflare/raw/master/Images/safaribooks/safaribooks_example02_NoKindle.png "Version compare")

---

## Development Setup (For Contributors)

Want to contribute? Here's how to set up a development environment:

```bash
# 1. Fork and clone
git clone https://github.com/YOUR-USERNAME/safaribooks.git
cd safaribooks

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 3. Install with dev dependencies
pip install -e ".[development]"

# 4. Install pre-commit hooks
pre-commit install

# 5. Run tests to verify setup
pytest tests/ -v
```

### Development Tools

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks for code quality

### Code Quality Commands

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix issues
ruff check . --fix

# Type check
mypy safaribooks.py logger.py

# Run all pre-commit hooks
pre-commit run --all-files
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_parser.py

# Run specific test
pytest tests/unit/test_parser.py::TestLinkReplace::test_replace_html_with_xhtml

# Run with coverage report
pytest tests/ --cov=safaribooks --cov=logger --cov-report=term-missing
```
