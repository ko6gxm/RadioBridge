# Ham Formatter

Download and format amateur radio repeater lists for various ham radio models.

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Ham Formatter is a Python tool that downloads repeater information from RepeaterBook.com and formats it for various ham radio programming software. It supports multiple radio models including Anytone, Baofeng, and others.

### Supported Radios

- **Anytone AT-D878UV II (Plus)** - DMR/Analog handheld with GPS and Bluetooth
- **Anytone AT-D578UV III (Plus)** - DMR/Analog mobile radio with GPS and APRS
- **Baofeng DN32UV** - Dual-band analog handheld with programmable memories
- **Baofeng K5 Plus** - Compact dual-band analog handheld radio

## Features

- **Download**: Fetch repeater data from RepeaterBook.com by state/region
- **Format**: Convert data to radio-specific CSV formats for programming software
- **CLI Tool**: Command-line interface for easy automation
- **Library**: Import as a Python library for custom applications
- **Extensible**: Easy to add support for new radio models

## Installation

### Requirements

- Python 3.9 or higher
- pipenv (for development)

### Install from Source

```bash
git clone <repository-url>
cd ham_formatter
pipenv install
pipenv run pip install -e .
```

## Usage

### Command Line Interface

#### List Supported Radios

```bash
ham-formatter list-radios
```

#### Download Repeater Data

Download all repeaters for a state:

```bash
# Download California repeaters
ham-formatter download --state CA --output ca_repeaters.csv

# Download Texas repeaters with verbose output
ham-formatter download --state TX --verbose
```

#### Format Data for Radio

Format downloaded data for a specific radio model:

```bash
# Format for Anytone 878
ham-formatter format ca_repeaters.csv --radio anytone-878 --output anytone_878_ca.csv

# Format for Baofeng K5 Plus
ham-formatter format ca_repeaters.csv --radio k5 --output baofeng_k5_ca.csv
```

### Python Library Usage

```python
import ham_formatter

# Download repeater data
data = ham_formatter.download_repeater_data(state="CA", country="United States")

# Get a formatter for your radio
from ham_formatter.radios import get_radio_formatter

formatter = get_radio_formatter("anytone-878")
formatted_data = formatter.format(data)

# Save formatted data
ham_formatter.write_csv(formatted_data, "my_repeaters.csv")
```

### Advanced Usage

#### Custom Data Processing

```python
import pandas as pd
from ham_formatter import read_csv, write_csv
from ham_formatter.radios import get_radio_formatter

# Load your own repeater data
data = read_csv("my_repeaters.csv")

# Filter data (example: only UHF repeaters)
uhf_data = data[data['frequency'].astype(float) >= 400.0]

# Format for multiple radios
formatters = ['anytone-878', 'baofeng-k5']
for radio in formatters:
    formatter = get_radio_formatter(radio)
    formatted = formatter.format(uhf_data)
    write_csv(formatted, f"{radio}_uhf_repeaters.csv")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd ham_formatter

# Install pipenv if not installed
brew install pipenv

# Create virtual environment and install dependencies
pipenv install --dev

# Install package in development mode
pipenv run pip install -e .

# Install pre-commit hooks
pipenv run pre-commit install
```

### Running Tests

```bash
# Run all tests
pipenv run pytest

# Run tests with verbose output
pipenv run pytest -v

# Run specific test file
pipenv run pytest tests/test_radios.py

# Run with coverage
pipenv run pytest --cov=ham_formatter
```

### Code Quality

```bash
# Format code with Black
pipenv run black src/ tests/

# Lint with Flake8
pipenv run flake8 src/ tests/

# Run pre-commit hooks manually
pipenv run pre-commit run --all-files
```

### Project Structure

```
ham_formatter/
├── src/ham_formatter/           # Main package
│   ├── __init__.py             # Public API
│   ├── cli.py                  # Command-line interface
│   ├── csv_utils.py            # CSV read/write utilities
│   ├── downloader.py           # RepeaterBook.com data fetcher
│   └── radios/                 # Radio formatters
│       ├── __init__.py         # Formatter registry
│       ├── base.py             # Base formatter class
│       ├── anytone_878.py      # Anytone 878 formatter
│       ├── anytone_578.py      # Anytone 578 formatter
│       ├── baofeng_dn32uv.py   # Baofeng DN32UV formatter
│       └── baofeng_k5.py       # Baofeng K5 Plus formatter
├── tests/                       # Test suite
├── docs/                        # Documentation
├── pyproject.toml              # Project configuration
├── Pipfile                     # pipenv dependencies
└── README.md                   # This file
```

## Adding Support for New Radios

To add support for a new radio model:

1. Create a new formatter module in `src/ham_formatter/radios/`
2. Inherit from `BaseRadioFormatter`
3. Implement required methods and properties
4. Register the formatter in `radios/__init__.py`
5. Add tests in `tests/test_radios.py`

Example:

```python
# src/ham_formatter/radios/my_radio.py
from typing import List
import pandas as pd
from .base import BaseRadioFormatter

class MyRadioFormatter(BaseRadioFormatter):
    @property
    def radio_name(self) -> str:
        return "My Radio Model"

    @property
    def description(self) -> str:
        return "Description of my radio"

    @property
    def required_columns(self) -> List[str]:
        return ["frequency"]

    @property
    def output_columns(self) -> List[str]:
        return ["Channel", "Frequency", "Name"]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        # Your formatting logic here
        pass
```

## Data Sources

This tool downloads data from RepeaterBook.com, which is a community-maintained database of amateur radio repeaters. Please respect their terms of service and consider making a donation to support their service.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Disclaimer

This software is provided "as is" without warranty. Users are responsible for verifying the accuracy of repeater information and ensuring compliance with amateur radio regulations in their jurisdiction.

## Support

For support, please open an issue on the GitHub repository or contact the maintainer.

---

**Note**: RepeaterBook.com URLs and data formats may change over time. If you encounter issues with data downloading, please check for updates or report the issue.
