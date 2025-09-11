# Changelog

All notable changes to this project will be documented in this file.

## [0.4.2] - 2025-09-11

### Fixed
- Detailed downloader now preserves frequencies/offsets/tones by cleaning the main table before filtering and falling back to base table values when detail pages are incomplete.
- Broadened frequency parsing on detail pages (Output/Receive for downlink; Input/Transmit for uplink).

## [0.4.0] - 2025-09-11

### Added
- CLI: JSON logging output via `--log-format json` (or `RADIOBRIDGE_LOG_FORMAT=json`).
- Typed CLI exit codes: `2` for HTTP/network errors, `3` for parse errors (others remain `1`).
- Common typed errors module: `radiobridge.errors` (`HTTPRequestError`, `ParseError`, etc.).

### Improved
- Downloader logging with contextual fields (url, status, content-type, elapsed).
- Detailed downloader now raises typed errors for clearer failure modes.
- README updated to document JSON logging, env var fallback, and exit codes.

### Fixed
- Test issues around kw-only constructor usage for `UnifiedDownloader`.

## [0.3.0] - 2025-09-10
- Previous minor release (see repository history).

[0.4.0]: https://github.com/ko6gxm/RadioBridge/releases/tag/v0.4.0

# Changelog

*All notable changes to RadioBridge will be documented in this file.*

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## How to Read This Changelog

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

## [Unreleased]

### Fixed
- 🛠️ RepeaterBook JSON API 400 errors when using API source
  - Use `state_id` (numeric) instead of two-letter `state` when calling `https://www.repeaterbook.com/api/export.php`
  - Map CLI band selections to API-compatible values (e.g., `70cm` → `440`, `33cm` → `900`, `23cm` → `1200`)
  - Omit the `band` parameter when the effective value is `All` (e.g., multiple bands), then apply client-side band filtering
  - Normalize API response columns (e.g., `Frequency` → `frequency`) so frequency-based filtering is always effective

### Documentation
- Expanded README and repeaterbook_api.md with details on API parameters, band mapping, `state_id` usage, and client-side filtering behavior

### Removed
- 🧹 **Deprecated static frequency modules**: Cleaned up orphaned static list functionality
  - Removed `static_cli.py`, `static_commands.py`, and `static_lists.py` modules
  - Removed `enhanced_downloader.py` which was unused by main CLI
  - Updated coverage configuration to remove obsolete exclusions
  - Prepares codebase for reimplementation of static lists feature

## [0.2.0] - 2025-01-31

### Added
- 🎯 **County-level downloads**: Precision targeting for local repeater coverage
  - New `RepeaterBookDownloader.download_by_county()` method
  - New `download_with_details_by_county()` convenience function
  - CLI support: `rb download --state CA --county "Los Angeles"`
  - Perfect for local emergency services and club operations

- 🏙️ **City-level downloads**: Ultra-focused repeater lists for urban areas
  - New `RepeaterBookDownloader.download_by_city()` method
  - New `download_with_details_by_city()` convenience function
  - CLI support: `rb download --state TX --city Austin`
  - Ideal for mobile operations and travel planning

- 📡 **Detailed information collection**: Automatic gathering of extended repeater metadata
  - Enhanced repeater details from individual pages
  - Improved zone generation for Anytone radios
  - Better field mapping and data validation
  - All downloads now include comprehensive information by default

- 🛡️ **Advanced rate limiting**: Server-respectful downloading options
  - `--nohammer` flag with intelligent random delays (1-10 seconds)
  - Customizable `--rate-limit` for connection-specific needs
  - Built-in retry logic for network reliability
  - Temporary file management for efficient processing

- 🖥️ **Enhanced CLI experience**: Professional command-line interface
  - Mutually exclusive location options with clear error messages
  - Automatic filename generation based on search criteria
  - Comprehensive help text with real-world examples
  - Verbose logging and debug modes for troubleshooting

- ✅ **Rock-solid testing**: Comprehensive test coverage
  - Unit tests for all new functionality
  - CLI integration tests
  - Mock-based HTTP testing with realistic fixtures
  - 115+ tests ensuring reliability

### Changed
- 🏗️ **Modern architecture**: Completely refactored downloader system
  - Unified internal download flow for state/county/city operations
  - Modular design enabling easy extension for new features
  - Improved error handling and recovery mechanisms
  - Better separation of concerns between downloading and formatting

- 📖 **Professional documentation**: Comprehensive user and developer guides
  - Detailed CLI help with real-world examples
  - Enhanced error messages with actionable suggestions
  - Complete API documentation for library users
  - Step-by-step tutorials for common use cases

- ⚡ **Performance improvements**: Faster and more efficient operations
  - Optimized data processing pipelines
  - Reduced memory usage for large datasets
  - Better HTTP connection management
  - Smart caching to avoid redundant requests

### Fixed
- 🐛 **Critical indexing bug**: Resolved "single positional indexer is out-of-bounds" error
  - Fixed improper use of `.iloc` with filtered DataFrame indices
  - Replaced with robust `.loc` indexing for reliable data access
  - Affects detailed downloads with band filtering applied
  - Ensures stable operation with all search combinations

- 🔧 **Baofeng DM-32UV formatter improvements**: Enhanced compatibility and reliability
  - Fixed field mapping between basic and detailed download formats
  - Improved tone value extraction and validation
  - Better handling of DMR-specific parameters
  - More robust CSV output formatting

- 📊 **Data validation enhancements**: Improved error handling and data quality
  - Better frequency range validation
  - Enhanced tone value parsing for various formats
  - Improved handling of missing or malformed data
  - More informative error messages for troubleshooting

### Technical Improvements
- 🏗️ **Refactored `RepeaterBookDownloader`**: Modern, maintainable architecture
  - New `_build_params()` method for flexible parameter construction
  - Unified `_download()` method handling all location types
  - Improved separation between CSV export and HTML scraping paths
  - Enhanced error handling and logging throughout

- 🧪 **Advanced testing infrastructure**: Professional-grade test suite
  - Added `responses` library for reliable HTTP mocking
  - Realistic fixtures based on actual RepeaterBook data
  - Comprehensive CLI integration tests
  - Performance benchmarks and regression tests

- 📊 **Enhanced data processing**: Robust and efficient operations
  - Fixed indexing issues in `DetailedRepeaterDownloader._create_structured_output()`
  - Improved DataFrame handling with proper `.loc` usage
  - Better memory management for large datasets
  - Optimized CSV parsing and output generation

- 🔧 **Development experience improvements**: Better tools and workflows
  - Comprehensive logging with appropriate levels
  - Enhanced debugging capabilities with `--debug` flag
  - Improved error messages with actionable information
  - Better code organization and documentation

### Backward Compatibility 🛡️
- **100% backward compatible**: All existing functionality preserved
- Original `download_repeater_data()` function works exactly as before
- State-level CLI usage (`rb download --state CA`) unchanged
- All radio formatters maintain identical APIs and behavior
- Existing scripts and integrations continue to work without modification
- Same output formats and file structures for seamless upgrades

## [0.1.0] - 2025-01-15

### Added
- 🚀 **Initial release of RadioBridge**: Professional repeater programming tool
- 🌍 **State-level repeater downloads**: Access RepeaterBook.com's comprehensive database
- 📡 **Multi-radio support**: Formatters for popular amateur radio models
  - **Anytone AT-D878UV II Plus**: DMR/Analog handheld with GPS and Bluetooth
  - **Anytone AT-D578UV III Plus**: DMR/Analog mobile with GPS and APRS
  - **Baofeng DM-32UV**: Dual-band DMR/Analog handheld
  - **Baofeng K5 Plus**: Compact dual-band analog handheld
- 🖥️ **Dual interface design**: Command-line tool and Python library
  - Professional CLI with `download` and `format` commands
  - Full Python API for programmatic access and integration
  - Comprehensive help system and error handling
- 🔄 **Flexible data acquisition**: Multiple download strategies
  - Primary CSV export for efficient bulk downloads
  - HTML scraping fallback for maximum compatibility
  - Automatic format detection and data cleaning
- ✅ **Professional development practices**: Production-ready codebase
  - Comprehensive test suite with 100+ tests
  - Code formatting with Black, linting with Flake8
  - Pre-commit hooks ensuring code quality
  - Modular architecture for easy extension

---

## 🎯 Future Roadmap

### Planned for v0.3.0
- 📱 **Additional radio support**: Yaesu, Icom, and TYT models
- 🌐 **Enhanced international support**: Better handling of non-US repeater data
- ⚡ **Performance optimizations**: Faster downloads and processing
- 🎛️ **Advanced filtering**: Frequency ranges, power levels, and operational status

### Long-term Vision
- 🔗 **Integration APIs**: Connect with popular logging and contest software
- 📊 **Analytics**: Repeater coverage analysis and recommendations
- 🤖 **Automation**: Scheduled updates and monitoring
- 📱 **Mobile companion**: Smartphone app for field operations

---

*RadioBridge is developed by Craig Simon (KO6GXM) with ❤️ for the amateur radio community.*

*Visit [ko6gxm.com](https://ko6gxm.com) for more amateur radio tools and tutorials.*
