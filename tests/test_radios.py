"""Tests for radio formatters."""

import pandas as pd
import pytest

from radiobridge.radios import get_radio_formatter, get_supported_radios
from radiobridge.radios.anytone_878 import Anytone878Formatter
from radiobridge.radios.base import BaseRadioFormatter


class TestRadioRegistry:
    """Test the radio formatter registry."""

    def test_get_supported_radios_returns_list(self):
        """Test that get_supported_radios returns a non-empty list."""
        radios = get_supported_radios()
        assert isinstance(radios, list)
        assert len(radios) > 0

        expected_radios = ["anytone-878", "anytone-578", "baofeng-dm32uv", "baofeng-k5"]
        for radio in expected_radios:
            assert radio in radios

    def test_get_radio_formatter_valid_radio(self):
        """Test getting formatter for valid radio."""
        formatter = get_radio_formatter("anytone-878")
        assert formatter is not None
        assert isinstance(formatter, BaseRadioFormatter)
        assert isinstance(formatter, Anytone878Formatter)

    def test_get_radio_formatter_case_insensitive(self):
        """Test that radio name lookup is case-insensitive."""
        formatter1 = get_radio_formatter("ANYTONE-878")
        formatter2 = get_radio_formatter("anytone-878")
        formatter3 = get_radio_formatter("Anytone-878")

        assert all(f is not None for f in [formatter1, formatter2, formatter3])
        assert all(
            isinstance(f, Anytone878Formatter)
            for f in [formatter1, formatter2, formatter3]
        )

    def test_get_radio_formatter_aliases(self):
        """Test that radio aliases work correctly."""
        # Test various aliases for Anytone 878
        aliases = ["878", "anytone878", "anytone_878"]

        for alias in aliases:
            formatter = get_radio_formatter(alias)
            assert formatter is not None
            assert isinstance(formatter, Anytone878Formatter)

    def test_get_radio_formatter_invalid_radio(self):
        """Test that invalid radio name returns None."""
        formatter = get_radio_formatter("nonexistent-radio")
        assert formatter is None


class TestAnytone878Formatter:
    """Test the Anytone 878 formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        formatter = Anytone878Formatter()

        assert formatter.radio_name == "Anytone AT-D878UV II (Plus)"
        assert "DMR" in formatter.description
        assert formatter.manufacturer == "Anytone"
        assert "frequency" in formatter.required_columns
        assert len(formatter.output_columns) > 0
        assert "Channel Number" in formatter.output_columns

    def test_format_basic_data(self):
        """Test formatting basic repeater data."""
        formatter = Anytone878Formatter()

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
        assert result.iloc[0]["Transmit Frequency"] == "147.120000"  # 146.52 + 0.6
        # Channel name is truncated to 16 chars for Anytone 878
        assert (
            "CALL1" in result.iloc[0]["Channel Name"]
            or "CALL" in result.iloc[0]["Channel Name"]
        )

    def test_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        formatter = Anytone878Formatter()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_format_missing_frequency_column_raises_error(self):
        """Test that missing required column raises ValueError."""
        formatter = Anytone878Formatter()
        data = pd.DataFrame({"tone": ["123.0"], "location": ["Test"]})

        with pytest.raises(ValueError, match="Missing required columns"):
            formatter.format(data)


class TestBaseFormatter:
    """Test the base formatter functionality."""

    def test_clean_frequency(self):
        """Test frequency cleaning function."""
        formatter = Anytone878Formatter()  # Use concrete class

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
        formatter = Anytone878Formatter()

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
        formatter = Anytone878Formatter()

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
        formatter = Anytone878Formatter()

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
        """Test Baofeng K5 formatter with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_k5 import BaofengK5Formatter

        formatter = BaofengK5Formatter()

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
        formatter = Anytone878Formatter()

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
        formatter = Anytone878Formatter()

        # Test data with no tone columns
        test_data = pd.DataFrame({"frequency": ["146.520"], "callsign": ["W1ABC"]})

        result = formatter.format(test_data)

        # Should default to 'Off'
        assert result.iloc[0]["CTCSS/DCS Encode"] == "Off"
        assert result.iloc[0]["CTCSS/DCS Decode"] == "Off"
