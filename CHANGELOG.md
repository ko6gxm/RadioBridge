# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-01-XX

### Added
- **County-level downloads**: Download repeaters filtered by county within a state
  - New `RepeaterBookDownloader.download_by_county()` method
  - New `download_repeater_data_by_county()` convenience function
  - CLI support: `ham-formatter download --state CA --county "Los Angeles"`

- **City-level downloads**: Download repeaters filtered by city within a state
  - New `RepeaterBookDownloader.download_by_city()` method
  - New `download_repeater_data_by_city()` convenience function
  - CLI support: `ham-formatter download --state TX --city Austin`

- **Enhanced CLI validation**: Mutually exclusive location options with clear error messages
- **Automatic filename generation**: Smart output filenames based on search criteria
  - State: `repeaters_<state>.csv`
  - County: `repeaters_<state>_<county>.csv`
  - City: `repeaters_<state>_<city>.csv`

- **Comprehensive test suite**: Unit tests and CLI tests for all new functionality
- **API documentation**: Updated docs with county/city search parameters

### Changed
- **Refactored downloader architecture**: Unified internal download flow for all location types
- **Updated CLI help text**: More descriptive usage examples and option explanations
- **Enhanced error messages**: Better location-specific error reporting

### Technical
- Refactored `RepeaterBookDownloader` with new `_build_params()` and unified `_download()` methods
- Updated `_try_csv_export()` and `_scrape_html_table()` to use parameter dictionaries
- Added `responses` library for HTTP mocking in tests
- Version bump to 0.2.0 in all relevant files

### Backward Compatibility
- **100% backward compatible**: All existing APIs unchanged
- Original `download_repeater_data()` function works exactly as before
- State-level CLI usage (`--state CA`) unchanged
- All radio formatters and other functionality unmodified

## [0.1.0] - 2025-01-XX

### Added
- Initial release of Ham Formatter
- State-level repeater downloads from RepeaterBook.com
- Support for multiple ham radio models:
  - Anytone AT-D878UV II (Plus)
  - Anytone AT-D578UV III (Plus)
  - Baofeng DM-32UV
  - Baofeng K5 Plus
- Command-line interface with download and format commands
- Python library API for programmatic usage
- CSV export and HTML scraping capabilities
- Comprehensive test suite
- Development tooling (Black, Flake8, pre-commit hooks)
