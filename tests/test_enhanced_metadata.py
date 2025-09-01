"""Tests for enhanced radio metadata functionality."""

import pytest
from datetime import date
from unittest import TestCase

from src.radiobridge.radios.enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel,
    determine_band_count,
    determine_form_factor_from_model,
)
from src.radiobridge.radios.metadata import RadioMetadata


class TestEnhancedRadioMetadata(TestCase):
    """Test enhanced radio metadata functionality."""

    def setUp(self):
        """Set up test data."""
        self.frequency_ranges = [
            FrequencyRange("VHF", 136.0, 174.0, 12.5),
            FrequencyRange("UHF", 400.0, 520.0, 12.5),
        ]

        self.power_levels = [
            PowerLevel("Low", 1.0, ["VHF", "UHF"]),
            PowerLevel("High", 5.0, ["VHF"]),
            PowerLevel("High", 4.0, ["UHF"]),
        ]

        self.enhanced_metadata = EnhancedRadioMetadata(
            manufacturer="Anytone",
            model="AT-D878UV II Plus",
            radio_version="Plus",
            firmware_versions=["1.24", "1.23"],
            cps_versions=["Anytone_CPS_3.00_3.08"],
            formatter_key="anytone-878",
            form_factor=FormFactor.HANDHELD,
            band_count=BandCount.DUAL_BAND,
            max_power_watts=5.0,
            frequency_ranges=self.frequency_ranges,
            power_levels=self.power_levels,
            modulation_modes=["FM", "DMR"],
            digital_modes=["DMR"],
            memory_channels=4000,
            gps_enabled=True,
        )

    def test_enhanced_metadata_creation(self):
        """Test creating enhanced metadata."""
        self.assertEqual(self.enhanced_metadata.manufacturer, "Anytone")
        self.assertEqual(self.enhanced_metadata.form_factor, FormFactor.HANDHELD)
        self.assertEqual(self.enhanced_metadata.band_count, BandCount.DUAL_BAND)
        self.assertEqual(self.enhanced_metadata.max_power_watts, 5.0)

    def test_legacy_conversion(self):
        """Test conversion to/from legacy metadata."""
        # Convert to legacy
        legacy = self.enhanced_metadata.to_legacy_metadata()
        self.assertIsInstance(legacy, RadioMetadata)
        self.assertEqual(legacy.manufacturer, "Anytone")
        self.assertEqual(legacy.model, "AT-D878UV II Plus")

        # Convert from legacy
        enhanced = EnhancedRadioMetadata.from_legacy_metadata(
            legacy,
            form_factor=FormFactor.HANDHELD,
            band_count=BandCount.DUAL_BAND,
            max_power_watts=5.0,
        )
        self.assertEqual(enhanced.manufacturer, "Anytone")
        self.assertEqual(enhanced.form_factor, FormFactor.HANDHELD)

    def test_frequency_support(self):
        """Test frequency support checking."""
        # VHF frequency
        self.assertTrue(self.enhanced_metadata.supports_frequency(146.520))

        # UHF frequency
        self.assertTrue(self.enhanced_metadata.supports_frequency(440.000))

        # Unsupported frequency
        self.assertFalse(self.enhanced_metadata.supports_frequency(300.000))

    def test_band_support(self):
        """Test band support checking."""
        self.assertTrue(self.enhanced_metadata.supports_band("VHF"))
        self.assertTrue(self.enhanced_metadata.supports_band("UHF"))
        self.assertFalse(self.enhanced_metadata.supports_band("6m"))

    def test_power_for_frequency(self):
        """Test power level determination by frequency."""
        # VHF frequency should get VHF power
        vhf_power = self.enhanced_metadata.get_power_for_frequency(146.520)
        self.assertEqual(vhf_power, 5.0)

        # UHF frequency should get UHF power
        uhf_power = self.enhanced_metadata.get_power_for_frequency(440.000)
        self.assertEqual(uhf_power, 4.0)

        # Unsupported frequency
        no_power = self.enhanced_metadata.get_power_for_frequency(300.000)
        self.assertIsNone(no_power)

    def test_computed_properties(self):
        """Test computed properties."""
        self.assertEqual(self.enhanced_metadata.supported_bands, ["VHF", "UHF"])
        self.assertEqual(self.enhanced_metadata.frequency_range_mhz, (136.0, 520.0))
        self.assertTrue(self.enhanced_metadata.is_digital)
        self.assertEqual(self.enhanced_metadata.min_power_watts, 1.0)

    def test_string_representations(self):
        """Test string representations."""
        str_repr = str(self.enhanced_metadata)
        self.assertIn("Anytone AT-D878UV II Plus (Plus)", str_repr)
        self.assertIn("Handheld", str_repr)
        self.assertIn("Dual Band", str_repr)
        self.assertIn("5.0W", str_repr)

        repr_str = repr(self.enhanced_metadata)
        self.assertIn("EnhancedRadioMetadata", repr_str)
        self.assertIn("form_factor=FormFactor.HANDHELD", repr_str)


class TestEnums(TestCase):
    """Test enum functionality."""

    def test_form_factor_enum(self):
        """Test FormFactor enum values."""
        self.assertEqual(FormFactor.HANDHELD.value, "Handheld")
        self.assertEqual(FormFactor.MOBILE.value, "Mobile")
        self.assertEqual(FormFactor.BASE_STATION.value, "Base Station")

    def test_band_count_enum(self):
        """Test BandCount enum values."""
        self.assertEqual(BandCount.SINGLE_BAND.value, "Single Band")
        self.assertEqual(BandCount.DUAL_BAND.value, "Dual Band")
        self.assertEqual(BandCount.TRI_BAND.value, "Tri Band")
        self.assertEqual(BandCount.MULTI_BAND.value, "Multi Band")


class TestHelperFunctions(TestCase):
    """Test helper functions."""

    def test_determine_band_count(self):
        """Test band count determination."""
        single = [FrequencyRange("VHF", 144, 148, 12.5)]
        dual = [
            FrequencyRange("VHF", 144, 148, 12.5),
            FrequencyRange("UHF", 420, 450, 12.5),
        ]
        tri = dual + [FrequencyRange("1.25m", 220, 225, 12.5)]
        multi = tri + [FrequencyRange("70cm", 430, 440, 12.5)]

        self.assertEqual(determine_band_count([]), BandCount.SINGLE_BAND)
        self.assertEqual(determine_band_count(single), BandCount.SINGLE_BAND)
        self.assertEqual(determine_band_count(dual), BandCount.DUAL_BAND)
        self.assertEqual(determine_band_count(tri), BandCount.TRI_BAND)
        self.assertEqual(determine_band_count(multi), BandCount.MULTI_BAND)

    def test_determine_form_factor_from_model(self):
        """Test form factor determination from model name."""
        # Handheld (default)
        self.assertEqual(
            determine_form_factor_from_model("AT-D878UV II"), FormFactor.HANDHELD
        )

        # Mobile
        self.assertEqual(
            determine_form_factor_from_model("TM-D710GA Mobile"), FormFactor.MOBILE
        )

        # Base station
        self.assertEqual(
            determine_form_factor_from_model("IC-7300 Base"), FormFactor.BASE_STATION
        )


class TestFrequencyRange(TestCase):
    """Test FrequencyRange dataclass."""

    def test_frequency_range_creation(self):
        """Test creating frequency ranges."""
        vhf_range = FrequencyRange("VHF", 144.0, 148.0, 12.5, False)

        self.assertEqual(vhf_range.band_name, "VHF")
        self.assertEqual(vhf_range.min_freq_mhz, 144.0)
        self.assertEqual(vhf_range.max_freq_mhz, 148.0)
        self.assertEqual(vhf_range.step_size_khz, 12.5)
        self.assertFalse(vhf_range.rx_only)


class TestPowerLevel(TestCase):
    """Test PowerLevel dataclass."""

    def test_power_level_creation(self):
        """Test creating power levels."""
        high_power = PowerLevel("High", 50.0, ["VHF", "UHF"])

        self.assertEqual(high_power.name, "High")
        self.assertEqual(high_power.power_watts, 50.0)
        self.assertEqual(high_power.bands, ["VHF", "UHF"])


if __name__ == "__main__":
    pytest.main([__file__])
