# Development Guide

This guide covers the development setup, testing, and code quality practices for the ACC project.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Quality Tools](#code-quality-tools)
- [Testing](#testing)
- [Code Coverage](#code-coverage)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Continuous Integration](#continuous-integration)

## Development Setup

### Prerequisites

- Python 3.11 or 3.12
- Git

### Install Development Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or install from pyproject.toml
pip install -e ".[dev]"
```

### Development Dependencies

The project uses the following development tools:

- **pytest** - Testing framework
- **pytest-cov** - Coverage measurement
- **pytest-qt** - PyQt5 GUI testing
- **pytest-timeout** - Test timeout management
- **coverage** - Code coverage reporting
- **ruff** - Fast Python linter and formatter
- **pre-commit** - Pre-commit hook management

## Code Quality Tools

### Ruff - Linting and Formatting

Ruff is a fast Python linter that replaces multiple tools (black, isort, flake8, etc.).

#### Run Ruff Linter

```bash
# Check code
ruff check .

# Auto-fix issues
ruff check --fix .
```

#### Run Ruff Formatter

```bash
# Check formatting
ruff format --check .

# Format code
ruff format .
```

#### Configuration

Ruff is configured in `pyproject.toml`:

- **Line length**: 120 characters
- **Target Python**: 3.11+
- **Enabled rules**: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear, and more
- **Per-file ignores**: Customized for GUI files, tests, and examples

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_acc_core.py

# Run tests by marker
pytest -m unit          # Run unit tests only
pytest -m integration   # Run integration tests only
pytest -m gui           # Run GUI tests only
```

### Test Markers

The project uses pytest markers to organize tests:

- `unit` - Fast, isolated unit tests
- `integration` - Integration tests (may use files or data)
- `gui` - GUI tests (require Qt application)
- `slow` - Slow running tests (>1s)
- `performance` - Performance benchmarking tests
- `visualization` - Tests that generate visualizations
- `algorithm` - Core algorithm tests (acc_core.py)
- `utils` - Utility function tests (acc_utils.py)
- `io` - File I/O tests (CSV loading, etc.)

### Using Markers in Tests

```python
import pytest

@pytest.mark.unit
def test_simple_function():
    assert 1 + 1 == 2

@pytest.mark.integration
@pytest.mark.io
def test_csv_loading():
    # Test CSV file loading
    pass
```

## Code Coverage

### Running Tests with Coverage

```bash
# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run only unit tests with coverage (skip slow tests)
pytest --cov=. --cov-report=html -m "not slow"
```

### Coverage Reports

After running tests with coverage:

- **Terminal report**: Displays in console with missing lines
- **HTML report**: Open `htmlcov/index.html` in browser for detailed report
- **XML report**: `coverage.xml` for CI/CD integration

### Coverage Configuration

Coverage is configured in both `.coveragerc` and `pyproject.toml`:

**Excluded from coverage:**
- Test files (`*/tests/*`, `*/test_*.py`)
- Build artifacts (`*/build/*`, `*/dist/*`)
- Documentation (`*/docs/*`)
- Examples (`*/examples/*`)
- Auto-generated files

**Excluded lines:**
- `pragma: no cover`
- `if __name__ == .__main__.:`
- Abstract methods
- Debug code

### Coverage Commands

```bash
# Generate coverage report
coverage report

# Generate HTML report
coverage html

# Generate XML report (for Codecov)
coverage xml

# Combine multiple coverage files
coverage combine

# Erase coverage data
coverage erase
```

## Pre-commit Hooks

Pre-commit hooks automatically check code quality before each commit.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install
```

### Running Pre-commit Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
git add .
pre-commit run

# Run specific hook
pre-commit run ruff --all-files
```

### Configured Hooks

The `.pre-commit-config.yaml` includes:

#### 1. Ruff Linting & Formatting
- **ruff** - Linter with auto-fix
- **ruff-format** - Code formatter

#### 2. General File Checks
- **check-added-large-files** - Prevents committing files > 1MB
- **check-yaml** - Validates YAML syntax
- **check-json** - Validates JSON syntax
- **check-case-conflict** - Checks for filename case conflicts
- **check-merge-conflict** - Detects merge conflict markers
- **end-of-file-fixer** - Ensures newline at EOF
- **trailing-whitespace** - Removes trailing whitespace

### Bypassing Hooks (Not Recommended)

```bash
# Skip pre-commit hooks (use with caution)
git commit --no-verify -m "message"
```

### Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate
```

## Continuous Integration

### GitHub Actions Workflows

The project uses GitHub Actions for automated testing and deployment:

#### Test Workflow (`.github/workflows/test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual dispatch

**Features:**
- Tests on Python 3.11 and 3.12
- Ubuntu with headless GUI testing (Xvfb)
- Separate runs for fast tests and slow tests
- Coverage measurement and reporting
- Codecov integration
- Artifact uploads (coverage reports)

**Running locally with same environment:**

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y xvfb libxcb-xinerama0 libgl1

# Run tests with Xvfb (headless)
xvfb-run -a pytest tests/ -v --cov=.
```

#### Build Workflow (`.github/workflows/build.yml`)

**Triggers:**
- Push to `main` branch
- Tag pushes (`v*`)

**Features:**
- Multi-platform builds (Windows, macOS, Linux)
- PyInstaller executable creation
- Release artifact generation

### Codecov Integration

Code coverage is automatically uploaded to Codecov:

1. Coverage is measured during test runs
2. `coverage.xml` is generated
3. Codecov Action uploads the report
4. Coverage badge is available in README

**Codecov Badge:**

```markdown
[![codecov](https://codecov.io/gh/jikhanjung/ACC/branch/main/graph/badge.svg)](https://codecov.io/gh/jikhanjung/ACC)
```

## Best Practices

### Before Committing

1. **Run tests locally:**
   ```bash
   pytest -v
   ```

2. **Check coverage:**
   ```bash
   pytest --cov=. --cov-report=term-missing
   ```

3. **Run linter:**
   ```bash
   ruff check --fix .
   ruff format .
   ```

4. **Pre-commit hooks will run automatically** when you commit

### Writing Tests

1. **Use appropriate markers:**
   ```python
   @pytest.mark.unit
   @pytest.mark.algorithm
   def test_cluster_extraction():
       pass
   ```

2. **Use fixtures from conftest.py:**
   ```python
   def test_with_sample_data(sample_dendro):
       # sample_dendro is provided by conftest.py
       pass
   ```

3. **Name tests descriptively:**
   ```python
   def test_build_acc_with_empty_dendro_raises_error():
       pass
   ```

4. **Keep unit tests fast** (< 1s) - use `@pytest.mark.slow` for longer tests

### Code Style

- Follow PEP 8 with 120 character line length
- Use double quotes for strings
- Sort imports automatically (ruff handles this)
- Document public functions with docstrings
- Use type hints where appropriate (optional, but recommended)

## Troubleshooting

### Qt Platform Issues

If you get `qt.qpa.plugin: Could not find the Qt platform plugin "xcb"`:

```bash
# Set environment variable
export QT_QPA_PLATFORM=offscreen

# Or run with xvfb
xvfb-run -a pytest
```

### Coverage Not Working

```bash
# Make sure coverage config is used
pytest --cov=. --cov-config=.coveragerc

# Check if .coveragerc exists
ls -la .coveragerc

# Verify coverage is installed
pip list | grep coverage
```

### Pre-commit Hooks Not Running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check installation
pre-commit --version
git config --get core.hooksPath
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [coverage.py documentation](https://coverage.readthedocs.io/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [pre-commit documentation](https://pre-commit.com/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Codecov documentation](https://docs.codecov.com/)

## Contributing

When contributing to the project:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/my-feature`
3. **Install development dependencies:** `pip install -r requirements-dev.txt`
4. **Install pre-commit hooks:** `pre-commit install`
5. **Write tests** for your changes
6. **Run tests and ensure coverage:** `pytest --cov=.`
7. **Commit your changes** (pre-commit hooks will run)
8. **Push to your fork** and create a pull request

All pull requests must:
- Pass all tests
- Maintain or improve code coverage
- Pass pre-commit hooks
- Follow the project's code style
