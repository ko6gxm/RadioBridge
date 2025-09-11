# RadioBridge 📻

**Professional Amateur Radio Repeater Programming Made Easy**

*A powerful Python toolkit for downloading and formatting repeater data from RepeaterBook.com for popular ham radio models. Created by Craig Simon - KO6GXM.*

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/tests-115_passing-brightgreen.svg)](https://github.com/ko6gxm/radiobridge)
[![Coverage](https://img.shields.io/badge/coverage-69%25-yellowgreen.svg)](https://github.com/ko6gxm/radiobridge)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ko6gxm/radiobridge/pulls)

## 🚀 Overview

RadioBridge revolutionizes the way amateur radio operators manage their repeater programming. This sophisticated yet user-friendly tool automatically downloads comprehensive repeater information from RepeaterBook.com and intelligently formats it for your specific radio models.

**Why RadioBridge?**
- 🎯 **Precision**: Downloads detailed repeater information including tones, offsets, and operational status
- 🌍 **Comprehensive**: Supports state, county, and city-level searches across multiple countries
- 🔧 **Smart Formatting**: Automatically handles radio-specific CSV formats and field mappings
- ⚡ **Efficient**: Built-in rate limiting and retry logic for reliable data collection
- 🛡️ **Respectful**: "No hammer" mode with intelligent delays to protect RepeaterBook servers

### 📡 Supported Radio Models

| Radio Model | Type | Modes | Key Features |
|-------------|------|-------|-------------|
| **Anytone AT-D878UV II Plus** | Handheld | DMR/Analog | GPS, Bluetooth, Roaming, Zones |
| **Anytone AT-D578UV III Plus** | Mobile | DMR/Analog | GPS, APRS, Cross-band Repeat, Color Display |
| **Baofeng DM-32UV** | Handheld | DMR/Analog | Dual-band, Digital/Analog, Budget-friendly |
| **Baofeng K5 Plus** | Handheld | Analog | Compact, Dual-band, Simple Operation |

> **Adding Your Radio**: The modular architecture makes it easy to add support for new models. See the [Contributing](#-contributing) section for details.

## ✨ Key Features

### 🌐 Smart Data Collection
- **Multi-level Search**: Download by state, county, or city for precise targeting
- **Band Filtering**: Focus on specific amateur bands (6m, 4m, 2m, 70cm, 33cm, 23cm)
- **Detailed Information**: Automatic collection of extended repeater metadata
- **International Support**: Works with RepeaterBook's global database

### 🎛️ Professional Formatting
- **Radio-Specific Output**: Tailored CSV formats for each supported radio model
- **Zone Generation**: Intelligent geographic grouping for Anytone radios
- **Field Mapping**: Automatic conversion between RepeaterBook and radio-specific fields
- **Data Validation**: Built-in checks for frequency ranges and tone values

### 🖥️ Dual Interface
- **Command-Line Tool**: Perfect for automation and batch processing
- **Python Library**: Full API access for custom applications and integrations
- **Comprehensive Logging**: Detailed progress tracking and debugging information
- **Flexible Output**: Custom file naming and multiple export options

## 📦 Installation

### Quick Start (Recommended)

```bash
# Install from PyPI (when available)
pip install radiobridge

# Or install from GitHub
pip install git+https://github.com/ko6gxm/radiobridge.git
```

### macOS Binary (Prebuilt)

You can download a prebuilt macOS binary from the Releases page.

- Architectures: arm64 (Apple Silicon) and x86_64 (Intel)
- File names: rb-macos-arm64, rb-macos-x86_64

Usage:

```bash
# Make it executable (if needed)
chmod +x ./rb-macos-arm64

# Verify
./rb-macos-arm64 --version

# Example
./rb-macos-arm64 download --state CA
```

Gatekeeper (first run on macOS):
- Right-click the file → Open → Confirm to run an unsigned binary
- Or remove quarantine attribute (advanced): `xattr -dr com.apple.quarantine ./rb-macos-arm64`

Note: Binaries are not codesigned/notarized.

### Development Installation

```bash
# Clone the repository
git clone https://github.com/ko6gxm/radiobridge.git
cd radiobridge

# Install pipenv if not already installed
pip install pipenv

# Create virtual environment and install dependencies
pipenv install --dev

# Install in development mode
pipenv run pip install -e .

# Verify installation
rb --version
```

### System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, Linux
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space for data and temporary files
- **Network**: Internet connection for downloading repeater data

### What's New in v0.2.0 🎉

- 🎯 **Precision Targeting**: County and city-level downloads for focused repeater lists
- 🔍 **Enhanced Details**: Automatic collection of extended repeater information
- 🛡️ **Server Respect**: Advanced rate limiting with "no hammer" mode
- 📍 **Smart Zones**: Geographic grouping for better radio organization
- 🐛 **Rock Solid**: Comprehensive bug fixes and stability improvements

## 🎯 Usage Guide

### Quick Start Examples

```bash
# See what radios are supported
rb list-radios

# Download and format in one command
rb download --state CA --county "Orange" | \
rb format --radio anytone-878 --output my_repeaters.csv

# Get detailed help
rb download --help
```

### 🖥️ Command Line Interface

#### Download Repeater Data

**Basic Downloads:**
```bash
# Download all repeaters in California
rb download --state CA

# Download with specific bands only
rb download --state TX --band 2m --band 70cm

# International support
rb download --state ON --country Canada
```

**Precision Targeting:**
```bash
# County-level (perfect for local repeaters)
rb download --state CA --county "Los Angeles"

# City-level (ultra-focused)
rb download --state NY --city "New York"

# Multiple locations (script friendly)
for county in "Orange" "Riverside" "San Bernardino"; do
  rb download --state CA --county "$county" \
    --output "ca_${county,,}_repeaters.csv"
done
```

**Advanced Options:**
```bash
# Respectful downloading with random delays
rb download --state CA --nohammer

# Custom rate limiting (good for slow connections)
rb download --state TX --rate-limit 2.0

# Debug mode (see all collected data)
rb --verbose download --state CA --debug

# Custom output location
rb download --state CA --output /path/to/my/repeaters.csv

# Use the RepeaterBook JSON API instead of scraping (personal use; attribution required)
# Tip: include your contact email via CLI or env var; API keys may be required for commercial use.
export RADIOBRIDGE_RB_CONTACT_EMAIL=me@example.com
rb download --state CA --source api --band 2m

# How API filtering works (important)
# - The CLI sends state_id (numeric) to the API for compatibility (e.g., CA → 06)
# - Band values are mapped to API-compatible values:
#     2m → 2m, 70cm → 440, 33cm → 900, 23cm → 1200 (6m and 4m map to themselves)
# - When multiple bands (or "all") are requested, the request omits the band parameter
#   and filters locally after fetch to honor your requested bands
# - API responses are normalized (e.g., "Frequency" → "frequency") so band filtering is reliable

# Try API first, then fall back to scraping automatically if rate-limited
rb download --state CA --source auto
```

#### Format for Your Radio

```bash
# Format downloaded data
rb format repeaters.csv --radio anytone-878 --output programmed.csv

# Direct pipeline (download + format)
rb download --state CA | \
rb format --radio baofeng-k5 --output k5_ready.csv

# New full-field formatters (exact CPS headers)
rb format repeaters.csv --radio anytone-878-uvii --output anytone_878_uvii_full.csv
rb format repeaters.csv --radio baofeng-dm32uv-full --output dm32uv_full.csv

# Multiple radio formats from same data
for radio in anytone-878 anytone-578 anytone-878-uvii baofeng-dm32uv baofeng-dm32uv-full baofeng-k5; do
  rb format repeaters.csv --radio $radio --output "${radio}_repeaters.csv"
done
```

#### Logging and Debugging

```bash
# Verbose output (see what's happening)
rb --verbose download --state CA

# Save logs for troubleshooting
rb --verbose --log-file debug.log download --state CA

# Debug mode (maximum information)
rb --verbose download --state CA --debug
```

### Python Library Usage

```python
import radiobridge

# Download repeater data by state
data = radiobridge.download_repeater_data(state="CA", country="United States")

# Download repeater data by county
county_data = radiobridge.download_repeater_data_by_county(
    state="CA", county="Los Angeles", country="United States"
)

# Download repeater data by city
city_data = radiobridge.download_repeater_data_by_city(
    state="TX", city="Austin", country="United States"
)

# Get a formatter for your radio
from radiobridge.radios import get_radio_formatter

formatter = get_radio_formatter("anytone-878")
formatted_data = formatter.format(data)

# Save formatted data
radiobridge.write_csv(formatted_data, "my_repeaters.csv")

# Note: Python library mode uses the same logging configuration
# To enable verbose logging in your scripts:
from radiobridge.logging_config import setup_logging
setup_logging(verbose=True)  # Enable debug-level logging
```

### Advanced Usage

#### Custom Data Processing (no pandas)

```python
from radiobridge import (
    download_repeater_data_by_county,
    write_csv,
)
from radiobridge.band_filter import filter_by_frequency
from radiobridge.lightweight_data import LightDataFrame
from radiobridge.radios import get_radio_formatter

# Download data for multiple counties in a state
counties = ["Los Angeles", "Orange", "Riverside"]
records = []
for county in counties:
    df = download_repeater_data_by_county("CA", county)
    records.extend(df.to_dict(orient="records"))

# Combine into a single dataset
combined = LightDataFrame.from_records(records)

# Filter by band (example: only 70cm/UHF)
uhf_only = filter_by_frequency(combined, ["70cm"])

# Format for multiple radios
for radio in ["anytone-878-uvii", "baofeng-dm32uv-full"]:
    formatter = get_radio_formatter(radio)
    formatted = formatter.format(uhf_only)
    write_csv(formatted, f"{radio}_uhf_repeaters.csv")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd radiobridge

# Install pipenv if not installed
brew install pipenv

# Create virtual environment and install dependencies
pipenv install --dev

# Install package in development mode
pipenv run pip install -e .

# Install pre-commit hooks
pipenv run pre-commit install
```

### Testing & Coverage

RadioBridge maintains high code quality with comprehensive testing:

- **115+ Tests**: Complete test coverage for all functionality
- **69% Code Coverage**: Focused on critical code paths
- **Multiple Platforms**: Tested on Windows, macOS, and Linux
- **Python Compatibility**: Supports Python 3.9 through 3.13

```bash
# Run all tests with coverage (default behavior)
pipenv run pytest

# Run tests with detailed coverage report
pipenv run pytest --cov-report=html

# Run specific test categories
pipenv run pytest -m unit          # Unit tests only
pipenv run pytest -m integration   # Integration tests only
pipenv run pytest -m "not slow"    # Skip slow tests

# Run tests for specific functionality
pipenv run pytest tests/test_radios.py              # Radio formatters
pipenv run pytest tests/test_downloader.py          # Data downloading
pipenv run pytest tests/test_cli.py                 # CLI interface
```

**Coverage Reports:**
- **Terminal**: Coverage summary displayed after each test run
- **HTML**: Detailed line-by-line coverage in `htmlcov/index.html`
- **XML**: Machine-readable coverage data in `coverage.xml`

**Testing Philosophy:**
- **Critical paths first**: High coverage on user-facing functionality
- **Real-world scenarios**: Tests based on actual usage patterns
- **Mock external services**: No dependencies on RepeaterBook during testing
- **Fast execution**: Complete test suite runs in under 4 seconds

### Code Quality

```bash
# Format code with Black
pipenv run black src/ tests/

# Lint with Flake8
pipenv run flake8 src/ tests/

# Run pre-commit hooks manually
pipenv run pre-commit run --all-files
```

### Logging

RadioBridge includes comprehensive logging to help with debugging and monitoring:

#### Log Levels
- **INFO**: Normal operation messages (file operations, progress updates)
- **DEBUG**: Detailed diagnostic information (HTTP requests, data processing steps)
- **WARNING**: Non-fatal issues that may need attention
- **ERROR**: Error conditions that prevent normal operation

#### CLI Logging
```bash
# Normal operation (INFO level)
rb download --state CA

# Verbose mode (DEBUG level) - shows detailed progress
rb --verbose download --state CA

# Save logs to file
rb --verbose --log-file debug.log download --state CA

# Structured (JSON) logging to console
rb --log-format json download --state CA

# Structured logging via environment variable
export RADIOBRIDGE_LOG_FORMAT=json
rb download --state CA
```

#### Python Library Logging
```python
from radiobridge.logging_config import setup_logging

# Setup logging for your script
setup_logging(verbose=True)  # Enable DEBUG level
setup_logging(verbose=False, log_file="app.log")  # INFO to file

# All radiobridge operations will now log appropriately
import radiobridge
data = radiobridge.download_repeater_data("CA")
```

#### Structured (JSON) Logging
- Use `--log-format json` (or `RADIOBRIDGE_LOG_FORMAT=json`) to emit structured JSON lines
- Useful for log aggregation tools (jq, ELK, Datadog, etc.)
- Includes helpful fields when available: url, status, content_type, elapsed_s, params, timeout, state_id

#### CLI Exit Codes
- `0` Success
- `1` General error (validation, unsupported radio, etc.)
- `2` HTTP/network error (e.g., timeouts, 5xx)
- `3` Parse error (e.g., no repeater table found, invalid frequency data)

#### What Gets Logged
- **Download operations**: HTTP requests, response status, data parsing
- **File operations**: CSV read/write operations, file paths
- **Radio formatting**: Formatter selection, data validation, processing steps
- **Error conditions**: Network failures, parsing errors, invalid data

### Project Structure

```
radiobridge/
├── src/radiobridge/            # Main package
│   ├── __init__.py             # Public API
│   ├── cli.py                  # Command-line interface
│   ├── csv_utils.py            # CSV read/write utilities
│   ├── downloader.py           # RepeaterBook.com data fetcher
│   └── radios/                 # Radio formatters
│       ├── __init__.py         # Formatter registry
│       ├── base.py             # Base formatter class
│       ├── anytone_878_v3.py      # Anytone 878 v3 formatter
│       ├── anytone_878_v4.py      # Anytone 878 v4 formatter
│       ├── anytone_878_uvii.py    # Anytone 878 UVII full-field formatter
│       ├── baofeng_dm32uv.py      # Baofeng DM-32UV formatter
│       ├── baofeng_dm32uv_full.py # Baofeng DM-32UV full-field formatter
│       └── baofeng_k5_plus.py     # Baofeng K5 Plus formatter
├── tests/                       # Test suite
├── docs/                        # Documentation
├── pyproject.toml              # Project configuration
├── Pipfile                     # pipenv dependencies
└── README.md                   # This file
```

## Adding Support for New Radios

To add support for a new radio model:

1. Create a new formatter module in `src/radiobridge/radios/`
2. Inherit from `BaseRadioFormatter`
3. Implement required methods and properties
4. Register the formatter in `radios/__init__.py`
5. Add tests in `tests/test_radios.py`

Example:

```python
# src/radiobridge/radios/my_radio.py
from typing import List
from radiobridge.lightweight_data import LightDataFrame
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

    def format(self, data: LightDataFrame) -> LightDataFrame:
        rows = []
        for i in range(len(data)):
            row = data.iloc(i)
            rows.append({
                "Channel": i + 1,
                "Frequency": str(row.get("frequency")),
                "Name": row.get("callsign") or f"RPT{i+1}",
            })
        return LightDataFrame.from_records(rows)
```

## 🌍 Data Sources & Ethics

RadioBridge responsibly sources data from [RepeaterBook.com](https://repeaterbook.com), the premier community-maintained database of amateur radio repeaters worldwide.

### 🤝 Respectful Usage
- **Rate Limiting**: Built-in delays between requests (default: 1 second)
- **No Hammer Mode**: Random delays (1-10 seconds) for extra server consideration
- **Efficient Caching**: Temporary file storage to minimize repeat requests
- **Error Handling**: Graceful failures that don't overload servers

### 📊 Data Quality
- **Real-time**: Direct from RepeaterBook's live database
- **Community Verified**: Maintained by amateur radio operators worldwide
- **Comprehensive**: Includes technical details often missing from other sources
- **Global Coverage**: Supports repeaters from multiple countries

> 💡 **Support RepeaterBook**: Consider [donating to RepeaterBook.com](https://repeaterbook.com) to support their invaluable service to the amateur radio community.

## 🚀 Real-World Examples

### 📱 Mobile Radio Programming
```bash
# Program your mobile for a road trip through California
rb download --state CA --band 2m --band 70cm --nohammer
rb format ca_repeaters.csv --radio anytone-578 --output mobile_trip.csv
```

### 🏠 Home Station Setup
```bash
# Get comprehensive local coverage
rb download --state TX --county "Harris" --debug
rb format harris_repeaters.csv --radio anytone-878 --output home_station.csv
```

### ⚡ Emergency Communications
```bash
# Quick deployment for emergency services
for state in CA NV AZ; do
  rb download --state $state --band 2m --output "emcomm_${state}.csv"
done
```

### 🔄 Automated Updates
```bash
#!/bin/bash
# Weekly repeater update script
DATE=$(date +%Y%m%d)
rb --verbose --log-file "update_${DATE}.log" \
  download --state CA --county "Orange" \
  --output "repeaters_${DATE}.csv"

rb format "repeaters_${DATE}.csv" \
  --radio anytone-878 --output "programmed_${DATE}.csv"
```

## 🎯 Use Cases

### 👨‍🚒 Emergency Services
- **Quick Deployment**: Rapidly configure radios for disaster response
- **Regional Coverage**: Download repeaters across multiple affected areas
- **Reliable Data**: Access verified repeater information when it matters most

### 🚗 Mobile Operations
- **Travel Planning**: Pre-configure radios for cross-country trips
- **Local Access**: Find repeaters in unfamiliar areas
- **Band Planning**: Focus on specific bands for your equipment

### 🏢 Club Management
- **Member Services**: Provide standardized repeater lists to club members
- **Event Planning**: Configure radios for special events and contests
- **Education**: Teaching tool for new amateur radio operators

### 🔧 Commercial Applications
- **Radio Shop Services**: Automated programming for customer radios
- **Fleet Management**: Standardized configurations across multiple radios
- **Integration**: Embed in existing radio management systems

## 🔧 Troubleshooting

### Common Issues

**"No repeaters found" Error**
```bash
# Check your search criteria
rb download --state CA --county "Los Angeles" --verbose

# Verify spelling and try state-level first
rb download --state CA --verbose
```

**Network/Timeout Issues**
```bash
# Increase rate limiting for slow connections
rb download --state TX --rate-limit 3.0

# Use no-hammer mode for better reliability
rb download --state TX --nohammer
```

**Radio Format Issues**
```bash
# Check supported radios
rb list-radios

# Use exact radio identifier
rb format data.csv --radio anytone-878 --verbose
```

### Debug Mode
```bash
# Maximum diagnostic information
rb --verbose --log-file debug.log download --state CA --debug

# Check the log file for detailed information
cat debug.log | grep ERROR
```

## 📈 Performance & Scalability

### Optimization Tips
- **Band Filtering**: Use `--band` to reduce data volume
- **Geographic Targeting**: County/city filtering for focused results
- **Batch Processing**: Script multiple operations for efficiency
- **Caching**: Temporary files reduce redundant downloads

### Resource Usage
| Operation | Memory | Disk Space | Network |
|-----------|--------|------------|---------|
| State Download | ~50MB | ~10MB | ~1MB |
| County Download | ~20MB | ~2MB | ~200KB |
| City Download | ~10MB | ~1MB | ~100KB |
| Format Operation | ~30MB | ~5MB | None |

## 🔒 Privacy & Security

- **No Personal Data**: Only public repeater information is processed
- **Local Processing**: All data formatting happens on your machine
- **No Tracking**: No analytics or user tracking
- **Open Source**: Full transparency in code and operations

## 🎓 Educational Resources

### Learning Amateur Radio Programming
- **[RepeaterBook.com](https://repeaterbook.com)** - Primary data source
- **[ARRL](https://arrl.org)** - Amateur Radio Relay League resources
- **[Radio Programming Basics](https://ko6gxm.com)** - Visit Craig's blog for tutorials

### Contributing to Open Source
- **First Contribution?** Check out issues labeled "good first issue"
- **Testing Needed** - Try it with your radio model and report results
- **Documentation** - Help improve examples and tutorials

## 📞 Support & Community

### Getting Help
1. **📖 Documentation**: Check this README and inline help (`--help`)
2. **🐛 Issues**: [GitHub Issues](https://github.com/ko6gxm/radiobridge/issues) for bugs and feature requests
3. **💬 Discussions**: [GitHub Discussions](https://github.com/ko6gxm/radiobridge/discussions) for general questions
4. **📧 Direct Contact**: craig@ko6gxm.com for urgent issues

### Author

**Craig Simon - KO6GXM**
- 📧 Email: craig@ko6gxm.com
- 🌐 Website: [ko6gxm.com](https://ko6gxm.com)
- 📻 QRZ: [KO6GXM on QRZ.com](https://qrz.com/db/KO6GXM)
- 🐙 GitHub: [@ko6gxm](https://github.com/ko6gxm)

*"Making amateur radio more accessible through better tools and automation."*

## 🤝 Contributing

Contributions make the amateur radio community stronger! Here's how you can help:

### 🚀 Quick Contributions
- **⭐ Star this repo** to show your support
- **🐛 Report bugs** with detailed information
- **📝 Improve documentation** with better examples
- **🧪 Test with your radio** and share results

### 🔧 Development Contributions
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`pipenv run pytest`)
5. **Format** code (`pipenv run black .`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Push** to branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### 🎯 High-Priority Needs
- **New Radio Support**: Add formatters for popular radio models
- **International Testing**: Verify compatibility with non-US repeater data
- **Performance Optimization**: Make large downloads faster
- **Documentation**: More real-world examples and tutorials

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License - Copyright (c) 2025 Craig Simon - KO6GXM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## ⚠️ Disclaimer

This software is provided "**as is**" without warranty of any kind. Users are responsible for:

- ✅ **Verifying repeater information accuracy**
- ✅ **Ensuring compliance with local amateur radio regulations**
- ✅ **Respecting RepeaterBook.com's terms of service**
- ✅ **Using appropriate power levels and operating procedures**

*Amateur radio operators are licensed and responsible for their transmissions.*

---

<div align="center">

**Made with ❤️ by the Amateur Radio Community**

*RadioBridge - Professional repeater programming made simple*

[![Built with Python](https://img.shields.io/badge/built%20with-Python-blue.svg)](https://python.org)
[![Amateur Radio](https://img.shields.io/badge/amateur%20radio-FCC%20Part%2097-red.svg)](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-97)
[![Open Source](https://img.shields.io/badge/open%20source-MIT-green.svg)](https://opensource.org/licenses/MIT)

*Visit [ko6gxm.com](https://ko6gxm.com) for more amateur radio tools and tutorials*

</div>
