# Enhanced Radio Metadata

This document describes the enhanced radio metadata system that extends RadioBridge's capabilities beyond the basic 5-dimension metadata (manufacturer, model, version, firmware, CPS) to include comprehensive technical specifications.

## Quick Start

The enhanced metadata focuses on three priority fields you requested:

### 1. **Form Factor** - Physical radio type
- `Handheld` - Portable handheld radios
- `Mobile` - Vehicle/mobile installation radios
- `Base Station` - Desktop/base station radios

### 2. **Band Count** - Number of frequency bands supported
- `Single Band` - One frequency band (e.g., VHF only)
- `Dual Band` - Two bands (e.g., VHF/UHF)
- `Tri Band` - Three bands (e.g., VHF/UHF/1.25m)
- `Multi Band` - Four or more bands

### 3. **Maximum Transmission Power** - Highest power output
- Specified in watts (e.g., `5.0` for 5 watts)
- Can vary by band (VHF vs UHF power levels)

## Basic Usage

```python
from src.radiobridge.radios.enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel
)

# Create enhanced metadata
metadata = EnhancedRadioMetadata(
    # Basic fields (existing)
    manufacturer="Anytone",
    model="AT-D878UV II Plus",
    radio_version="Plus",
    firmware_versions=["1.24", "1.23"],
    cps_versions=["Anytone_CPS_3.00_3.08"],
    formatter_key="anytone-878",

    # Enhanced priority fields
    form_factor=FormFactor.HANDHELD,
    band_count=BandCount.DUAL_BAND,
    max_power_watts=5.0,

    # Optional detailed specifications
    frequency_ranges=[
        FrequencyRange("VHF", 136.0, 174.0),
        FrequencyRange("UHF", 400.0, 520.0)
    ],
    power_levels=[
        PowerLevel("High", 5.0, ["VHF"]),
        PowerLevel("High", 4.0, ["UHF"])
    ]
)

# Use the metadata
print(f"Radio: {metadata}")
# Output: Anytone AT-D878UV II Plus (Plus) - Handheld, Dual Band, 5.0W max

print(f"Supports 146.52 MHz: {metadata.supports_frequency(146.52)}")
# Output: True

print(f"Power at 440 MHz: {metadata.get_power_for_frequency(440.0)}W")
# Output: 4.0W
```

## Key Features

### ✅ **Backward Compatibility**
Enhanced metadata can convert to/from legacy RadioMetadata:

```python
# Convert to legacy for existing code
legacy = enhanced_metadata.to_legacy_metadata()

# Create enhanced from existing legacy metadata
enhanced = EnhancedRadioMetadata.from_legacy_metadata(
    legacy_metadata,
    form_factor=FormFactor.HANDHELD,
    band_count=BandCount.DUAL_BAND,
    max_power_watts=5.0
)
```

### ✅ **Smart Frequency/Power Queries**
```python
# Check if radio supports a frequency
if metadata.supports_frequency(146.520):
    power = metadata.get_power_for_frequency(146.520)
    print(f"Max power at 146.520 MHz: {power}W")

# Check band support
if metadata.supports_band("UHF"):
    print("Radio supports UHF band")
```

### ✅ **Rich Information Display**
```python
# Comprehensive radio information
print(f"Form Factor: {metadata.form_factor.value}")
print(f"Band Count: {metadata.band_count.value}")
print(f"Frequency Range: {metadata.frequency_range_mhz}")
print(f"Supported Bands: {metadata.supported_bands}")
print(f"Digital Modes: {metadata.digital_modes}")
print(f"Is Digital: {metadata.is_digital}")
```

## File Structure

```
src/radiobridge/radios/
├── enhanced_metadata.py          # Core enhanced metadata classes
└── metadata.py                   # Existing basic metadata (unchanged)

examples/
└── enhanced_anytone_878_example.py  # Complete working example

tests/
└── test_enhanced_metadata.py     # Comprehensive tests
```

## Example Implementation

See `examples/enhanced_anytone_878_example.py` for a complete example showing how to:

1. **Define enhanced metadata** for Anytone AT-D878UV II Plus and Standard variants
2. **Extend existing formatters** with enhanced metadata capabilities
3. **Query capabilities** like frequency support and power levels
4. **Maintain backward compatibility** with existing RadioMetadata

## Running the Example

```bash
# Run the complete example
cd /Users/craig/source_code/RadioBridge
python examples/enhanced_anytone_878_example.py
```

Expected output:
```
=== Enhanced Anytone AT-D878UV II Metadata ===

Radio: Anytone AT-D878UV II Plus (Plus) - Handheld, Dual Band, 5.0W max
  Form Factor: Handheld
  Band Count: Dual Band
  Max Power: 5.0W
  Frequency Range: 136.000 - 520.000 MHz
  Supported Bands: VHF, UHF
  Digital Modes: DMR
  Memory Channels: 4000
  GPS: Yes
  Bluetooth: Yes
  MSRP: $189.99

Radio: Anytone AT-D878UV II (Standard) - Handheld, Dual Band, 5.0W max
  Form Factor: Handheld
  Band Count: Dual Band
  Max Power: 5.0W
  Frequency Range: 136.000 - 520.000 MHz
  Supported Bands: VHF, UHF
  Digital Modes: DMR
  Memory Channels: 4000
  GPS: No
  Bluetooth: No
  MSRP: $169.99

=== Frequency Support Test ===
146.52 MHz: Plus=True, Standard=True, Power=5.0W
440.0 MHz: Plus=True, Standard=True, Power=4.0W
300.0 MHz: Plus=False, Standard=False, Power=0.0W
900.0 MHz: Plus=False, Standard=False, Power=0.0W

=== Backward Compatibility ===
Legacy format: RadioMetadata(manufacturer='Anytone', model='AT-D878UV II Plus', ...)
```

## Running Tests

```bash
# Run enhanced metadata tests
python -m pytest tests/test_enhanced_metadata.py -v
```

## Next Steps

1. **Populate enhanced metadata** for existing radios in the codebase
2. **Enhance CLI commands** to display and filter by new metadata fields
3. **Add validation** to ensure metadata consistency
4. **Create migration utilities** for bulk conversion of existing formatters
5. **Add more metadata fields** as needed (physical dimensions, digital capabilities, etc.)

## Benefits

- **Better User Experience**: Users can quickly find radios by form factor, band count, and power requirements
- **Smarter Recommendations**: System can suggest compatible radios based on technical needs
- **Enhanced CLI**: Richer `list-radios` output with filtering capabilities
- **Future-Proof**: Extensible structure for adding more metadata fields
- **Backward Compatible**: Existing code continues to work unchanged

This enhanced metadata system provides the foundation for making RadioBridge the definitive radio compatibility and specification database.
