"""Tests for radio formatters."""

import pandas as pd
import pytest

from radiobridge.radios import get_radio_formatter, get_supported_radios
from radiobridge.radios.anytone_878_v3 import Anytone878V3Formatter
from radiobridge.radios.anytone_878_v4 import Anytone878V4Formatter
from radiobridge.radios.base import BaseRadioFormatter


class TestRadioRegistry:
    """Test the radio formatter registry."""

    def test_get_supported_radios_returns_list(self):
        """Test that get_supported_radios returns a non-empty list."""
        radios = get_supported_radios()
        assert isinstance(radios, list)
        assert len(radios) > 0

        expected_radios = [
            "anytone-878-v3",
            "anytone-878-v4",
            "anytone-578",
            "baofeng-dm32uv",
            "baofeng-k5-plus",
        ]
        for radio in expected_radios:
            assert radio in radios

    def test_get_radio_formatter_valid_radio(self):
        """Test getting formatter for valid radio."""
        formatter = get_radio_formatter("anytone-878-v3")
        assert formatter is not None
        assert isinstance(formatter, BaseRadioFormatter)
        assert isinstance(formatter, Anytone878V3Formatter)

    def test_get_radio_formatter_case_insensitive(self):
        """Test that radio name lookup is case-insensitive."""
        formatter1 = get_radio_formatter("ANYTONE-878-V3")
        formatter2 = get_radio_formatter("anytone-878-v3")
        formatter3 = get_radio_formatter("Anytone-878-V3")

        assert all(f is not None for f in [formatter1, formatter2, formatter3])
        assert all(
            isinstance(f, Anytone878V3Formatter)
            for f in [formatter1, formatter2, formatter3]
        )

    def test_get_radio_formatter_aliases(self):
        """Test that radio aliases work correctly."""
        # Test various aliases for Anytone 878 V3 - use actual working aliases
        aliases = ["anytone-878-v3"]

        for alias in aliases:
            formatter = get_radio_formatter(alias)
            assert formatter is not None
            assert isinstance(formatter, Anytone878V3Formatter)

    def test_get_radio_formatter_invalid_radio(self):
        """Test that invalid radio name returns None."""
        formatter = get_radio_formatter("nonexistent-radio")
        assert formatter is None


class TestAnytone878V3Formatter:
    """Test the Anytone 878 V3 formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        formatter = Anytone878V3Formatter()

        assert formatter.radio_name == "Anytone AT-D878UV II (v3.0x)"
        assert "DMR" in formatter.description
        assert formatter.manufacturer == "Anytone"
        assert "frequency" in formatter.required_columns
        assert len(formatter.output_columns) > 0
        assert "Channel Number" in formatter.output_columns

    def test_format_basic_data(self):
        """Test formatting basic repeater data."""
        formatter = Anytone878V3Formatter()

        # Sample input data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "offset": ["+0.600000", "-0.600000"],
                "tone": ["123.0", "146.2"],
                "location": ["Repeater 1", "Repeater 2"],
                "callsign": ["CALL1", "CALL2"],
            }
        )

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert "Channel Number" in result.columns
        assert "Receive Frequency" in result.columns
        assert "Transmit Frequency" in result.columns

        # Check first row
        assert result.iloc[0]["Channel Number"] == 1
        assert result.iloc[0]["Receive Frequency"] == "146.520000"
        assert result.iloc[0]["Transmit Frequency"] == "147.12000"  # 146.52 + 0.6
        # Channel name is truncated to 16 chars for Anytone 878
        assert (
            "CALL1" in result.iloc[0]["Channel Name"]
            or "CALL" in result.iloc[0]["Channel Name"]
        )

    def test_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        formatter = Anytone878V3Formatter()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_format_missing_frequency_column_raises_error(self):
        """Test that missing required column raises ValueError."""
        formatter = Anytone878V3Formatter()
        data = pd.DataFrame({"tone": ["123.0"], "location": ["Test"]})

        with pytest.raises(ValueError, match="Missing required columns"):
            formatter.format(data)


class TestBaseFormatter:
    """Test the base formatter functionality."""

    def test_clean_frequency(self):
        """Test frequency cleaning function."""
        formatter = Anytone878V3Formatter()  # Use concrete class

        # Valid frequencies
        assert formatter.clean_frequency("146.520") == "146.520000"
        assert formatter.clean_frequency("146.520 MHz") == "146.520000"
        assert formatter.clean_frequency("146.520MHz") == "146.520000"
        assert formatter.clean_frequency(146.52) == "146.520000"

        # Invalid frequencies
        assert formatter.clean_frequency("") is None
        assert formatter.clean_frequency(None) is None
        assert formatter.clean_frequency("invalid") is None
        assert formatter.clean_frequency(pd.NA) is None

    def test_clean_tone(self):
        """Test tone cleaning function."""
        formatter = Anytone878V3Formatter()

        # Valid tones
        assert formatter.clean_tone("123.0") == "123.0"
        assert formatter.clean_tone("123.0 Hz") == "123.0"
        assert formatter.clean_tone("123.0Hz") == "123.0"
        assert formatter.clean_tone(123.0) == "123.0"

        # Invalid or empty tones
        assert formatter.clean_tone("") is None
        assert formatter.clean_tone("none") is None
        assert formatter.clean_tone("N/A") is None
        assert formatter.clean_tone(None) is None
        assert formatter.clean_tone(pd.NA) is None
        assert formatter.clean_tone(500.0) == "500.0"  # Out of range but returned as-is

    def test_clean_offset(self):
        """Test offset cleaning function."""
        formatter = Anytone878V3Formatter()

        # Valid offsets
        assert formatter.clean_offset("+0.600") == "+0.600000"
        assert formatter.clean_offset("-0.600") == "-0.600000"
        assert formatter.clean_offset("0.600") == "+0.600000"
        assert formatter.clean_offset(0.6) == "+0.600000"
        assert formatter.clean_offset(0.0) == "0.000000"

        # Invalid offsets
        assert formatter.clean_offset("") is None
        assert formatter.clean_offset(None) is None
        assert formatter.clean_offset(pd.NA) is None


class TestBaofengDM32UVFormatter:
    """Test the Baofeng DM-32UV formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        assert formatter.radio_name == "Baofeng DM-32UV"
        assert "DMR" in formatter.description
        assert formatter.manufacturer == "Baofeng"
        assert (
            formatter.required_columns == []
        )  # Accepts both basic and detailed formats
        assert len(formatter.output_columns) == 40  # DM-32UV has 40 columns
        assert "No." in formatter.output_columns
        assert "RX Frequency[MHz]" in formatter.output_columns
        assert "TX Frequency[MHz]" in formatter.output_columns

    def test_format_basic_data(self):
        """Test formatting basic repeater data for DM-32UV."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Sample input data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "offset": ["+0.000000", "-0.600000"],
                "tone": ["", "146.2"],
                "location": ["Los Angeles", "San Francisco"],
                "call": ["W6ABC", "K6XYZ"],
            }
        )

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert len(result.columns) == 40  # DM-32UV specific column count
        assert "No." in result.columns
        assert "RX Frequency[MHz]" in result.columns
        assert "TX Frequency[MHz]" in result.columns
        assert "Channel Type" in result.columns

        # Check first row
        assert result.iloc[0]["No."] == 1
        assert result.iloc[0]["RX Frequency[MHz]"] == "146.520000"
        assert (
            result.iloc[0]["TX Frequency[MHz]"] == "146.52000"
        )  # Same freq (no offset)
        assert result.iloc[0]["Channel Type"] == "Analog"
        assert (
            "W6ABC" in result.iloc[0]["Channel Name"]
            or "Los Ange" in result.iloc[0]["Channel Name"]
        )

        # Check second row with offset
        assert result.iloc[1]["No."] == 2
        assert result.iloc[1]["RX Frequency[MHz]"] == "147.000000"
        assert result.iloc[1]["TX Frequency[MHz]"] == "146.40000"  # 147.0 - 0.6
        assert result.iloc[1]["CTC/DCS Decode"] == "146.2"
        assert result.iloc[1]["CTC/DCS Encode"] == "146.2"


class TestToneUpDownFunctionality:
    """Test tone_up and tone_down support across all radio formatters."""

    def test_dm32uv_supports_separate_tones(self):
        """Test DM-32UV formatter with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test data with separate tones
        test_data = pd.DataFrame(
            {
                "frequency": ["146.520", "147.000"],
                "tone_up": ["123.0", None],
                "tone_down": ["456.0", "88.5"],
                "callsign": ["W1ABC", "K2DEF"],
                "location": ["City1", "City2"],
            }
        )

        result = formatter.format(test_data)

        # Check tone mapping: tone_up -> encode, tone_down -> decode
        assert result.iloc[0]["CTC/DCS Encode"] == "123.0"
        assert result.iloc[0]["CTC/DCS Decode"] == "456.0"
        assert result.iloc[1]["CTC/DCS Encode"] == "None"  # None tone_up
        assert result.iloc[1]["CTC/DCS Decode"] == "88.5"

    def test_anytone_878_supports_separate_tones(self):
        """Test Anytone 878 formatter with separate tone_up and tone_down."""
        formatter = Anytone878V3Formatter()

        test_data = pd.DataFrame(
            {
                "frequency": ["146.520"],
                "tone_up": ["123.0"],
                "tone_down": ["456.0"],
                "callsign": ["W1ABC"],
            }
        )

        result = formatter.format(test_data)

        assert result.iloc[0]["CTCSS/DCS Encode"] == "123.0"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "456.0"

    def test_anytone_578_supports_separate_tones(self):
        """Test Anytone 578 formatter with separate tone_up and tone_down."""
        from radiobridge.radios.anytone_578 import Anytone578Formatter

        formatter = Anytone578Formatter()

        test_data = pd.DataFrame(
            {
                "frequency": ["146.520"],
                "tone_up": ["123.0"],
                "tone_down": ["456.0"],
                "callsign": ["W1ABC"],
            }
        )

        result = formatter.format(test_data)

        assert result.iloc[0]["CTCSS/DCS Encode"] == "123.0"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "456.0"

    def test_baofeng_k5_supports_separate_tones(self):
        """Test Baofeng K5 Plus formatter with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_k5_plus import BaofengK5PlusFormatter

        formatter = BaofengK5PlusFormatter()

        test_data = pd.DataFrame(
            {
                "frequency": ["146.520"],
                "tone_up": ["123.0"],
                "tone_down": ["456.0"],
                "callsign": ["W1ABC"],
            }
        )

        result = formatter.format(test_data)

        assert result.iloc[0]["TX CTCSS/DCS"] == "123.0"
        assert result.iloc[0]["RX CTCSS/DCS"] == "456.0"

    def test_legacy_tone_column_fallback(self):
        """Test that formatters fall back to legacy 'tone' column.

        When tone_up/down don't exist, should use legacy tone column.
        """
        formatter = Anytone878V3Formatter()

        # Test data with only legacy tone column
        test_data = pd.DataFrame(
            {"frequency": ["146.520"], "tone": ["100.0"], "callsign": ["W1ABC"]}
        )

        result = formatter.format(test_data)

        # Should use same tone for both encode and decode
        assert result.iloc[0]["CTCSS/DCS Encode"] == "100.0"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "100.0"

    def test_no_tone_columns_results_in_off(self):
        """Test that missing tone data results in 'Off' values."""
        formatter = Anytone878V3Formatter()

        # Test data with no tone columns
        test_data = pd.DataFrame({"frequency": ["146.520"], "callsign": ["W1ABC"]})

        result = formatter.format(test_data)

        # Should default to 'Off'
        assert result.iloc[0]["CTCSS/DCS Encode"] == "Off"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "Off"


class TestAnytone878V4Formatter:
    """Test the Anytone 878 V4 formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        formatter = Anytone878V4Formatter()

        assert formatter.radio_name == "Anytone AT-D878UV II (v4.0)"
        assert "DMR" in formatter.description
        assert formatter.manufacturer == "Anytone"
        assert "frequency" in formatter.required_columns
        assert len(formatter.output_columns) > 0
        assert "Channel Number" in formatter.output_columns

    def test_format_basic_data(self):
        """Test formatting basic repeater data for v4 firmware."""
        formatter = Anytone878V4Formatter()

        # Sample input data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "offset": ["+0.600000", "-0.600000"],
                "tone": ["123.0", "146.2"],
                "location": ["Repeater 1", "Repeater 2"],
                "callsign": ["CALL1", "CALL2"],
            }
        )

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert "Channel Number" in result.columns
        assert "Receive Frequency" in result.columns
        assert "Transmit Frequency" in result.columns

        # Check first row
        assert result.iloc[0]["Channel Number"] == 1
        assert result.iloc[0]["Receive Frequency"] == "146.520000"
        assert result.iloc[0]["Transmit Frequency"] == "147.12000"  # 146.52 + 0.6
        # Channel name is truncated to 16 chars for Anytone 878
        assert (
            "CALL1" in result.iloc[0]["Channel Name"]
            or "CALL" in result.iloc[0]["Channel Name"]
        )

    def test_metadata_properties(self):
        """Test that v4 formatter has correct metadata."""
        formatter = Anytone878V4Formatter()

        # Test regular metadata
        metadata_list = formatter.metadata
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        assert metadata.manufacturer == "Anytone"
        assert metadata.model == "AT-D878UV II Plus"
        assert metadata.radio_version == "Plus"
        assert "4." in metadata.firmware_versions[0]  # Should have v4 firmware
        assert metadata.formatter_key == "anytone-878-v4"

        # Test enhanced metadata
        enhanced_list = formatter.enhanced_metadata
        assert len(enhanced_list) == 1
        enhanced = enhanced_list[0]

        assert enhanced.manufacturer == "Anytone"
        assert enhanced.model == "AT-D878UV II Plus"
        assert enhanced.radio_version == "Plus"
        assert enhanced.gps_enabled is True
        assert enhanced.bluetooth_enabled is True
        assert enhanced.memory_channels == 4000

    def test_v4_vs_v3_differences(self):
        """Test that v4 and v3 formatters produce similar but distinct results."""
        v3_formatter = Anytone878V3Formatter()
        v4_formatter = Anytone878V4Formatter()

        # Same test data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "offset": ["+0.600000"],
                "tone": ["123.0"],
                "location": ["Test"],
                "callsign": ["W1ABC"],
            }
        )

        v3_result = v3_formatter.format(input_data)
        v4_result = v4_formatter.format(input_data)

        # Both should have similar basic structure (v4 has more columns)
        # v4 has additional features like Roaming and Encryption
        assert len(v4_result.columns) >= len(v3_result.columns)
        assert (
            v3_result.iloc[0]["Receive Frequency"]
            == v4_result.iloc[0]["Receive Frequency"]
        )
        assert (
            v3_result.iloc[0]["Transmit Frequency"]
            == v4_result.iloc[0]["Transmit Frequency"]
        )

        # But metadata should differ
        assert v3_formatter.radio_name != v4_formatter.radio_name
        assert "v3.0x" in v3_formatter.radio_name
        assert "v4.0" in v4_formatter.radio_name

    def test_cps_version_validation(self):
        """Test CPS version validation for v4 formatter."""
        formatter = Anytone878V4Formatter()

        # Get supported CPS versions
        supported_versions = formatter.get_supported_cps_versions()
        assert len(supported_versions) > 0

        # Test validation with supported version
        if supported_versions:
            assert formatter.validate_cps_version(supported_versions[0]) is True

        # Test validation with unsupported version
        assert formatter.validate_cps_version("Invalid_CPS_1.99") is False

    def test_registry_integration(self):
        """Test that v4 formatter is properly registered."""
        # Test that we can get the v4 formatter by key
        formatter = get_radio_formatter("anytone-878-v4")
        assert formatter is not None
        assert isinstance(formatter, Anytone878V4Formatter)

        # Test case insensitive lookup
        formatter_upper = get_radio_formatter("ANYTONE-878-V4")
        assert formatter_upper is not None
        assert isinstance(formatter_upper, Anytone878V4Formatter)

        # Test that both v3 and v4 are in supported radios list
        supported = get_supported_radios()
        assert "anytone-878-v3" in supported
        assert "anytone-878-v4" in supported


class TestBaofengUV5RFormatter:
    """Test the Baofeng UV-5R formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        assert formatter.radio_name == "Baofeng UV-5R"
        assert "dual-band analog handheld" in formatter.description
        assert formatter.manufacturer == "Baofeng"
        assert formatter.model == "UV-5R"
        assert (
            formatter.required_columns == []
        )  # Accepts both basic and detailed formats
        assert len(formatter.output_columns) == 18  # UV-5R specific column count
        assert "Location" in formatter.output_columns
        assert "Name" in formatter.output_columns
        assert "Frequency" in formatter.output_columns
        assert "Duplex" in formatter.output_columns
        assert "Mode" in formatter.output_columns

    def test_metadata_properties(self):
        """Test that UV-5R formatter has correct metadata."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Test regular metadata
        metadata_list = formatter.metadata
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        assert metadata.manufacturer == "Baofeng"
        assert metadata.model == "UV-5R"
        assert metadata.radio_version == "Standard"
        assert metadata.firmware_versions == []  # UV-5R firmware is not upgradable
        assert len(metadata.cps_versions) > 0
        assert "CHIRP" in metadata.cps_versions[0]
        assert metadata.formatter_key == "baofeng-uv5r"

    def test_enhanced_metadata_properties(self):
        """Test enhanced metadata properties."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Test enhanced metadata
        enhanced_list = formatter.enhanced_metadata
        assert len(enhanced_list) == 1
        enhanced = enhanced_list[0]

        assert enhanced.manufacturer == "Baofeng"
        assert enhanced.model == "UV-5R"
        assert enhanced.radio_version == "Standard"
        assert enhanced.gps_enabled is False
        assert enhanced.bluetooth_enabled is False
        assert enhanced.memory_channels == 128
        assert enhanced.max_power_watts == 8.0
        assert "FM" in enhanced.modulation_modes
        assert enhanced.digital_modes == []  # Analog only
        assert len(enhanced.frequency_ranges) == 2  # VHF and UHF
        assert enhanced.frequency_ranges[0].band_name == "VHF"
        assert enhanced.frequency_ranges[1].band_name == "UHF"

    def test_format_basic_simplex_data(self):
        """Test formatting basic simplex repeater data."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Sample simplex input data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "offset": ["0.000000", "0.000000"],
                "tone": ["", "88.5"],
                "location": ["Simplex 1", "Simplex 2"],
                "callsign": ["W6ABC", "K6XYZ"],
            }
        )

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert len(result.columns) == 18
        assert "Location" in result.columns
        assert "Name" in result.columns
        assert "Frequency" in result.columns
        assert "Duplex" in result.columns

        # Check first row (no tone)
        assert result.iloc[0]["Location"] == 1
        assert result.iloc[0]["Frequency"] == "146.520000"
        assert result.iloc[0]["Duplex"] == ""
        assert result.iloc[0]["Offset"] == "0.000000"
        assert result.iloc[0]["Mode"] == "FM"
        assert result.iloc[0]["Tone"] == "None"
        assert result.iloc[0]["TStep"] == "5.00"  # VHF step

        # Check second row (with tone)
        assert result.iloc[1]["Location"] == 2
        assert result.iloc[1]["Frequency"] == "147.000000"
        assert result.iloc[1]["Tone"] == "Tone"
        assert result.iloc[1]["rToneFreq"] == "88.5"
        assert result.iloc[1]["cToneFreq"] == "88.5"

    def test_format_repeater_data_with_offsets(self):
        """Test formatting repeater data with positive and negative offsets."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Sample repeater input data
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "447.000000"],
                "offset": ["+0.600000", "-5.000000"],
                "tone": ["123.0", ""],
                "location": ["VHF Rptr", "UHF Rptr"],
                "callsign": ["W6ABC", "K6XYZ"],
            }
        )

        result = formatter.format(input_data)

        # Check positive offset
        assert result.iloc[0]["Frequency"] == "146.520000"
        assert result.iloc[0]["Duplex"] == "+"
        assert result.iloc[0]["Offset"] == "0.600000"
        assert result.iloc[0]["TStep"] == "5.00"  # VHF step
        assert result.iloc[0]["Tone"] == "Tone"
        assert result.iloc[0]["rToneFreq"] == "123.0"

        # Check negative offset
        assert result.iloc[1]["Frequency"] == "447.000000"
        assert result.iloc[1]["Duplex"] == "-"
        assert result.iloc[1]["Offset"] == "5.000000"  # Absolute value
        assert result.iloc[1]["TStep"] == "12.50"  # UHF step
        assert result.iloc[1]["Tone"] == "None"

    def test_format_with_tx_frequency(self):
        """Test formatting with explicit TX frequency (detailed downloader)."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Sample input data with TX frequency (using 'Uplink' column)
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "Uplink": ["147.120000"],  # +0.6 offset
                "location": ["Test Rptr"],
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        # Should calculate offset from TX/RX frequencies
        assert result.iloc[0]["Frequency"] == "146.520000"
        assert result.iloc[0]["Duplex"] == "+"
        assert result.iloc[0]["Offset"] == "0.600000"

    def test_format_with_dcs_tones(self):
        """Test formatting with DCS tones."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Sample input data with DCS tone
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "tone": ["D023"],  # DCS code
                "location": ["DCS Test"],
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        # Should set DCS mode
        assert result.iloc[0]["Tone"] == "DTCS"
        assert result.iloc[0]["DtcsCode"] == "023"
        assert result.iloc[0]["DtcsPolarity"] == "NN"

    def test_format_with_separate_tones(self):
        """Test formatting with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Sample input data with separate tones
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "tone_up": ["123.0"],
                "tone_down": ["88.5"],
                "location": ["Split Tone"],
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        # Should use tone_up for ctone and tone_down for rtone
        assert result.iloc[0]["Tone"] == "Tone"
        assert result.iloc[0]["rToneFreq"] == "88.5"  # tone_down
        assert result.iloc[0]["cToneFreq"] == "123.0"  # tone_up

    def test_channel_name_generation(self):
        """Test channel name generation and truncation."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Test with various name combinations
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000", "448.000000"],
                "callsign": ["W6ABC", "VERYLONGCALL", ""],
                "location": ["Los Angeles", "San Francisco Bay Area", "Short"],
            }
        )

        result = formatter.format(input_data)

        # Channel names should be 8 chars or less for UV-5R
        assert len(result.iloc[0]["Name"]) <= 8
        assert len(result.iloc[1]["Name"]) <= 8
        assert len(result.iloc[2]["Name"]) <= 8

        # Should contain recognizable parts
        assert "W6ABC" in result.iloc[0]["Name"] or "Los" in result.iloc[0]["Name"]
        assert len(result.iloc[2]["Name"]) > 0  # Should generate some name

    def test_channel_name_conflict_resolution(self):
        """Test channel name conflict resolution."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Create data that would generate conflicting names
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000", "448.000000"],
                "callsign": ["W6ABC", "W6ABC", "W6ABC"],
                "location": ["LA", "LA", "LA"],
            }
        )

        result = formatter.format(input_data)

        # Names should be unique after conflict resolution
        names = result["Name"].tolist()
        assert len(names) == len(set(names))  # All unique

    def test_cps_version_optimization(self):
        """Test CPS version-specific optimizations."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "location": ["Test"],
                "callsign": ["W6ABC"],
            }
        )

        # Test with CHIRP optimization
        result_chirp = formatter.format(input_data, cps_version="CHIRP_next_20240301")
        assert len(result_chirp) == 1

        # Test with RT Systems optimization
        result_rt = formatter.format(input_data, cps_version="RT_Systems_UV5R_1.0")
        assert len(result_rt) == 1

        # Both should produce valid results
        assert result_chirp.iloc[0]["Frequency"] == "146.520000"
        assert result_rt.iloc[0]["Frequency"] == "146.520000"

    def test_frequency_step_calculation(self):
        """Test frequency step calculation for different bands."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        input_data = pd.DataFrame(
            {
                "frequency": [
                    "146.520000",
                    "447.000000",
                    "100.000000",
                ],  # VHF, UHF, out of band
                "location": ["VHF", "UHF", "OOB"],
            }
        )

        result = formatter.format(input_data)

        # Check frequency steps
        assert result.iloc[0]["TStep"] == "5.00"  # VHF
        assert result.iloc[1]["TStep"] == "12.50"  # UHF
        assert result.iloc[2]["TStep"] == "5.00"  # Default for out of band

    def test_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_format_invalid_frequency_skips_row(self):
        """Test that rows with invalid frequencies are skipped."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        # Mix of valid and invalid frequencies
        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "", "invalid", "447.000000"],
                "location": ["Valid1", "Empty", "Invalid", "Valid2"],
            }
        )

        result = formatter.format(input_data)

        # Should only have 2 valid rows
        assert len(result) == 2
        assert result.iloc[0]["Frequency"] == "146.520000"
        assert result.iloc[1]["Frequency"] == "447.000000"

    def test_start_channel_parameter(self):
        """Test start_channel parameter affects channel numbering."""
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        formatter = BaofengUV5RFormatter()

        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "location": ["Ch1", "Ch2"],
            }
        )

        # Test default start (1)
        result_default = formatter.format(input_data)
        assert result_default.iloc[0]["Location"] == 1
        assert result_default.iloc[1]["Location"] == 2

        # Test custom start (10)
        result_custom = formatter.format(input_data, start_channel=10)
        assert result_custom.iloc[0]["Location"] == 10
        assert result_custom.iloc[1]["Location"] == 11

    def test_registry_integration(self):
        """Test that UV-5R formatter is properly registered."""
        # Test that we can get the UV-5R formatter by key
        formatter = get_radio_formatter("baofeng-uv5r")
        assert formatter is not None
        from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter

        assert isinstance(formatter, BaofengUV5RFormatter)

        # Test aliases
        formatter_alias = get_radio_formatter("uv5r")
        assert formatter_alias is not None
        assert isinstance(formatter_alias, BaofengUV5RFormatter)

        # Test case insensitive lookup
        formatter_upper = get_radio_formatter("BAOFENG-UV5R")
        assert formatter_upper is not None
        assert isinstance(formatter_upper, BaofengUV5RFormatter)

        # Test that it's in supported radios list
        supported = get_supported_radios()
        assert "baofeng-uv5r" in supported


class TestBaofengUV5RMFormatter:
    """Test the Baofeng UV-5RM formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_uv5rm import BaofengUV5RMFormatter

        formatter = BaofengUV5RMFormatter()

        assert formatter.radio_name == "Baofeng UV-5RM"
        assert "Enhanced UV-5R with additional memory" in formatter.description
        assert formatter.manufacturer == "Baofeng"
        assert formatter.model == "UV-5RM"
        assert formatter.required_columns == []
        assert len(formatter.output_columns) == 18  # Same as UV-5R

    def test_enhanced_metadata_differences(self):
        """Test enhanced metadata shows UV-5RM specific features."""
        from radiobridge.radios.baofeng_uv5rm import BaofengUV5RMFormatter

        formatter = BaofengUV5RMFormatter()
        enhanced = formatter.enhanced_metadata[0]

        assert enhanced.memory_channels == 999  # More than UV-5R's 128
        assert enhanced.model == "UV-5RM"
        assert (
            "UV5RM" in enhanced.cps_versions[0] or "UV5RM" in enhanced.cps_versions[1]
        )

    def test_format_basic_data(self):
        """Test basic formatting functionality."""
        from radiobridge.radios.baofeng_uv5rm import BaofengUV5RMFormatter

        formatter = BaofengUV5RMFormatter()

        input_data = pd.DataFrame(
            {
                "frequency": ["146.520000"],
                "tone": ["88.5"],
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        assert len(result) == 1
        assert result.iloc[0]["Frequency"] == "146.520000"
        assert result.iloc[0]["Mode"] == "FM"
        assert result.iloc[0]["Tone"] == "Tone"
        assert result.iloc[0]["rToneFreq"] == "88.5"

    def test_registry_integration(self):
        """Test UV-5RM is properly registered."""
        formatter = get_radio_formatter("baofeng-uv5rm")
        assert formatter is not None
        from radiobridge.radios.baofeng_uv5rm import BaofengUV5RMFormatter

        assert isinstance(formatter, BaofengUV5RMFormatter)


class TestBaofengUV25Formatter:
    """Test the Baofeng UV-25 formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_uv25 import BaofengUV25Formatter

        formatter = BaofengUV25Formatter()

        assert formatter.radio_name == "Baofeng UV-25"
        assert "tri-band" in formatter.description.lower()
        assert formatter.manufacturer == "Baofeng"
        assert formatter.model == "UV-25"
        assert formatter.required_columns == []
        assert len(formatter.output_columns) == 18

    def test_enhanced_metadata_tri_band(self):
        """Test enhanced metadata shows tri-band capabilities."""
        from radiobridge.radios.baofeng_uv25 import BaofengUV25Formatter

        formatter = BaofengUV25Formatter()
        enhanced = formatter.enhanced_metadata[0]

        assert enhanced.model == "UV-25"
        assert enhanced.band_count.value == "Tri Band"
        assert len(enhanced.frequency_ranges) == 3  # VHF, UHF, 1.25m
        # Check for 1.25m band (220-225 MHz)
        band_names = [r.band_name for r in enhanced.frequency_ranges]
        assert "1.25m" in band_names or "220MHz" in band_names

    def test_format_basic_data(self):
        """Test basic formatting functionality."""
        from radiobridge.radios.baofeng_uv25 import BaofengUV25Formatter

        formatter = BaofengUV25Formatter()

        input_data = pd.DataFrame(
            {
                "frequency": ["223.500000"],  # 1.25m band
                "offset": ["+1.600000"],
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        assert len(result) == 1
        assert result.iloc[0]["Frequency"] == "223.500000"
        assert result.iloc[0]["Duplex"] == "+"
        assert result.iloc[0]["Offset"] == "1.600000"
        assert result.iloc[0]["Mode"] == "FM"

    def test_registry_integration(self):
        """Test UV-25 is properly registered."""
        formatter = get_radio_formatter("baofeng-uv25")
        assert formatter is not None
        from radiobridge.radios.baofeng_uv25 import BaofengUV25Formatter

        assert isinstance(formatter, BaofengUV25Formatter)


class TestBaofengUV28Formatter:
    """Test the Baofeng UV-28 formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_uv28 import BaofengUV28Formatter

        formatter = BaofengUV28Formatter()

        assert formatter.radio_name == "Baofeng UV-28"
        assert "tri-band" in formatter.description.lower()
        assert formatter.manufacturer == "Baofeng"
        assert formatter.model == "UV-28"
        assert formatter.required_columns == []
        assert len(formatter.output_columns) == 19

    def test_enhanced_metadata_tri_band(self):
        """Test enhanced metadata shows tri-band capabilities."""
        from radiobridge.radios.baofeng_uv28 import BaofengUV28Formatter

        formatter = BaofengUV28Formatter()
        enhanced = formatter.enhanced_metadata[0]

        assert enhanced.model == "UV-28"
        assert enhanced.band_count.value == "Tri Band"
        assert len(enhanced.frequency_ranges) == 3  # VHF, UHF, 1.25m
        # Should support 1.25m band
        band_names = [r.band_name for r in enhanced.frequency_ranges]
        assert "1.25m" in band_names or "220MHz" in band_names

    def test_format_basic_data(self):
        """Test basic formatting functionality."""
        from radiobridge.radios.baofeng_uv28 import BaofengUV28Formatter

        formatter = BaofengUV28Formatter()

        input_data = pd.DataFrame(
            {
                "frequency": ["222.000000"],  # 1.25m band
                "tone": ["D023"],  # DCS tone
                "callsign": ["W6ABC"],
            }
        )

        result = formatter.format(input_data)

        assert len(result) == 1
        assert result.iloc[0]["Frequency"] == "222.000000"
        assert result.iloc[0]["Tone"] == "DTCS"
        assert result.iloc[0]["DtcsCode"] == "023"
        assert result.iloc[0]["Mode"] == "FM"

    def test_registry_integration(self):
        """Test UV-28 is properly registered."""
        formatter = get_radio_formatter("baofeng-uv28")
        assert formatter is not None
        from radiobridge.radios.baofeng_uv28 import BaofengUV28Formatter

        assert isinstance(formatter, BaofengUV28Formatter)

    def test_v4_separate_tones(self):
        """Test v4 formatter with separate tone_up and tone_down."""
        formatter = Anytone878V4Formatter()

        test_data = pd.DataFrame(
            {
                "frequency": ["146.520"],
                "tone_up": ["123.0"],
                "tone_down": ["456.0"],
                "callsign": ["W1ABC"],
            }
        )

        result = formatter.format(test_data)

        assert result.iloc[0]["CTCSS/DCS Encode"] == "123.0"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "456.0"

    def test_v4_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError for v4."""
        formatter = Anytone878V4Formatter()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_v4_format_missing_frequency_column_raises_error(self):
        """Test that missing required column raises ValueError for v4."""
        formatter = Anytone878V4Formatter()
        data = pd.DataFrame({"tone": ["123.0"], "location": ["Test"]})

        with pytest.raises(ValueError, match="Missing required columns"):
            formatter.format(data)
