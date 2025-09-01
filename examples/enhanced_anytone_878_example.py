#!/usr/bin/env python3
"""Example of enhanced Anytone 878 formatter with comprehensive metadata.

This example shows how to extend the existing Anytone 878 formatter with
enhanced metadata including form factor, band count, and maximum power.
"""

from datetime import date
from typing import List

from src.radiobridge.radios.enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel,
)
from src.radiobridge.radios.anytone_878 import Anytone878Formatter


def create_enhanced_anytone_878_metadata() -> List[EnhancedRadioMetadata]:
    """Create enhanced metadata for Anytone AT-D878UV II variants."""

    # Define common frequency ranges for dual-band VHF/UHF
    frequency_ranges = [
        FrequencyRange(
            band_name="VHF",
            min_freq_mhz=136.000,
            max_freq_mhz=174.000,
            step_size_khz=12.5,
        ),
        FrequencyRange(
            band_name="UHF",
            min_freq_mhz=400.000,
            max_freq_mhz=520.000,
            step_size_khz=12.5,
        ),
    ]

    # Define power levels
    power_levels = [
        PowerLevel(name="Low", power_watts=1.0, bands=["VHF", "UHF"]),
        PowerLevel(name="Medium", power_watts=2.5, bands=["VHF", "UHF"]),
        PowerLevel(name="High", power_watts=5.0, bands=["VHF"]),  # VHF max power
        PowerLevel(name="High", power_watts=4.0, bands=["UHF"]),  # UHF max power
    ]

    # AT-D878UV II Plus (Enhanced version)
    plus_metadata = EnhancedRadioMetadata(
        # Legacy fields
        manufacturer="Anytone",
        model="AT-D878UV II Plus",
        radio_version="Plus",
        firmware_versions=["1.24", "1.23", "1.22"],
        cps_versions=[
            "Anytone_CPS_3.00_3.08",
            "Anytone_CPS_4.00",
            "CHIRP_next_20240801_20250401",
        ],
        formatter_key="anytone-878",
        # Enhanced priority fields
        form_factor=FormFactor.HANDHELD,
        band_count=BandCount.DUAL_BAND,
        max_power_watts=5.0,  # VHF max power
        # Technical specifications
        frequency_ranges=frequency_ranges,
        power_levels=power_levels,
        modulation_modes=["FM", "DMR"],
        # Physical characteristics
        dimensions_mm=(58, 110, 32),  # W x H x D
        weight_grams=267,
        display_type="LCD",
        antenna_connector="SMA-Female",
        # Features
        digital_modes=["DMR"],
        memory_channels=4000,
        zones=250,
        gps_enabled=True,
        bluetooth_enabled=True,
        # Market information
        launch_date=date(2019, 3, 1),  # Approximate launch date
        msrp_usd=189.99,
        target_markets=["Amateur", "Commercial"],
        # Legacy compatibility
        legacy_description="Dual-band DMR/Analog handheld with GPS and Bluetooth",
    )

    # AT-D878UV II Standard (Basic version)
    standard_metadata = EnhancedRadioMetadata(
        # Legacy fields
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
        # Enhanced priority fields
        form_factor=FormFactor.HANDHELD,
        band_count=BandCount.DUAL_BAND,
        max_power_watts=5.0,  # Same power as Plus version
        # Technical specifications
        frequency_ranges=frequency_ranges,
        power_levels=power_levels,
        modulation_modes=["FM", "DMR"],
        # Physical characteristics
        dimensions_mm=(58, 110, 32),  # Same as Plus
        weight_grams=267,
        display_type="LCD",
        antenna_connector="SMA-Female",
        # Features (reduced compared to Plus)
        digital_modes=["DMR"],
        memory_channels=4000,
        zones=250,
        gps_enabled=False,  # No GPS on standard version
        bluetooth_enabled=False,  # No Bluetooth on standard version
        # Market information
        launch_date=date(2018, 9, 1),  # Earlier launch than Plus
        msrp_usd=169.99,  # Lower price than Plus
        target_markets=["Amateur", "Commercial"],
        # Legacy compatibility
        legacy_description="Dual-band DMR/Analog handheld radio",
    )

    return [plus_metadata, standard_metadata]


class EnhancedAnytone878Formatter(Anytone878Formatter):
    """Enhanced Anytone 878 formatter with comprehensive metadata."""

    def __init__(self):
        super().__init__()
        self._enhanced_metadata = create_enhanced_anytone_878_metadata()

    @property
    def enhanced_metadata(self) -> List[EnhancedRadioMetadata]:
        """Get enhanced metadata for all radio variants."""
        return self._enhanced_metadata

    def get_enhanced_metadata_by_version(self, version: str) -> EnhancedRadioMetadata:
        """Get enhanced metadata for a specific radio version.

        Args:
            version: Radio version ("Plus" or "Standard")

        Returns:
            Enhanced metadata for the specified version

        Raises:
            ValueError: If version not found
        """
        for metadata in self._enhanced_metadata:
            if metadata.radio_version.lower() == version.lower():
                return metadata

        raise ValueError(f"No enhanced metadata found for version: {version}")

    def supports_frequency(self, freq_mhz: float, version: str = "Plus") -> bool:
        """Check if a specific radio version supports a frequency.

        Args:
            freq_mhz: Frequency in MHz
            version: Radio version to check

        Returns:
            True if frequency is supported
        """
        try:
            metadata = self.get_enhanced_metadata_by_version(version)
            return metadata.supports_frequency(freq_mhz)
        except ValueError:
            return False

    def get_power_for_frequency(self, freq_mhz: float, version: str = "Plus") -> float:
        """Get maximum power for a frequency on a specific radio version.

        Args:
            freq_mhz: Frequency in MHz
            version: Radio version to check

        Returns:
            Maximum power in watts, or 0.0 if not supported
        """
        try:
            metadata = self.get_enhanced_metadata_by_version(version)
            power = metadata.get_power_for_frequency(freq_mhz)
            return power if power is not None else 0.0
        except ValueError:
            return 0.0


def main():
    """Demonstration of enhanced metadata usage."""

    # Create enhanced formatter
    formatter = EnhancedAnytone878Formatter()

    print("=== Enhanced Anytone AT-D878UV II Metadata ===")
    print()

    for metadata in formatter.enhanced_metadata:
        print(f"Radio: {metadata}")
        print(f"  Form Factor: {metadata.form_factor.value}")
        print(f"  Band Count: {metadata.band_count.value}")
        print(f"  Max Power: {metadata.max_power_watts}W")
        print(
            f"  Frequency Range: {metadata.frequency_range_mhz[0]:.3f} - {metadata.frequency_range_mhz[1]:.3f} MHz"
        )
        print(f"  Supported Bands: {', '.join(metadata.supported_bands)}")
        print(f"  Digital Modes: {', '.join(metadata.digital_modes)}")
        print(f"  Memory Channels: {metadata.memory_channels}")
        print(f"  GPS: {'Yes' if metadata.gps_enabled else 'No'}")
        print(f"  Bluetooth: {'Yes' if metadata.bluetooth_enabled else 'No'}")
        print(f"  MSRP: ${metadata.msrp_usd}")
        print()

    # Demonstrate frequency checking
    test_frequencies = [146.520, 440.000, 300.000, 900.000]  # MHz

    print("=== Frequency Support Test ===")
    for freq in test_frequencies:
        plus_supported = formatter.supports_frequency(freq, "Plus")
        std_supported = formatter.supports_frequency(freq, "Standard")
        plus_power = formatter.get_power_for_frequency(freq, "Plus")

        print(
            f"{freq} MHz: Plus={plus_supported}, Standard={std_supported}, Power={plus_power}W"
        )

    # Show backward compatibility
    print("\n=== Backward Compatibility ===")
    legacy_metadata = formatter.enhanced_metadata[0].to_legacy_metadata()
    print(f"Legacy format: {legacy_metadata}")


if __name__ == "__main__":
    main()
