# Contributing to SafariBooks

Thank you for your interest in contributing to SafariBooks! This guide will help you get started.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing Requirements](#testing-requirements)
6. [Submitting Changes](#submitting-changes)
7. [Documentation](#documentation)
8. [Getting Help](#getting-help)

---

## Code of Conduct

This project follows the Contributor Covenant Code of Conduct. Be respectful, constructive, and professional in all interactions.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Git**
- **GitHub account** (for pull requests)

### Initial Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/safaribooks.git
   cd safaribooks
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/willianpaixao/safaribooks.git
   ```

4. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # OR
   .venv\Scripts\activate  # Windows
   ```

5. **Install with development dependencies**:
   ```bash
   pip install -e ".[development]"
   ```

6. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

7. **Verify setup**:
   ```bash
   pytest
   ruff check .
   mypy src/safaribooks
   ```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Conventions**:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions/improvements
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy src/safaribooks

# Run tests
pytest

# Run specific test categories
pytest tests/unit/test_cli.py          # CLI tests
pytest tests/unit/test_http_client.py  # HTTP client tests
pytest tests/unit/test_html_parser.py  # Parser tests
pytest tests/unit/test_epub_builder.py # EPUB builder tests

# Check coverage
pytest --cov=src/safaribooks --cov-report=html
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add new feature description"
```

**Commit Message Format**:
```
<type>: <subject>

[optional body]

[optional footer]
```

**Types**:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Code style/formatting
- `chore:` - Build/tooling changes

**Examples**:
```
feat: add async download support

fix: handle missing cover image gracefully

docs: update README with cookie setup instructions

test: add tests for parse_html method
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

### Code Quality Tools

#### Ruff (Linter + Formatter)

```bash
# Check code
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

Configuration in `pyproject.toml`:
- Line length: 100
- Python version: 3.11+
- Rules: pycodestyle, pyflakes, pep8-naming, etc.

#### MyPy (Type Checker)

```bash
mypy src/safaribooks
```

#### Pre-commit Hooks

Automatically run on every commit:
- Ruff linting and formatting
- MyPy type checking
- Trailing whitespace removal
- Line ending normalization
- Large file checks

```bash
# Run manually
pre-commit run --all-files
```

---

## Testing Requirements

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/unit/test_parser.py

# Specific test
pytest tests/unit/test_parser.py::TestLinkReplace::test_replace_html_with_xhtml

# With coverage
pytest --cov=src/safaribooks --cov-report=html

# With verbose output
pytest -vv

# With print statements
pytest -s

# Fail fast (stop on first failure)
pytest -x
```

---

## Submitting Changes

### Pull Request Process

1. **Ensure all checks pass**:
   - ✅ All tests passing
   - ✅ Code formatted (ruff)
   - ✅ No lint errors
   - ✅ Type check passes
   - ✅ Coverage maintained or increased

2. **Update documentation**:
   - Update README.md if needed
   - Add/update docstrings

3. **Create pull request**:
   - Clear, descriptive title
   - Reference related issues
   - Describe changes made
   - List breaking changes (if any)

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation update
- [ ] Test improvement

## Changes Made
- Changed X to improve Y
- Added tests for Z
- Updated documentation for W

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Coverage maintained/increased

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. **Automated checks** run via GitHub Actions
2. **Code review** by maintainers
3. **Discussion** if changes needed
4. **Approval** and merge

---

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing public APIs
- Fixing bugs (update examples if needed)
- Improving existing functionality

---

## Development Tips

### Quick Commands Reference

```bash
# Format and lint
ruff format . && ruff check .

# Run tests with coverage
pytest --cov=src/safaribooks --cov-report=term-missing

# Type check
mypy src/safaribooks

# All quality checks
ruff format . && ruff check . && mypy src/safaribooks && pytest
```
