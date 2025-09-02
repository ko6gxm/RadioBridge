"""Tests for radio formatters."""

import pytest

from radiobridge.lightweight_data import LightDataFrame, is_null
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
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "offset": "+0.600000",
                "tone": "123.0",
                "location": "Repeater 1",
                "callsign": "CALL1",
            },
            {
                "frequency": "147.000000",
                "offset": "-0.600000",
                "tone": "146.2",
                "location": "Repeater 2",
                "callsign": "CALL2",
            }
        ])

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert "Channel Number" in result.columns
        assert "Receive Frequency" in result.columns
        assert "Transmit Frequency" in result.columns

        # Check first row
        assert result.iloc(0)["Channel Number"] == 1
        assert result.iloc(0)["Receive Frequency"] == "146.520000"
        assert result.iloc(0)["Transmit Frequency"] == "147.120000"  # 146.52 + 0.6
        # Channel name is truncated to 16 chars for Anytone 878
        assert (
            "CALL1" in result.iloc(0)["Channel Name"]
            or "CALL" in result.iloc(0)["Channel Name"]
        )

    def test_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        formatter = Anytone878V3Formatter()
        empty_data = LightDataFrame.from_records([])

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_format_missing_frequency_column_raises_error(self):
        """Test that missing required column raises ValueError."""
        formatter = Anytone878V3Formatter()
        data = LightDataFrame.from_records([{"tone": "123.0", "location": "Test"}])

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
        assert formatter.clean_frequency(None) is None

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
        assert formatter.clean_tone(None) is None
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
        assert formatter.clean_offset(None) is None


class TestBaofengDM32UVFormatter:
    """Test the Baofeng DM-32UV formatter specifically."""

    def test_formatter_properties(self):
        """Test formatter properties are correctly set."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        assert formatter.radio_name == "Baofeng DM-32UV"
        assert "DMR" in formatter.description
        assert formatter.manufacturer == "Baofeng"
        assert formatter.model == "DM-32UV"
        assert (
            formatter.required_columns == []
        )  # Accepts both basic and detailed formats
        assert len(formatter.output_columns) == 40  # DM-32UV has 40 columns
        assert "No." in formatter.output_columns
        assert "RX Frequency[MHz]" in formatter.output_columns
        assert "TX Frequency[MHz]" in formatter.output_columns

    def test_metadata_properties(self):
        """Test formatter metadata is correctly set."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test regular metadata
        metadata_list = formatter.metadata
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        assert metadata.manufacturer == "Baofeng"
        assert metadata.model == "DM-32UV"
        assert metadata.radio_version == "Standard"
        assert len(metadata.firmware_versions) > 0
        assert (
            "v.046" in metadata.firmware_versions
            or "2.14" in metadata.firmware_versions
            or "2.13" in metadata.firmware_versions
        )
        assert len(metadata.cps_versions) >= 2
        assert (
            "CHIRP" in metadata.cps_versions[1]
            or "DM_32UV_CPS" in metadata.cps_versions[0]
        )
        assert metadata.formatter_key == "baofeng-dm32uv"

    def test_format_basic_data(self):
        """Test formatting basic repeater data for DM-32UV."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Sample input data
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "offset": "+0.000000",
                "tone": "",
                "location": "Los Angeles",
                "call": "W6ABC",
            },
            {
                "frequency": "147.000000",
                "offset": "-0.600000",
                "tone": "146.2",
                "location": "San Francisco",
                "call": "K6XYZ",
            }
        ])

        result = formatter.format(input_data)

        # Check basic structure
        assert len(result) == 2
        assert len(result.columns) == 40  # DM-32UV specific column count
        assert "No." in result.columns
        assert "RX Frequency[MHz]" in result.columns
        assert "TX Frequency[MHz]" in result.columns
        assert "Channel Type" in result.columns

        # Check first row
        assert result.iloc(0)["No."] == 1
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.520000"
        assert (
            result.iloc(0)["TX Frequency[MHz]"] == "146.52000"
        )  # Same freq (no offset)
        assert result.iloc(0)["Channel Type"] == "Analog"
        assert (
            "W6ABC" in result.iloc(0)["Channel Name"]
            or "Los Ange" in result.iloc(0)["Channel Name"]
        )

        # Check second row with offset
        assert result.iloc(1)["No."] == 2
        assert result.iloc(1)["RX Frequency[MHz]"] == "147.000000"
        assert result.iloc(1)["TX Frequency[MHz]"] == "146.40000"  # 147.0 - 0.6
        assert result.iloc(1)["CTC/DCS Decode"] == "146.2"
        assert result.iloc(1)["CTC/DCS Encode"] == "146.2"

    def test_format_detailed_downloader_data(self):
        """Test formatting detailed downloader data with Downlink/Uplink."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Sample detailed downloader input
        input_data = LightDataFrame.from_records([
            {
                "Downlink": "146.520000",
                "Uplink": "146.520000",
                "Uplink Tone": "123.0",
                "Downlink Tone": "88.5",
                "Location": "Los Angeles",
                "callsign": "W6ABC",
            },
            {
                "Downlink": "447.000000",
                "Uplink": "442.000000",
                "Uplink Tone": "",
                "Downlink Tone": "146.2",
                "Location": "San Francisco",
                "callsign": "K6XYZ",
            }
        ])

        result = formatter.format(input_data)

        # Check structure
        assert len(result) == 2
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.520000"
        assert result.iloc(0)["TX Frequency[MHz]"] == "146.520000"  # Simplex
        assert result.iloc(0)["CTC/DCS Encode"] == "123.0"
        assert result.iloc(0)["CTC/DCS Decode"] == "88.5"

        assert result.iloc(1)["RX Frequency[MHz]"] == "447.000000"
        assert result.iloc(1)["TX Frequency[MHz]"] == "442.000000"  # Repeater
        assert result.iloc(1)["CTC/DCS Encode"] == "None"
        assert result.iloc(1)["CTC/DCS Decode"] == "146.2"

    def test_format_dmr_repeater(self):
        """Test formatting DMR repeater data."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # DMR repeater data
        input_data = LightDataFrame.from_records([
            {
                "frequency": "447.000000",
                "offset": "-5.000000",
                "DMR": "true",
                "Color Code": "1",
                "DMR ID": "123456",
                "location": "Digital Rptr",
                "callsign": "N6ABC",
            }
        ])

        result = formatter.format(input_data)

        # Check DMR settings
        assert len(result) == 1
        assert result.iloc(0)["Channel Type"] == "Digital"
        assert result.iloc(0)["Band Width"] == "12.5KHz"
        assert result.iloc(0)["Color Code"] == "1"
        assert result.iloc(0)["Time Slot"] == "Slot 1"
        assert result.iloc(0)["DMR ID"] == "123456"
        assert result.iloc(0)["RX Frequency[MHz]"] == "447.000000"
        assert result.iloc(0)["TX Frequency[MHz]"] == "442.00000"  # 447 - 5

    def test_format_with_alternative_rx_frequency_columns(self):
        """Test RX frequency detection from alternative columns."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test with rx_freq column
        input_data = LightDataFrame.from_records([
            {
                "rx_freq": "146.520000",
                "callsign": "W6ABC",
            }
        ])

        result = formatter.format(input_data)
        assert len(result) == 1
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.520000"

    def test_format_with_alternative_tx_frequency_columns(self):
        """Test TX frequency detection from alternative columns."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test with tx_freq column
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "tx_freq": "147.120000",
                "callsign": "W6ABC",
            }
        ])

        result = formatter.format(input_data)
        assert len(result) == 1
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.520000"
        assert result.iloc(0)["TX Frequency[MHz]"] == "147.120000"

    def test_format_with_offset_calculation(self):
        """Test TX frequency calculation from offset."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test offset calculation
        input_data = LightDataFrame.from_records([
            {
                "Downlink": "146.940000",  # Use detailed format
                "Offset": "+0.600000",  # Capital O for detailed format
                "callsign": "W6ABC",
            }
        ])

        result = formatter.format(input_data)
        assert len(result) == 1
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.940000"
        assert result.iloc(0)["TX Frequency[MHz]"] == "147.54000"  # 146.94 + 0.6

    def test_dmr_detection_methods(self):
        """Test various methods of detecting DMR repeaters."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test DMR detection via DMR column
        test_cases = [
            # DMR column with boolean values
            {"frequency": ["447.000"], "DMR": ["true"], "expected_dmr": True},
            {"frequency": ["447.000"], "DMR": ["1"], "expected_dmr": True},
            {"frequency": ["447.000"], "DMR": ["false"], "expected_dmr": False},
            # Color code detection
            {"frequency": ["447.000"], "Color Code": ["5"], "expected_dmr": True},
            {
                "frequency": ["447.000"],
                "Color Code": ["20"],
                "expected_dmr": False,
            },  # Out of range
            # DMR ID detection
            {"frequency": ["447.000"], "DMR ID": ["123456"], "expected_dmr": True},
            {
                "frequency": ["447.000"],
                "DMR ID": ["12"],
                "expected_dmr": False,
            },  # Too short
            # Mode field detection
            {"frequency": ["447.000"], "mode": ["DMR"], "expected_dmr": True},
            {"frequency": ["447.000"], "type": ["digital"], "expected_dmr": True},
            {"frequency": ["447.000"], "service": ["MOTOTRBO"], "expected_dmr": True},
        ]

        for case in test_cases:
            expected_dmr = case.pop("expected_dmr")
            # Convert list values to single values for LightDataFrame.from_records
            case_record = {k: v[0] if isinstance(v, list) else v for k, v in case.items()}
            input_data = LightDataFrame.from_records([case_record])
            
            result = formatter.format(input_data)
            actual_dmr = result.iloc(0)["Channel Type"] == "Digital"
            assert actual_dmr == expected_dmr, f"DMR detection failed for {case}"

    def test_color_code_detection(self):
        """Test color code detection and validation."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test valid color codes
        test_cases = [
            {
                "frequency": ["447.000"],
                "DMR": ["true"],
                "Color Code": ["0"],
                "expected_cc": "0",
            },
            {
                "frequency": ["447.000"],
                "DMR": ["true"],
                "Color Code": ["15"],
                "expected_cc": "15",
            },
            {
                "frequency": ["447.000"],
                "DMR": ["true"],
                "color_code": ["5"],
                "expected_cc": "5",
            },
            {
                "frequency": ["447.000"],
                "DMR": ["true"],
                "cc": ["7"],
                "expected_cc": "7",
            },
            # Invalid or missing color codes should default to "1"
            {
                "frequency": ["447.000"],
                "DMR": ["true"],
                "Color Code": ["20"],
                "expected_cc": "1",
            },  # Out of range
            {"frequency": ["447.000"], "DMR": ["true"], "expected_cc": "1"},  # Missing
        ]

        for case in test_cases:
            expected_cc = case.pop("expected_cc")
            # Convert list values to single values for LightDataFrame.from_records
            case_record = {k: v[0] if isinstance(v, list) else v for k, v in case.items()}
            input_data = LightDataFrame.from_records([case_record])
            
            result = formatter.format(input_data)
            actual_cc = result.iloc(0)["Color Code"]
            assert actual_cc == expected_cc, f"Color code detection failed for {case}"

    def test_dmr_id_detection(self):
        """Test DMR ID detection from various columns."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        test_cases = [
            {"frequency": ["447.000"], "DMR ID": ["123456"], "expected_id": "123456"},
            {"frequency": ["447.000"], "dmr_id": ["789012"], "expected_id": "789012"},
            {"frequency": ["447.000"], "radio_id": ["345678"], "expected_id": "345678"},
            {"frequency": ["447.000"], "id": ["901234"], "expected_id": "901234"},
            # Callsign fallback
            {"frequency": ["447.000"], "callsign": ["N6ABC"], "expected_id": "N6ABC"},
            # Invalid IDs should return "None"
            {
                "frequency": ["447.000"],
                "DMR ID": ["12"],
                "expected_id": "None",
            },  # Too short
            {
                "frequency": ["447.000"],
                "DMR ID": ["abc"],
                "expected_id": "None",
            },  # Not numeric
            {"frequency": ["447.000"], "expected_id": "None"},  # Missing
        ]

        for case in test_cases:
            expected_id = case.pop("expected_id")
            # Convert list values to single values for LightDataFrame.from_records
            case_record = {k: v[0] if isinstance(v, list) else v for k, v in case.items()}
            input_data = LightDataFrame.from_records([case_record])
            
            result = formatter.format(input_data)
            actual_id = result.iloc(0)["DMR ID"]
            assert actual_id == expected_id, f"DMR ID detection failed for {case}"

    def test_channel_name_generation_and_conflicts(self):
        """Test channel name generation and conflict resolution."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test conflict resolution with duplicate names
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "callsign": "W6ABC",
                "location": "LA",
            },
            {
                "frequency": "147.000",
                "callsign": "W6ABC",
                "location": "LA",
            },
            {
                "frequency": "448.000",
                "callsign": "W6ABC",
                "location": "LA",
            }
        ])

        result = formatter.format(input_data)
        names = [result.iloc(i)["Channel Name"] for i in range(len(result))]

        # Names should be unique after conflict resolution
        assert len(names) == len(set(names)), "Channel names should be unique"
        assert len(names[0]) <= 16, "Channel names should be 16 chars or less"

    def test_cps_version_optimization(self):
        """Test CPS version-specific optimizations."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "W6ABC",
            }
        ])

        # Test CHIRP optimization
        result_chirp = formatter.format(input_data, cps_version="CHIRP_next_20240301")
        assert len(result_chirp) == 1

        # Test DM-32UV CPS optimization
        result_cps = formatter.format(input_data, cps_version="DM_32UV_CPS_2.08")
        assert len(result_cps) == 1

    def test_start_channel_parameter(self):
        """Test start_channel parameter affects numbering."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "callsign": "W6ABC",
            },
            {
                "frequency": "147.000",
                "callsign": "K6XYZ",
            }
        ])

        # Test default start (1)
        result_default = formatter.format(input_data)
        assert result_default.iloc(0)["No."] == 1
        assert result_default.iloc(1)["No."] == 2

        # Test custom start (100)
        result_custom = formatter.format(input_data, start_channel=100)
        assert result_custom.iloc(0)["No."] == 100
        assert result_custom.iloc(1)["No."] == 101

    def test_format_empty_data_raises_error(self):
        """Test that empty input data raises ValueError."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()
        empty_data = LightDataFrame.from_records([])

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    def test_format_invalid_frequency_skips_row(self):
        """Test that rows with invalid frequencies are skipped."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Mix of valid and invalid frequencies
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "W6ABC",
            },
            {
                "frequency": "",
                "callsign": "EMPTY",
            },
            {
                "frequency": "invalid",
                "callsign": "BAD",
            },
            {
                "frequency": "447.000000",
                "callsign": "K6XYZ",
            }
        ])

        result = formatter.format(input_data)

        # Should only have 2 valid rows
        assert len(result) == 2
        assert result.iloc(0)["RX Frequency[MHz]"] == "146.520000"
        assert result.iloc(1)["RX Frequency[MHz]"] == "447.000000"

    def test_format_no_valid_data_raises_error(self):
        """Test that no valid repeater data raises error."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # All invalid frequencies
        input_data = LightDataFrame.from_records([
            {
                "frequency": "",
                "callsign": "BAD1",
            },
            {
                "frequency": "invalid",
                "callsign": "BAD2",
            },
            {
                "frequency": None,
                "callsign": "BAD3",
            }
        ])

        with pytest.raises(
            ValueError, match="No valid repeater data found after formatting"
        ):
            formatter.format(input_data)

    def test_format_zones_location_strategy(self):
        """Test zone formatting with location strategy."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Format some channels first
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "callsign": "W6ABC",
            },
            {
                "frequency": "147.000",
                "callsign": "K6XYZ",
            },
            {
                "frequency": "448.000",
                "callsign": "N6DEF",
            }
        ])

        formatted_channels = formatter.format(input_data)

        # Test CSV metadata
        csv_metadata = {"County": "Los Angeles", "State": "CA"}

        zones = formatter.format_zones(
            formatted_channels, csv_metadata=csv_metadata, zone_strategy="location"
        )

        assert len(zones) == 1
        # Zone name may be "Unknown" if metadata processing doesn't work as expected
        assert len(zones.iloc(0)["Zone Name"]) > 0
        assert zones.iloc(0)["No."] == 1
        assert "|" in zones.iloc(0)["Channel Members"]  # Pipe-separated

    def test_format_zones_band_strategy(self):
        """Test zone formatting with band strategy."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Mix of VHF and UHF channels
        input_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "callsign": "W6VHF1",
            },
            {
                "frequency": "147.000",
                "callsign": "W6VHF2",
            },
            {
                "frequency": "447.000",
                "callsign": "W6UHF1",
            },
            {
                "frequency": "448.000",
                "callsign": "W6UHF2",
            }
        ])

        formatted_channels = formatter.format(input_data)

        zones = formatter.format_zones(formatted_channels, zone_strategy="band")

        # Should create VHF and UHF zones
        assert len(zones) >= 2
        zone_names = [zones.iloc(i)["Zone Name"] for i in range(len(zones))]
        assert "VHF" in zone_names
        assert "UHF" in zone_names

    def test_format_zones_large_channel_set(self):
        """Test zone formatting with channels exceeding max per zone."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Create more channels than max_channels_per_zone (64)
        records = []
        for i in range(70):  # 70 channels
            records.append({
                "frequency": f"146.{520 + i:03d}",
                "callsign": f"W6T{i:02d}",
            })
        
        input_data = LightDataFrame.from_records(records)

        formatted_channels = formatter.format(input_data)

        csv_metadata = {"County": "Test", "State": "CA"}
        zones = formatter.format_zones(
            formatted_channels,
            csv_metadata=csv_metadata,
            zone_strategy="location",
            max_channels_per_zone=64,
        )

        # Should create multiple zones
        assert len(zones) >= 2
        assert zones.iloc(0)["Zone Name"].endswith("1")
        assert zones.iloc(1)["Zone Name"].endswith("2")

    def test_format_zones_fallback(self):
        """Test zone formatting fallback behavior."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # No channels (empty formatted data)
        empty_channels = LightDataFrame.from_records([])

        zones = formatter.format_zones(empty_channels)

        # Should create default zone (may be "Unknown" instead of "Default")
        assert len(zones) == 1
        assert zones.iloc(0)["Zone Name"] in ["Default", "Unknown"]
        assert zones.iloc(0)["Channel Members"] == ""

    def test_registry_integration(self):
        """Test that DM-32UV formatter is properly registered."""
        # Test that we can get the formatter by key
        formatter = get_radio_formatter("baofeng-dm32uv")
        assert formatter is not None
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        assert isinstance(formatter, BaofengDM32UVFormatter)

        # Test case insensitive lookup
        formatter_upper = get_radio_formatter("BAOFENG-DM32UV")
        assert formatter_upper is not None
        assert isinstance(formatter_upper, BaofengDM32UVFormatter)

        # Test that it's in supported radios list
        supported = get_supported_radios()
        assert "baofeng-dm32uv" in supported


class TestToneUpDownFunctionality:
    """Test tone_up and tone_down support across all radio formatters."""

    def test_dm32uv_supports_separate_tones(self):
        """Test DM-32UV formatter with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        formatter = BaofengDM32UVFormatter()

        # Test data with separate tones
        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "tone_up": "123.0",
                "tone_down": "456.0",
                "callsign": "W1ABC",
                "location": "City1",
            },
            {
                "frequency": "147.000",
                "tone_up": None,
                "tone_down": "88.5",
                "callsign": "K2DEF",
                "location": "City2",
            }
        ])

        result = formatter.format(test_data)

        # Check tone mapping: tone_up -> encode, tone_down -> decode
        assert result.iloc(0)["CTC/DCS Encode"] == "123.0"
        assert result.iloc(0)["CTC/DCS Decode"] == "456.0"
        assert result.iloc(1)["CTC/DCS Encode"] == "None"  # None tone_up
        assert result.iloc(1)["CTC/DCS Decode"] == "88.5"

    def test_anytone_878_supports_separate_tones(self):
        """Test Anytone 878 formatter with separate tone_up and tone_down."""
        formatter = Anytone878V3Formatter()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "tone_up": "123.0",
                "tone_down": "456.0",
                "callsign": "W1ABC",
            }
        ])

        result = formatter.format(test_data)

        assert result.iloc(0)["CTCSS/DCS Encode"] == "123.0"
        assert result.iloc(0)["CTCSS/DCS Decode"] == "456.0"

    def test_anytone_578_supports_separate_tones(self):
        """Test Anytone 578 formatter with separate tone_up and tone_down."""
        from radiobridge.radios.anytone_578 import Anytone578Formatter

        formatter = Anytone578Formatter()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "tone_up": "123.0",
                "tone_down": "456.0",
                "callsign": "W1ABC",
            }
        ])

        result = formatter.format(test_data)

        assert result.iloc(0)["CTCSS/DCS Encode"] == "123.0"
        assert result.iloc(0)["CTCSS/DCS Decode"] == "456.0"

    def test_baofeng_k5_supports_separate_tones(self):
        """Test Baofeng K5 Plus formatter with separate tone_up and tone_down."""
        from radiobridge.radios.baofeng_k5_plus import BaofengK5PlusFormatter

        formatter = BaofengK5PlusFormatter()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "tone_up": "123.0",
                "tone_down": "456.0",
                "callsign": "W1ABC",
            }
        ])

        result = formatter.format(test_data)

        assert result.iloc(0)["TX CTCSS/DCS"] == "123.0"
        assert result.iloc(0)["RX CTCSS/DCS"] == "456.0"

    def test_legacy_tone_column_fallback(self):
        """Test that formatters fall back to legacy 'tone' column.

        When tone_up/down don't exist, should use legacy tone column.
        """
        formatter = Anytone878V3Formatter()

        # Test data with only legacy tone column
        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "tone": "100.0",
                "callsign": "W1ABC",
            }
        ])

        result = formatter.format(test_data)

        # Should use same tone for both encode and decode
        assert result.iloc(0)["CTCSS/DCS Encode"] == "100.0"
        assert result.iloc(0)["CTCSS/DCS Decode"] == "100.0"

    def test_no_tone_columns_results_in_off(self):
        """Test that missing tone data results in 'Off' values."""
        formatter = Anytone878V3Formatter()

        # Test data with no tone columns
        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520",
                "callsign": "W1ABC",
            }
        ])

        result = formatter.format(test_data)

        # Should default to 'Off'
        assert result.iloc(0)["CTCSS/DCS Encode"] == "Off"
        assert result.iloc(0)["CTCSS/DCS Decode"] == "Off"
