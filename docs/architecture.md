# Ham Formatter Architecture

This document explains the architecture and design decisions of the Ham Formatter project.

## Overview

Ham Formatter is designed as a modular, extensible system for downloading and formatting amateur radio repeater data. The architecture follows these key principles:

- **Separation of Concerns**: Each module has a single responsibility
- **Extensibility**: Easy to add new radio formatters
- **Testability**: Components can be tested in isolation
- **Usability**: Both CLI and library interfaces

## Module Structure

### Core Modules

#### `ham_formatter/__init__.py`
- **Purpose**: Public API entry point
- **Exports**: Key functions for library users
- **Dependencies**: None (imports from submodules)

#### `ham_formatter/cli.py`
- **Purpose**: Command-line interface implementation
- **Framework**: Click for argument parsing and command structure
- **Commands**:
  - `download`: Download repeater data from RepeaterBook.com
  - `format`: Format data for specific radio models
  - `list-radios`: Show supported radio models
- **Dependencies**: Click, internal modules

#### `ham_formatter/csv_utils.py`
- **Purpose**: CSV file operations and data validation
- **Key Functions**:
  - `read_csv()`: Enhanced pandas CSV reading with error handling
  - `write_csv()`: CSV writing with directory creation
  - `validate_csv_columns()`: Column presence validation
  - `clean_csv_data()`: Data normalization
- **Dependencies**: Pandas, pathlib

#### `ham_formatter/downloader.py`
- **Purpose**: Download repeater data from RepeaterBook.com
- **Key Classes**:
  - `RepeaterBookDownloader`: Main downloader with session management
- **Features**:
  - Multiple download strategies (CSV export, HTML scraping)
  - Graceful fallbacks
  - Data cleaning and normalization
- **Dependencies**: Requests, BeautifulSoup4, Pandas

### Radio Formatters Package

#### `ham_formatter/radios/__init__.py`
- **Purpose**: Formatter registry and discovery
- **Key Functions**:
  - `get_supported_radios()`: List all supported models
  - `get_radio_formatter()`: Factory function for formatters
  - `list_radio_info()`: Detailed radio information
- **Registry**: Maps radio names to formatter classes
- **Aliases**: Supports multiple names for the same radio

#### `ham_formatter/radios/base.py`
- **Purpose**: Abstract base class for all radio formatters
- **Key Features**:
  - Abstract interface definition
  - Common utility methods for data cleaning
  - Input validation
- **Utilities**:
  - `clean_frequency()`: Normalize frequency formats
  - `clean_tone()`: Normalize CTCSS/DCS tones
  - `clean_offset()`: Normalize repeater offsets

#### Individual Radio Formatters
Each radio formatter inherits from `BaseRadioFormatter`:

- `anytone_878.py`: Anytone AT-D878UV II (Plus) handheld
- `anytone_578.py`: Anytone AT-D578UV III (Plus) mobile
- `baofeng_dm32uv.py`: Baofeng DM-32UV handheld
- `baofeng_k5.py`: Baofeng K5 Plus handheld

## Data Flow

```
1. CLI Command or Library Call
   ↓
2. Download Module (RepeaterBook.com)
   ↓
3. Raw CSV/HTML Data
   ↓
4. CSV Utils (Cleaning & Validation)
   ↓
5. Radio Formatter (Format Conversion)
   ↓
6. Formatted CSV Output
```

## Design Patterns

### Factory Pattern
- `get_radio_formatter()` creates appropriate formatter instances
- Allows runtime selection of formatters
- Supports aliases and case-insensitive lookup

### Strategy Pattern
- Each radio formatter implements the same interface
- Different formatting strategies for each radio model
- Easy to add new radio support

### Template Method Pattern
- `BaseRadioFormatter` provides common functionality
- Subclasses implement radio-specific formatting
- Shared data cleaning utilities

## Error Handling

### Graceful Degradation
- Multiple download strategies with fallbacks
- Continue processing even if some data is invalid
- Informative error messages

### Validation
- Input validation at module boundaries
- Required column checking for formatters
- File existence and permission checking

### Exception Hierarchy
- Custom exceptions for different error types
- Proper exception chaining and context
- User-friendly error messages in CLI

## Extensibility

### Adding New Radio Support

1. **Create Formatter Module**:
   ```python
   class NewRadioFormatter(BaseRadioFormatter):
       # Implement required methods
   ```

2. **Register in Registry**:
   ```python
   RADIO_FORMATTERS["new-radio"] = NewRadioFormatter
   ```

3. **Add Tests**:
   ```python
   def test_new_radio_formatter():
       # Test the new formatter
   ```

### Adding New Data Sources

1. **Extend Downloader**:
   ```python
   class NewSourceDownloader:
       # Implement download logic
   ```

2. **Update CLI**:
   ```python
   @click.option("--source", type=click.Choice(["repeaterbook", "newsource"]))
   ```

## Configuration

### Project Configuration (`pyproject.toml`)
- Package metadata and dependencies
- Tool configurations (Black, Flake8, pytest)
- Entry points for CLI commands

### Development Configuration
- Pre-commit hooks for code quality
- Test configuration and markers
- Development dependencies

## Testing Strategy

### Unit Tests
- Each module tested in isolation
- Mock external dependencies
- Test both success and failure cases

### Integration Tests
- Test CLI commands end-to-end
- Test data flow between modules
- Use fixtures for sample data

### Property-Based Testing
- Test data cleaning functions with varied inputs
- Validate formatter output constraints
- Ensure data integrity

## Performance Considerations

### Memory Efficiency
- Stream processing for large datasets
- Pandas operations optimized for memory usage
- Cleanup of temporary data

### Network Efficiency
- Connection pooling with requests.Session
- Appropriate timeouts and retries
- Respectful rate limiting

### Processing Efficiency
- Vectorized pandas operations
- Minimal data copying
- Efficient data structures

## Security Considerations

### Input Validation
- Validate all external inputs
- Sanitize file paths
- Check data types and ranges

### Network Security
- HTTPS connections only
- User-agent identification
- No credential storage

### File Security
- Safe file path handling
- Proper permissions checking
- No arbitrary code execution

## Future Enhancements

### Planned Features
1. **More Radio Models**: Yaesu, Icom, Kenwood support
2. **Advanced Filtering**: Frequency ranges, usage types, geographic filtering
3. **Data Caching**: Local storage to reduce API calls
4. **Configuration Files**: User preferences and default settings
5. **GUI Interface**: Desktop application for non-technical users

### Architecture Improvements
1. **Plugin System**: Dynamic loading of radio formatters
2. **Configuration Management**: Centralized settings system
3. **Async Support**: Concurrent downloads and processing
4. **Database Backend**: Local storage for large datasets
5. **REST API**: Web service interface

## Dependencies

### Core Dependencies
- **pandas**: Data manipulation and analysis
- **requests**: HTTP library for downloads
- **click**: Command-line interface framework
- **beautifulsoup4**: HTML parsing for web scraping
- **lxml**: XML/HTML parsing backend

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **pre-commit**: Git hooks for quality assurance
- **ipython**: Interactive development

## Maintenance

### Code Quality
- Automated formatting with Black
- Linting with Flake8
- Type hints for better maintainability
- Comprehensive docstrings

### Documentation
- Inline code documentation
- Architecture documentation
- User guides and examples
- API reference

### Testing
- Automated test suite
- Continuous integration
- Test coverage monitoring
- Performance benchmarks
