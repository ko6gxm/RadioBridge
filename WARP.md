# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Quick Start Commands

### Development Environment Setup
```bash
# Install pipenv if not already installed
pip install pipenv

# Create virtual environment and install dependencies
pipenv install --dev

# Install package in development mode
pipenv run pip install -e .

# Verify installation
pipenv run rb --version
```

### Build and Testing
```bash
# Run all tests with coverage (default behavior)
pipenv run pytest

# Run tests with detailed coverage report
pipenv run pytest --cov-report=html

# Run specific test categories
pipenv run pytest -m unit          # Unit tests only
pipenv run pytest -m integration   # Integration tests only
pipenv run pytest tests/test_radios.py  # Radio formatters only

# Code formatting
pipenv run black src/ tests/

# Linting
pipenv run flake8 src/ tests/

# Run pre-commit hooks manually
pipenv run pre-commit run --all-files

# Install pre-commit hooks
pipenv run pre-commit install
```

### CLI Usage Examples
```bash
# See supported radio models
pipenv run rb list-radios

# Download repeaters for a state
pipenv run rb download --state CA

# Download with county targeting
pipenv run rb download --state CA --county "Los Angeles"

# Format data for specific radio
pipenv run rb format repeaters.csv --radio anytone-878 --output formatted.csv

# Pipeline download and format
pipenv run rb download --state TX | pipenv run rb format --radio baofeng-k5 --output ready.csv
```

## Project Architecture

### High-Level Data Flow
1. **CLI Command** (`cli.py`) → Parse user input and options
2. **Download Module** (`downloader.py`, `detailed_downloader.py`) → Fetch data from RepeaterBook.com
3. **CSV Utils** (`csv_utils.py`) → Data cleaning, validation, and I/O
4. **Radio Formatter** (`radios/`) → Transform generic data to radio-specific format
5. **Output** → Formatted CSV ready for radio programming software

### Core Modules
- `src/radiobridge/__init__.py`: Public API entry point
- `src/radiobridge/cli.py`: Click-based command-line interface with two main commands: `download` and `format`
- `src/radiobridge/downloader.py`: Basic RepeaterBook.com data fetcher
- `src/radiobridge/detailed_downloader.py`: Enhanced scraper that fetches individual repeater detail pages for comprehensive data
- `src/radiobridge/csv_utils.py`: Pandas-based CSV operations with data validation
- `src/radiobridge/radios/`: Radio formatter package with registry pattern

### Radio Formatter Plugin System
The project uses a registry pattern for radio formatters located in `src/radiobridge/radios/`:

**Key Components:**
- `base.py`: `BaseRadioFormatter` abstract class with common utilities
- `__init__.py`: `RADIO_FORMATTERS` registry maps radio names to formatter classes
- Individual formatters: `anytone_878.py`, `anytone_578.py`, `baofeng_dm32uv.py`, `baofeng_k5.py`

**Supported Radio Models:**
- Anytone AT-D878UV II Plus (handheld DMR/Analog)
- Anytone AT-D578UV III Plus (mobile DMR/Analog)
- Baofeng DM-32UV (handheld DMR/Analog)
- Baofeng K5 Plus (handheld analog)

## Adding Support for New Radios

1. **Create formatter module** in `src/radiobridge/radios/new_radio.py`:
```python
from typing import List
import pandas as pd
from .base import BaseRadioFormatter

class NewRadioFormatter(BaseRadioFormatter):
    @property
    def radio_name(self) -> str:
        return "New Radio Model"

    @property
    def description(self) -> str:
        return "Description of new radio"

    @property
    def required_columns(self) -> List[str]:
        return ["frequency", "callsign", "location"]

    @property
    def output_columns(self) -> List[str]:
        return ["Channel", "Frequency", "Name"]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        # Transform data to radio-specific format
        formatted = pd.DataFrame()
        formatted["Channel"] = range(1, len(data) + 1)
        formatted["Frequency"] = data["frequency"]
        formatted["Name"] = data["callsign"] + " " + data["location"]
        return formatted
```

2. **Register in `src/radiobridge/radios/__init__.py`**:
```python
from .new_radio import NewRadioFormatter

RADIO_FORMATTERS = {
    # existing formatters...
    "new-radio": NewRadioFormatter,
}

# Add aliases if needed
RADIO_ALIASES = {
    # existing aliases...
    "newradio": "new-radio",
    "new_radio": "new-radio",
}
```

3. **Add tests in `tests/test_radios.py`** following existing patterns

4. **Update documentation** if the radio has special requirements or features

## Testing Strategy

**Framework**: pytest with coverage reporting
**Coverage Target**: Currently 69%, focus on critical code paths
**Test Categories**:
- Unit tests (`-m unit`)
- Integration tests (`-m integration`)
- Slow tests can be skipped (`-m "not slow"`)

**Test Files:**
- `tests/test_cli.py`: CLI command testing with Click's test runner
- `tests/test_radios.py`: Radio formatter validation
- `tests/test_downloader.py`: Data download and parsing
- `tests/test_csv_utils.py`: File I/O and data validation
- `tests/test_detailed_downloader.py`: Enhanced scraping functionality

**Key Testing Patterns:**
- Mock external HTTP requests to RepeaterBook.com
- Use fixtures for sample repeater data
- Test both success and error conditions
- Validate output formats match radio requirements

## Code Quality Standards

**Python Version**: 3.9+ (supports 3.9-3.13)
**Formatting**: Black with 88-character line length
**Linting**: Flake8 with configuration in `pyproject.toml`
**Type Hints**: Encouraged but not strictly enforced
**Pre-commit Hooks**: Configured for trailing whitespace, YAML/TOML validation, and code formatting

**CI/CD Pipeline** (`.github/workflows/ci.yml`):
- Tests across Python 3.9-3.13 on Ubuntu, Windows, macOS
- Code formatting validation with Black
- Linting with Flake8
- Coverage reporting with pytest-cov
- Security scanning with Safety and Bandit
- Performance testing with memory usage monitoring
- Build validation for PyPI distribution

**Dependencies Management**:
- Use `pipenv` for dependency management
- `Pipfile` for runtime and dev dependencies
- `pyproject.toml` for package configuration and tool settings

## Key Development Notes

**Rate Limiting**: All downloads respect RepeaterBook.com servers with default 1-second delays. Use `--nohammer` for random 1-10 second delays.

**Data Sources**: Primary data from RepeaterBook.com CSV exports and HTML scraping for detailed information.

**Logging**: Comprehensive logging system with DEBUG level for data processing details. Use `--verbose` flag or `setup_logging(verbose=True)` in Python.

**Band Filtering**: Supports amateur radio bands: 6m, 4m, 2m, 70cm, 33cm, 23cm with validation in `band_filter.py`.

**Geographic Targeting**: Three levels - state, county, city - with automatic filename generation based on search criteria.

**Entry Points**: CLI accessible via `rb` command after installation, implemented through `click` framework with main group and subcommands.
