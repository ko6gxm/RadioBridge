"""Test suite for CPS version functionality.

This module tests:
- CPS version display formatting
- CPS version validation (ranges and exact matches)
- RadioMetadata CPS handling
- Edge cases and error conditions
"""

import pytest

from radiobridge.radios.metadata import RadioMetadata
from radiobridge.radios.base import BaseRadioFormatter


class MockRadioFormatter(BaseRadioFormatter):
    """Mock radio formatter for testing CPS validation."""

    def __init__(self, test_metadata=None):
        # Skip the parent __init__ to avoid logger setup
        self.test_metadata = test_metadata or []

    @property
    def radio_name(self):
        return "Test Radio"

    @property
    def description(self):
        return "Test radio for CPS validation"

    @property
    def required_columns(self):
        return []

    @property
    def output_columns(self):
        return []

    @property
    def metadata(self):
        return self.test_metadata

    def format(self, data, start_channel=1, cps_version=None):
        pass


class TestRadioMetadataCPSDisplay:
    """Test CPS display formatting in RadioMetadata."""

    def test_single_cps_version_range(self):
        """Test formatting of single CPS version range."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["Anytone_CPS_3.00_3.08"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "Anytone-CPS 3.00-3.08"

    def test_single_cps_version_no_range(self):
        """Test formatting of single CPS version without range."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["Anytone_CPS_4.00"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "Anytone-CPS 4.00"

    def test_multi_word_manufacturer_cps(self):
        """Test formatting with multi-word manufacturer names."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["DM_32UV_CPS_2.08_2.12"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "DM 32UV-CPS 2.08-2.12"

    def test_chirp_next_version_range(self):
        """Test formatting of CHIRP-next version ranges."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["CHIRP_next_20240801_20250401"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "CHIRP-next 20240801+"

    def test_multiple_cps_versions_mixed(self):
        """Test formatting of multiple mixed CPS versions."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=[
                "Anytone_CPS_3.00_3.08",
                "Anytone_CPS_4.00",
                "CHIRP_next_20240801_20250401",
            ],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "Anytone-CPS 3.00-3.08, Anytone-CPS 4.00, CHIRP-next 20240801+"

    def test_complex_version_numbers(self):
        """Test formatting with complex version numbers."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["OpenGD77_CPS_4.2.5_4.3.0"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "OpenGD77-CPS 4.2.5-4.3.0"

    def test_empty_cps_versions(self):
        """Test formatting with empty CPS versions list."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=[],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "Unknown"

    def test_non_cps_version_strings(self):
        """Test formatting with non-standard CPS version strings."""
        metadata = RadioMetadata(
            manufacturer="Test",
            model="TestModel",
            radio_version="v1",
            firmware_versions=["1.0"],
            cps_versions=["Simple_Name", "Multiple_Under_Scores_Here"],
            formatter_key="test",
        )

        result = metadata._format_cps_display()
        assert result == "Simple Name, Multiple Under Scores Here"


class TestCPSVersionValidation:
    """Test CPS version validation logic."""

    def test_exact_match_validation(self):
        """Test exact match CPS validation."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=["Anytone_CPS_4.00"],
                formatter_key="anytone-878",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Exact match should pass
        assert formatter.validate_cps_version("Anytone CPS 4.00") is True
        assert formatter.validate_cps_version("Anytone_CPS_4.00") is True

        # Non-match should fail
        assert formatter.validate_cps_version("Anytone CPS 4.01") is False

    def test_range_validation_within_range(self):
        """Test range validation for versions within range."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=["Anytone_CPS_3.00_3.08"],
                formatter_key="anytone-878",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Versions within range should pass
        assert formatter.validate_cps_version("Anytone CPS 3.00") is True
        assert formatter.validate_cps_version("Anytone CPS 3.05") is True
        assert formatter.validate_cps_version("Anytone CPS 3.08") is True

        # Versions outside range should fail
        assert formatter.validate_cps_version("Anytone CPS 2.99") is False
        assert formatter.validate_cps_version("Anytone CPS 3.09") is False

    def test_range_validation_complex_versions(self):
        """Test range validation with complex version numbers."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Baofeng",
                model="K5",
                radio_version="v2",
                firmware_versions=["v2.0.1.26"],
                cps_versions=["K5_CPS_2.0.6_2.1.8"],
                formatter_key="baofeng-k5",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Complex versions within range
        assert formatter.validate_cps_version("K5 CPS 2.0.6") is True
        assert formatter.validate_cps_version("K5 CPS 2.1.0") is True
        assert formatter.validate_cps_version("K5 CPS 2.1.8") is True

        # Outside range
        assert formatter.validate_cps_version("K5 CPS 2.0.5") is False
        assert formatter.validate_cps_version("K5 CPS 2.1.9") is False

    def test_multi_word_manufacturer_validation(self):
        """Test validation with multi-word manufacturer names."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Baofeng",
                model="DM-32UV",
                radio_version="v2",
                firmware_versions=["2.14"],
                cps_versions=["DM_32UV_CPS_2.08_2.12"],
                formatter_key="baofeng-dm32uv",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Should handle multi-word manufacturers correctly
        assert formatter.validate_cps_version("DM 32UV CPS 2.10") is True
        assert formatter.validate_cps_version("DM 32UV CPS 2.08") is True
        assert formatter.validate_cps_version("DM 32UV CPS 2.12") is True

        # Outside range should fail
        assert formatter.validate_cps_version("DM 32UV CPS 2.07") is False
        assert formatter.validate_cps_version("DM 32UV CPS 2.13") is False

    def test_chirp_date_validation(self):
        """Test CHIRP date range validation."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=["CHIRP_next_20240801_20250401"],
                formatter_key="anytone-878",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Dates within range should pass
        assert formatter.validate_cps_version("CHIRP next 20240801") is True
        assert formatter.validate_cps_version("CHIRP next 20241201") is True
        assert formatter.validate_cps_version("CHIRP next 20250401") is True

        # Dates outside range should fail
        assert formatter.validate_cps_version("CHIRP next 20240701") is False
        assert formatter.validate_cps_version("CHIRP next 20250501") is False

    def test_chirp_exact_range_match(self):
        """Test exact CHIRP range matching with dash format."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=["CHIRP_next_20240801_20250401"],
                formatter_key="anytone-878",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Exact range match should pass
        assert formatter.validate_cps_version("CHIRP next 20240801-20250401") is True

    def test_multiple_cps_versions_validation(self):
        """Test validation against multiple CPS versions."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=[
                    "Anytone_CPS_3.00_3.08",
                    "Anytone_CPS_4.00",
                    "CHIRP_next_20240801_20250401",
                ],
                formatter_key="anytone-878",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Should match any of the available versions
        assert formatter.validate_cps_version("Anytone CPS 3.05") is True  # Range match
        assert formatter.validate_cps_version("Anytone CPS 4.00") is True  # Exact match
        assert (
            formatter.validate_cps_version("CHIRP next 20241201") is True
        )  # CHIRP match

        # Should fail if no match
        assert formatter.validate_cps_version("Anytone CPS 2.50") is False

    def test_empty_cps_version_input(self):
        """Test validation with empty or None input."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Test",
                model="Test",
                radio_version="v1",
                firmware_versions=["1.0"],
                cps_versions=["Test_CPS_1.0"],
                formatter_key="test",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Empty/None input should be valid (default behavior)
        assert formatter.validate_cps_version("") is True
        assert formatter.validate_cps_version(None) is True

    def test_case_insensitive_validation(self):
        """Test case-insensitive CPS validation."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Test",
                model="Test",
                radio_version="v1",
                firmware_versions=["1.0"],
                cps_versions=["CHIRP_next_20240801_20250401"],
                formatter_key="test",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Case variations should work
        assert formatter.validate_cps_version("chirp next 20241201") is True
        assert formatter.validate_cps_version("CHIRP NEXT 20241201") is True
        assert formatter.validate_cps_version("Chirp Next 20241201") is True


class TestCPSVersionRangeMatching:
    """Test the internal range matching logic."""

    def test_version_matches_range_basic(self):
        """Test basic version range matching."""
        formatter = MockRadioFormatter()

        # Basic range matching
        assert (
            formatter._version_matches_range(
                "Anytone_CPS_3.05", "Anytone_CPS_3.00_3.08"
            )
            is True
        )

        assert (
            formatter._version_matches_range(
                "Anytone_CPS_2.99", "Anytone_CPS_3.00_3.08"
            )
            is False
        )

        assert (
            formatter._version_matches_range(
                "Anytone_CPS_3.09", "Anytone_CPS_3.00_3.08"
            )
            is False
        )

    def test_version_matches_range_edge_cases(self):
        """Test edge cases in version range matching."""
        formatter = MockRadioFormatter()

        # Boundary conditions
        assert (
            formatter._version_matches_range("Test_CPS_3.00", "Test_CPS_3.00_3.08")
            is True
        )

        assert (
            formatter._version_matches_range("Test_CPS_3.08", "Test_CPS_3.00_3.08")
            is True
        )

        # Different base names should not match
        assert (
            formatter._version_matches_range(
                "Anytone_CPS_3.05", "Baofeng_CPS_3.00_3.08"
            )
            is False
        )

    def test_version_matches_range_invalid_input(self):
        """Test range matching with invalid input."""
        formatter = MockRadioFormatter()

        # Invalid formats should not match
        assert (
            formatter._version_matches_range("Invalid_Format", "Anytone_CPS_3.00_3.08")
            is False
        )

        assert (
            formatter._version_matches_range("Anytone_CPS_3.05", "Invalid_Range_Format")
            is False
        )

        # Non-numeric versions
        assert (
            formatter._version_matches_range("Test_CPS_abc", "Test_CPS_3.00_3.08")
            is False
        )

    def test_date_in_chirp_range(self):
        """Test CHIRP date range validation."""
        formatter = MockRadioFormatter()

        # Valid dates within range
        assert (
            formatter._date_in_chirp_range("20240801", "CHIRP_next_20240801_20250401")
            is True
        )

        assert (
            formatter._date_in_chirp_range("20241201", "CHIRP_next_20240801_20250401")
            is True
        )

        assert (
            formatter._date_in_chirp_range("20250401", "CHIRP_next_20240801_20250401")
            is True
        )

        # Invalid dates outside range
        assert (
            formatter._date_in_chirp_range("20240701", "CHIRP_next_20240801_20250401")
            is False
        )

        assert (
            formatter._date_in_chirp_range("20250501", "CHIRP_next_20240801_20250401")
            is False
        )

    def test_date_in_chirp_range_invalid_input(self):
        """Test CHIRP date validation with invalid input."""
        formatter = MockRadioFormatter()

        # Invalid date formats
        assert (
            formatter._date_in_chirp_range("2024-08-01", "CHIRP_next_20240801_20250401")
            is False
        )

        assert (
            formatter._date_in_chirp_range("202408", "CHIRP_next_20240801_20250401")
            is False
        )

        # Invalid range format
        assert formatter._date_in_chirp_range("20241201", "Invalid_Range") is False


class TestCPSVersionEdgeCases:
    """Test edge cases and error conditions."""

    def test_get_supported_cps_versions(self):
        """Test getting all supported CPS versions."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Test1",
                model="Model1",
                radio_version="v1",
                firmware_versions=["1.0"],
                cps_versions=["Test1_CPS_1.0", "CHIRP_next_20240801_20250401"],
                formatter_key="test1",
            ),
            RadioMetadata(
                manufacturer="Test2",
                model="Model2",
                radio_version="v1",
                firmware_versions=["1.0"],
                cps_versions=["Test2_CPS_2.0_2.5"],
                formatter_key="test2",
            ),
        ]

        formatter = MockRadioFormatter(test_metadata)

        supported = formatter.get_supported_cps_versions()
        expected = [
            "CHIRP_next_20240801_20250401",
            "Test1_CPS_1.0",
            "Test2_CPS_2.0_2.5",
        ]

        assert sorted(supported) == sorted(expected)

    def test_no_metadata(self):
        """Test formatter with no metadata."""
        formatter = MockRadioFormatter([])

        # Should handle empty metadata gracefully
        assert formatter.get_supported_cps_versions() == []
        assert formatter.validate_cps_version("Any CPS Version") is False
        assert formatter.validate_cps_version("") is True  # Empty is always valid

    def test_malformed_cps_versions(self):
        """Test handling of malformed CPS versions."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Test",
                model="Test",
                radio_version="v1",
                firmware_versions=["1.0"],
                cps_versions=["", "Invalid_Format", "No_Underscores"],
                formatter_key="test",
            )
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Should handle malformed versions without crashing
        assert formatter.validate_cps_version("Test Input") is False

        # Should include malformed versions in supported list
        supported = formatter.get_supported_cps_versions()
        assert "Invalid_Format" in supported
        assert "No_Underscores" in supported


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_anytone_878_realistic_scenario(self):
        """Test realistic Anytone 878 CPS validation scenario."""
        # Simulate actual Anytone 878 metadata
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II Plus",
                radio_version="Plus",
                firmware_versions=["1.24", "1.23"],
                cps_versions=[
                    "Anytone_CPS_3.00_3.08",
                    "Anytone_CPS_4.00",
                    "CHIRP_next_20240801_20250401",
                ],
                formatter_key="anytone-878",
            ),
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II",
                radio_version="Standard",
                firmware_versions=["1.20", "1.19"],
                cps_versions=[
                    "Anytone_CPS_2.50_2.58",
                    "Anytone_CPS_3.00_3.05",
                    "CHIRP_next_20240301_20240801",
                ],
                formatter_key="anytone-878",
            ),
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Test various user inputs
        valid_inputs = [
            "Anytone CPS 3.05",  # Within Plus range
            "Anytone CPS 4.00",  # Exact Plus match
            "Anytone CPS 2.55",  # Within Standard range
            "CHIRP next 20241201",  # Within Plus CHIRP range
            "CHIRP next 20240501",  # Within Standard CHIRP range
        ]

        for cps_input in valid_inputs:
            assert (
                formatter.validate_cps_version(cps_input) is True
            ), f"Expected {cps_input} to be valid"

        invalid_inputs = [
            "Anytone CPS 1.50",  # Below all ranges
            "Anytone CPS 5.00",  # Above all ranges
            "Baofeng CPS 3.05",  # Wrong manufacturer
            "CHIRP next 20240101",  # Before all CHIRP ranges
        ]

        for cps_input in invalid_inputs:
            assert (
                formatter.validate_cps_version(cps_input) is False
            ), f"Expected {cps_input} to be invalid"

    def test_mixed_manufacturer_scenario(self):
        """Test scenario with multiple manufacturers."""
        test_metadata = [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV",
                radio_version="Plus",
                firmware_versions=["1.24"],
                cps_versions=["Anytone_CPS_3.00_3.08"],
                formatter_key="anytone-878",
            ),
            RadioMetadata(
                manufacturer="Baofeng",
                model="DM-32UV",
                radio_version="v2",
                firmware_versions=["2.14"],
                cps_versions=["DM_32UV_CPS_2.08_2.12"],
                formatter_key="baofeng-dm32uv",
            ),
            RadioMetadata(
                manufacturer="Baofeng",
                model="K5",
                radio_version="v2",
                firmware_versions=["v2.0.1.26"],
                cps_versions=["K5_CPS_2.0.6_2.1.8"],
                formatter_key="baofeng-k5",
            ),
        ]

        formatter = MockRadioFormatter(test_metadata)

        # Each manufacturer should validate independently
        assert formatter.validate_cps_version("Anytone CPS 3.05") is True
        assert formatter.validate_cps_version("DM 32UV CPS 2.10") is True
        assert formatter.validate_cps_version("K5 CPS 2.1.0") is True

        # Cross-manufacturer validation should fail
        assert (
            formatter.validate_cps_version("Anytone CPS 2.10") is False
        )  # Wrong range
        assert (
            formatter.validate_cps_version("K5 CPS 3.05") is False
        )  # Wrong manufacturer


if __name__ == "__main__":
    pytest.main([__file__])
