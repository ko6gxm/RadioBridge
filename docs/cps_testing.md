# CPS Version Testing Documentation

## Overview

The CPS (Customer Programming Software) version testing suite (`tests/test_cps_versions.py`) provides comprehensive testing for the CPS version validation and display functionality in RadioBridge.

## Test Structure

### Test Classes

1. **TestRadioMetadataCPSDisplay**
   - Tests CPS version display formatting in RadioMetadata
   - Covers range formatting, multi-word manufacturers, CHIRP versions, and edge cases

2. **TestCPSVersionValidation**
   - Tests CPS version validation logic
   - Covers exact matches, range validation, complex versions, and CHIRP dates

3. **TestCPSVersionRangeMatching**
   - Tests internal range matching methods
   - Covers version comparisons, date ranges, and invalid inputs

4. **TestCPSVersionEdgeCases**
   - Tests edge cases and error conditions
   - Covers empty metadata, malformed versions, and error handling

5. **TestIntegrationScenarios**
   - Tests realistic integration scenarios
   - Covers multi-radio configurations and cross-manufacturer validation

## Key Features Tested

### CPS Display Formatting
- **Range Format**: `"Anytone_CPS_3.00_3.08"` → `"Anytone-CPS 3.00-3.08"`
- **Single Version**: `"K5_CPS_2.1.8"` → `"K5-CPS 2.1.8"`
- **Multi-word Manufacturers**: `"DM_32UV_CPS_2.08_2.12"` → `"DM 32UV-CPS 2.08-2.12"`
- **CHIRP Versions**: `"CHIRP_next_20240801_20250401"` → `"CHIRP-next 20240801+"`

### CPS Validation
- **Exact Matches**: User input exactly matches supported version
- **Range Validation**: User version falls within supported version range
- **Complex Versions**: Handles version numbers like "2.0.6" with multiple decimal points
- **Multi-word Manufacturers**: Properly handles manufacturers like "DM 32UV"
- **CHIRP Date Validation**: Validates dates against CHIRP date ranges
- **Case Insensitivity**: Handles various capitalization formats

### Version Comparison Logic
- **Simple Versions**: Float comparison for versions like "3.05"
- **Complex Versions**: Semantic version comparison for versions like "2.0.6"
- **Date Ranges**: String comparison for YYYYMMDD date formats
- **Manufacturer Matching**: Dynamic CPS position detection for multi-word manufacturers

## Test Coverage

The test suite includes **27 comprehensive test cases** covering:

- ✅ Single and multiple CPS version formatting
- ✅ Range-based and exact version validation
- ✅ Complex version number handling (e.g., "2.0.6")
- ✅ Multi-word manufacturer support (e.g., "DM 32UV")
- ✅ CHIRP date range validation
- ✅ Case-insensitive input handling
- ✅ Edge cases and error conditions
- ✅ Cross-manufacturer validation
- ✅ Integration scenarios with real radio metadata

## Running the Tests

```bash
# Run all CPS version tests
python -m pytest tests/test_cps_versions.py -v

# Run specific test class
python -m pytest tests/test_cps_versions.py::TestCPSVersionValidation -v

# Run with coverage
python -m pytest tests/test_cps_versions.py --cov=radiobridge.radios
```

## Example Usage in Tests

```python
# Test CPS display formatting
metadata = RadioMetadata(
    manufacturer="Anytone",
    model="AT-D878UV",
    radio_version="Plus",
    firmware_versions=["1.24"],
    cps_versions=["Anytone_CPS_3.00_3.08"],
    formatter_key="anytone-878"
)

result = metadata._format_cps_display()
assert result == "Anytone-CPS 3.00-3.08"

# Test CPS validation
formatter = MockRadioFormatter([metadata])
assert formatter.validate_cps_version("Anytone CPS 3.05") is True
assert formatter.validate_cps_version("Anytone CPS 2.99") is False
```

## Integration with RadioBridge

The CPS testing suite validates the core functionality used by:

- **CLI Interface**: `rb list-radios` displays formatted CPS versions
- **Radio Formatters**: All radio formatters use CPS validation
- **User Input**: Command-line CPS version specifications are validated
- **Metadata Display**: Radio metadata shows human-readable CPS versions

This comprehensive testing ensures reliable CPS version handling across the entire RadioBridge system.
