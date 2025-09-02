"""Tests for Baofeng radio formatters (UV-5R, UV-5RM, UV-25, UV-28)."""

import pytest

from radiobridge.lightweight_data import LightDataFrame
from radiobridge.radios import get_radio_formatter
from radiobridge.radios.baofeng_uv5r import BaofengUV5RFormatter
from radiobridge.radios.baofeng_uv5rm import BaofengUV5RMFormatter
from radiobridge.radios.baofeng_uv25 import BaofengUV25Formatter
from radiobridge.radios.baofeng_uv28 import BaofengUV28Formatter


# Test data fixtures
@pytest.fixture
def sample_repeater_data():
    """Sample repeater data for testing."""
    return LightDataFrame.from_records([
        {
            "frequency": "146.520000",
            "offset": "+0.000000",
            "tone": "",
            "location": "Los Angeles",
            "callsign": "W6ABC",
        },
        {
            "frequency": "147.000000",
            "offset": "-0.600000",
            "tone": "123.0",
            "location": "San Francisco",
            "callsign": "K6XYZ",
        },
        {
            "frequency": "447.000000",
            "offset": "-5.000000",
            "tone": "146.2",
            "location": "San Diego",
            "callsign": "N6DEF",
        }
    ])


@pytest.fixture
def detailed_downloader_data():
    """Sample detailed downloader data format."""
    return LightDataFrame.from_records([
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
            "Location": "San Diego",
            "callsign": "N6DEF",
        }
    ])


@pytest.fixture
def tone_data():
    """Test data with separate tone_up and tone_down columns."""
    return LightDataFrame.from_records([
        {
            "frequency": "146.520000",
            "tone_up": "123.0",
            "tone_down": "88.5",
            "callsign": "W1ABC",
            "location": "City1",
        },
        {
            "frequency": "447.000000",
            "tone_up": "",
            "tone_down": "146.2",
            "callsign": "K2DEF",
            "location": "City2",
        },
        {
            "frequency": "144.390000",
            "tone_up": "67.0",
            "tone_down": "67.0",
            "callsign": "N3GHI",
            "location": "City3",
        }
    ])


@pytest.fixture
def dcs_tone_data():
    """Test data with DCS tones."""
    return LightDataFrame.from_records([
        {
            "frequency": "146.520000",
            "tone": "D023",
            "callsign": "W1DCS",
            "location": "DCS1",
        },
        {
            "frequency": "447.000000",
            "tone": "D047",
            "callsign": "K2DCS",
            "location": "DCS2",
        }
    ])


@pytest.fixture
def invalid_data():
    """Test data with invalid frequencies."""
    return LightDataFrame.from_records([
        {
            "frequency": "",
            "callsign": "BAD1",
            "location": "Test1",
        },
        {
            "frequency": "invalid",
            "callsign": "BAD2",
            "location": "Test2",
        },
        {
            "frequency": "146.520000",
            "callsign": "GOOD",
            "location": "Test3",
        },
        {
            "frequency": None,
            "callsign": "BAD3",
            "location": "Test4",
        }
    ])


@pytest.fixture
def empty_data():
    """Empty DataFrame for testing."""
    return LightDataFrame.from_records([])


# Formatter test parameters
FORMATTER_TEST_PARAMS = [
    (BaofengUV5RFormatter, "baofeng-uv5r", "UV-5R", 18, 8),  # 18 columns, 8 char names
    (BaofengUV5RMFormatter, "baofeng-uv5rm", "UV-5RM", 18, 8),
    (BaofengUV25Formatter, "baofeng-uv25", "UV-25", 18, 10),  # 10 char names
    (
        BaofengUV28Formatter,
        "baofeng-uv28",
        "UV-28",
        19,
        12,
    ),  # 19 columns (has Power), 12 char names
]


class TestBaofengFormatterProperties:
    """Test basic properties and metadata for all Baofeng formatters."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_formatter_properties(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test formatter properties are correctly set."""
        formatter = formatter_class()

        # Test basic properties
        assert formatter.manufacturer == "Baofeng"
        assert model in formatter.model
        assert model in formatter.radio_name
        assert (
            "dual-band" in formatter.description.lower()
            or "VHF" in formatter.description
            or "enhanced" in formatter.description.lower()
        )
        assert formatter.required_columns == []  # All accept flexible input
        assert len(formatter.output_columns) == expected_columns

        # Test required columns are present
        assert "Location" in formatter.output_columns
        assert "Name" in formatter.output_columns
        assert "Frequency" in formatter.output_columns
        assert "Mode" in formatter.output_columns

        # UV-28 should have Power column, others should not
        if model == "UV-28":
            assert "Power" in formatter.output_columns
        else:
            assert "Power" not in formatter.output_columns

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_metadata_properties(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test formatter metadata is correctly set."""
        formatter = formatter_class()

        metadata_list = formatter.metadata
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        assert metadata.manufacturer == "Baofeng"
        assert metadata.model == model
        assert metadata.radio_version == "Standard"
        assert len(metadata.firmware_versions) > 0
        assert len(metadata.cps_versions) >= 3
        assert "CHIRP" in str(metadata.cps_versions)
        assert metadata.formatter_key == registry_key

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_registry_integration(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test that formatter is properly registered."""
        formatter = get_radio_formatter(registry_key)
        assert formatter is not None
        assert isinstance(formatter, formatter_class)

        # Test case insensitive lookup
        formatter_upper = get_radio_formatter(registry_key.upper())
        assert formatter_upper is not None
        assert isinstance(formatter_upper, formatter_class)


class TestBaofengFormatterBasicFormatting:
    """Test basic formatting functionality for all Baofeng formatters."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_basic_data(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test formatting basic repeater data."""
        formatter = formatter_class()
        result = formatter.format(sample_repeater_data)

        # Check basic structure
        assert len(result) == 3  # All 3 input rows should be valid
        assert len(result.columns) == expected_columns
        assert "Location" in result.columns
        assert "Name" in result.columns
        assert "Frequency" in result.columns

        # Check channel numbering
        assert result.iloc(0)["Location"] == 1
        assert result.iloc(1)["Location"] == 2
        assert result.iloc(2)["Location"] == 3

        # Check frequencies
        assert result.iloc(0)["Frequency"] == "146.520000"
        assert result.iloc(1)["Frequency"] == "147.000000"
        assert result.iloc(2)["Frequency"] == "447.000000"

        # Check duplex settings
        assert result.iloc(0)["Duplex"] == ""  # Simplex
        assert result.iloc(1)["Duplex"] == "-"  # Negative offset
        assert result.iloc(2)["Duplex"] == "-"  # Negative offset

        # Check offsets
        assert result.iloc(0)["Offset"] == "0.000000"
        assert result.iloc(1)["Offset"] == "0.600000"
        assert result.iloc(2)["Offset"] == "5.000000"

        # Check mode is always FM for these radios
        modes = [result.iloc(i)["Mode"] for i in range(len(result))]
        assert all(mode == "FM" for mode in modes)

        # Check channel names are within limits
        names = [result.iloc(i)["Name"] for i in range(len(result))]
        for name in names:
            assert len(name) <= max_name_len

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_detailed_downloader_data(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        detailed_downloader_data,
    ):
        """Test formatting detailed downloader data with Downlink/Uplink."""
        formatter = formatter_class()
        result = formatter.format(detailed_downloader_data)

        # Check structure
        assert len(result) == 2
        assert result.iloc(0)["Frequency"] == "146.520000"  # Downlink becomes RX
        assert result.iloc(1)["Frequency"] == "447.000000"

        # Check duplex calculation from Downlink/Uplink
        assert result.iloc(0)["Duplex"] == ""  # Simplex (same frequencies)
        assert result.iloc(1)["Duplex"] == "-"  # Repeater (447 -> 442)

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_with_start_channel(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test start_channel parameter affects numbering."""
        formatter = formatter_class()

        # Test custom start channel
        result = formatter.format(sample_repeater_data, start_channel=100)
        assert result.iloc(0)["Location"] == 100
        assert result.iloc(1)["Location"] == 101
        assert result.iloc(2)["Location"] == 102

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_with_cps_version(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test CPS version-specific optimizations."""
        formatter = formatter_class()

        # Test CHIRP optimization
        result_chirp = formatter.format(
            sample_repeater_data, cps_version="CHIRP_next_20240301"
        )
        assert len(result_chirp) == 3

        # Test RT Systems optimization
        result_rt = formatter.format(
            sample_repeater_data, cps_version="RT_Systems_Test_1.0"
        )
        assert len(result_rt) == 3


class TestBaofengFormatterToneHandling:
    """Test tone handling for all Baofeng formatters."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_tone_up_tone_down_support(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        tone_data,
    ):
        """Test separate tone_up and tone_down columns."""
        formatter = formatter_class()
        result = formatter.format(tone_data)

        # Check tone mapping
        assert result.iloc(0)["Tone"] == "Tone"  # Has tones
        assert result.iloc(0)["rToneFreq"] == "88.5"  # tone_down
        assert result.iloc(0)["cToneFreq"] == "123.0"  # tone_up

        assert result.iloc(1)["Tone"] == "Tone"  # Has tone_down only
        assert result.iloc(1)["rToneFreq"] == "146.2"
        assert result.iloc(1)["cToneFreq"] == "146.2"  # Should copy tone_down

        assert result.iloc(2)["Tone"] == "Tone"  # Same tone for both
        assert result.iloc(2)["rToneFreq"] == "67.0"
        assert result.iloc(2)["cToneFreq"] == "67.0"

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_dcs_tone_support(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        dcs_tone_data,
    ):
        """Test DCS tone support."""
        formatter = formatter_class()
        result = formatter.format(dcs_tone_data)

        # Check DCS tone handling
        assert result.iloc(0)["Tone"] == "DTCS"
        assert result.iloc(0)["DtcsCode"] == "023"
        assert result.iloc(0)["DtcsPolarity"] == "NN"

        assert result.iloc(1)["Tone"] == "DTCS"
        assert result.iloc(1)["DtcsCode"] == "047"

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_no_tone_defaults(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test default values when no tone data is provided."""
        formatter = formatter_class()

        # Data with no tone columns
        no_tone_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "W1ABC",
                "location": "Test",
            }
        ])

        result = formatter.format(no_tone_data)

        assert result.iloc(0)["Tone"] == "None"
        assert result.iloc(0)["rToneFreq"] == "88.5"
        assert result.iloc(0)["cToneFreq"] == "88.5"
        assert result.iloc(0)["DtcsCode"] == "023"
        assert result.iloc(0)["DtcsPolarity"] == "NN"


class TestBaofengFormatterFrequencyHandling:
    """Test frequency and band-specific handling."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_vhf_uhf_frequency_steps(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test frequency step settings for VHF/UHF bands."""
        formatter = formatter_class()

        # Test VHF and UHF frequencies
        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "VHF",
            },
            {
                "frequency": "447.000000",
                "callsign": "UHF",
            },
            {
                "frequency": "220.000000",
                "callsign": "OTHER",
            }
        ])

        result = formatter.format(test_data)

        # Check frequency steps
        assert result.iloc(0)["TStep"] == "5.00"  # VHF
        assert result.iloc(1)["TStep"] == "12.50"  # UHF
        assert result.iloc(2)["TStep"] == "5.00"  # Default to 5.00 for other bands

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_offset_calculation_edge_cases(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test edge cases in offset calculation."""
        formatter = formatter_class()

        # Test various offset scenarios
        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "offset": "0.000000",
                "callsign": "ZERO",
            },
            {
                "frequency": "146.520000",
                "offset": "+0.000001",
                "callsign": "TINY_POS",
            },
            {
                "frequency": "146.520000",
                "offset": "-0.000001",
                "callsign": "TINY_NEG",
            }
        ])

        result = formatter.format(test_data)

        # Check that tiny offsets are treated as simplex
        assert result.iloc(0)["Duplex"] == ""
        assert result.iloc(0)["Offset"] == "0.000000"
        # Tiny offsets should still be recognized
        assert result.iloc(1)["Duplex"] == ""  # Less than 0.001 threshold
        assert result.iloc(2)["Duplex"] == ""  # Less than 0.001 threshold


class TestBaofengFormatterChannelNaming:
    """Test channel name generation and conflict resolution."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_channel_name_generation(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test channel name generation from callsign and location."""
        formatter = formatter_class()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "W6VERYLONGCALLSIGN",
                "location": "Very Long Location Name That Exceeds Limits",
            }
        ])

        result = formatter.format(test_data)
        channel_name = result.iloc(0)["Name"]

        # Channel name should be within length limits
        assert len(channel_name) <= max_name_len
        # Should contain some part of the callsign or location
        assert len(channel_name) > 0

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_channel_name_conflicts(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test channel name conflict resolution."""
        formatter = formatter_class()

        # Create data that would generate duplicate names
        test_data = LightDataFrame.from_records([
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

        result = formatter.format(test_data)
        names = [result.iloc(i)["Name"] for i in range(len(result))]

        # Names should be unique after conflict resolution
        assert len(names) == len(set(names))

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_fallback_channel_names(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test fallback channel names when no callsign/location data."""
        formatter = formatter_class()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
            },
            {
                "frequency": "147.000000",
            }
        ])

        result = formatter.format(test_data)

        # Should generate fallback names
        assert "CH" in result.iloc(0)["Name"]
        assert "CH" in result.iloc(1)["Name"]
        assert result.iloc(0)["Name"] != result.iloc(1)["Name"]  # Should be unique


class TestBaofengFormatterErrorHandling:
    """Test error handling and validation."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_empty_data_raises_error(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        empty_data,
    ):
        """Test that empty input data raises ValueError."""
        formatter = formatter_class()

        with pytest.raises(ValueError, match="Input data is empty"):
            formatter.format(empty_data)

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_invalid_frequencies_skipped(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        invalid_data,
    ):
        """Test that rows with invalid frequencies are skipped."""
        formatter = formatter_class()

        result = formatter.format(invalid_data)

        # Should only have 1 valid row (the one with "146.520000")
        assert len(result) == 1
        assert result.iloc(0)["Frequency"] == "146.520000"

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_format_no_valid_data_raises_error(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test that no valid repeater data raises error."""
        formatter = formatter_class()

        # All invalid frequencies
        all_invalid_data = LightDataFrame.from_records([
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
            formatter.format(all_invalid_data)

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_invalid_offset_handling(
        self, formatter_class, registry_key, model, expected_columns, max_name_len
    ):
        """Test handling of invalid offset values."""
        formatter = formatter_class()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "offset": "invalid",
                "callsign": "TEST1",
            },
            {
                "frequency": "147.000000",
                "offset": None,
                "callsign": "TEST2",
            }
        ])

        result = formatter.format(test_data)

        # Should default to simplex for invalid offsets
        assert result.iloc(0)["Duplex"] == ""
        assert result.iloc(0)["Offset"] == "0.000000"
        assert result.iloc(1)["Duplex"] == ""
        assert result.iloc(1)["Offset"] == "0.000000"


class TestUV28SpecificFeatures:
    """Test UV-28 specific features (mobile radio differences)."""

    def test_uv28_power_column(self, sample_repeater_data):
        """Test that UV-28 includes Power column."""
        formatter = BaofengUV28Formatter()
        result = formatter.format(sample_repeater_data)

        # UV-28 should have Power column
        assert "Power" in result.columns
        power_values = [result.iloc(i)["Power"] for i in range(len(result))]
        assert all(power == "High" for power in power_values)  # Default to High

    def test_uv28_longer_channel_names(self):
        """Test that UV-28 supports longer channel names."""
        formatter = BaofengUV28Formatter()

        test_data = LightDataFrame.from_records([
            {
                "frequency": "146.520000",
                "callsign": "W6VERYLONGCALL",
                "location": "LongLocationName",
            }
        ])

        result = formatter.format(test_data)

        # UV-28 should allow up to 12 character names
        channel_name = result.iloc(0)["Name"]
        assert len(channel_name) <= 12
        # Should be able to fit more characters than handheld radios
        assert len(channel_name) >= 8  # Should use more space available


class TestBaofengFormatterOutputValidation:
    """Test output format validation."""

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_output_column_order(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test that output columns are in the expected order."""
        formatter = formatter_class()
        result = formatter.format(sample_repeater_data)

        expected_columns_list = formatter.output_columns
        actual_columns = list(result.columns)

        assert actual_columns == expected_columns_list

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_output_data_types(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test output data types are appropriate."""
        formatter = formatter_class()
        result = formatter.format(sample_repeater_data)

        # Location should be numeric (channel numbers)
        location_values = [result.iloc(i)["Location"] for i in range(len(result))]
        assert all(
            isinstance(x, int) for x in location_values
        )

        # Other fields should be strings
        string_columns = ["Name", "Frequency", "Duplex", "Offset", "Mode", "TStep"]
        for col in string_columns:
            if col in result.columns:
                col_values = [result.iloc(i)[col] for i in range(len(result))]
                assert all(isinstance(x, str) for x in col_values)

    @pytest.mark.parametrize(
        "formatter_class,registry_key,model,expected_columns,max_name_len",
        FORMATTER_TEST_PARAMS,
    )
    def test_required_fields_not_empty(
        self,
        formatter_class,
        registry_key,
        model,
        expected_columns,
        max_name_len,
        sample_repeater_data,
    ):
        """Test that required fields are not empty."""
        formatter = formatter_class()
        result = formatter.format(sample_repeater_data)

        # These fields should never be empty
        required_fields = ["Location", "Name", "Frequency", "Mode"]
        for field in required_fields:
            field_values = [result.iloc(i)[field] for i in range(len(result))]
            if field == "Location":
                # Location is numeric, check not zero/empty
                assert all(x is not None and x != 0 for x in field_values)
            else:
                # String fields should not be empty
                assert all(x != "" for x in field_values)
                assert all(x is not None and str(x) != "nan" for x in field_values)
