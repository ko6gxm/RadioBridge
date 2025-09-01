"""Enhanced radio metadata for comprehensive radio specifications.

This module defines enhanced metadata structures that extend beyond the basic
RadioMetadata to capture physical characteristics, RF capabilities, and other
important radio specifications.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import date

from .metadata import RadioMetadata


class FormFactor(Enum):
    """Radio form factor categories."""

    HANDHELD = "Handheld"
    MOBILE = "Mobile"
    BASE_STATION = "Base Station"


class BandCount(Enum):
    """Number of supported frequency bands."""

    SINGLE_BAND = "Single Band"
    DUAL_BAND = "Dual Band"
    TRI_BAND = "Tri Band"
    MULTI_BAND = "Multi Band"  # For 4+ bands


@dataclass
class FrequencyRange:
    """Frequency range specification for a radio band."""

    band_name: str  # "VHF", "UHF", "700MHz", "800MHz", "1.25m"
    min_freq_mhz: float
    max_freq_mhz: float
    step_size_khz: float = 12.5
    rx_only: bool = False


@dataclass
class PowerLevel:
    """Power level specification."""

    name: str  # "Low", "Medium", "High"
    power_watts: float
    bands: List[str] = field(
        default_factory=list
    )  # Which bands support this power level


@dataclass
class EnhancedRadioMetadata:
    """Enhanced radio metadata with comprehensive specifications.

    Extends the basic RadioMetadata with detailed technical specifications
    while maintaining backward compatibility.
    """

    # Core identification (from existing RadioMetadata)
    manufacturer: str
    model: str
    radio_version: str
    firmware_versions: List[str]
    cps_versions: List[str]
    formatter_key: str

    # Enhanced metadata - Priority Fields
    form_factor: FormFactor
    band_count: BandCount
    max_power_watts: float

    # Enhanced metadata - Technical Specifications
    frequency_ranges: List[FrequencyRange] = field(default_factory=list)
    power_levels: List[PowerLevel] = field(default_factory=list)
    modulation_modes: List[str] = field(default_factory=list)  # ["FM", "DMR", "D-STAR"]

    # Enhanced metadata - Physical Characteristics
    dimensions_mm: Optional[tuple] = None  # (width, height, depth)
    weight_grams: Optional[int] = None
    display_type: Optional[str] = None  # "LCD", "OLED", "LED", "None"
    antenna_connector: Optional[str] = None  # "SMA-Female", "BNC", "N-Type"

    # Enhanced metadata - Features
    digital_modes: List[str] = field(default_factory=list)  # ["DMR", "D-STAR", "P25"]
    memory_channels: Optional[int] = None
    zones: Optional[int] = None
    gps_enabled: bool = False
    bluetooth_enabled: bool = False

    # Enhanced metadata - Market Information
    launch_date: Optional[date] = None
    discontinued_date: Optional[date] = None
    msrp_usd: Optional[float] = None
    target_markets: List[str] = field(
        default_factory=list
    )  # ["Amateur", "Commercial", "Public Safety"]

    # Legacy compatibility
    legacy_description: Optional[str] = None

    @classmethod
    def from_legacy_metadata(
        cls, legacy: RadioMetadata, **enhanced_kwargs
    ) -> "EnhancedRadioMetadata":
        """Create enhanced metadata from legacy RadioMetadata.

        Args:
            legacy: Existing RadioMetadata instance
            **enhanced_kwargs: Additional enhanced metadata fields

        Returns:
            New EnhancedRadioMetadata instance
        """
        return cls(
            manufacturer=legacy.manufacturer,
            model=legacy.model,
            radio_version=legacy.radio_version,
            firmware_versions=legacy.firmware_versions,
            cps_versions=legacy.cps_versions,
            formatter_key=legacy.formatter_key,
            **enhanced_kwargs,
        )

    def to_legacy_metadata(self) -> RadioMetadata:
        """Convert to legacy RadioMetadata for backward compatibility.

        Returns:
            RadioMetadata instance with core fields
        """
        return RadioMetadata(
            manufacturer=self.manufacturer,
            model=self.model,
            radio_version=self.radio_version,
            firmware_versions=self.firmware_versions,
            cps_versions=self.cps_versions,
            formatter_key=self.formatter_key,
        )

    @property
    def full_model_name(self) -> str:
        """Get the full model name including version."""
        return f"{self.model} ({self.radio_version})"

    @property
    def supported_bands(self) -> List[str]:
        """Get list of supported band names."""
        return [r.band_name for r in self.frequency_ranges]

    @property
    def frequency_range_mhz(self) -> tuple:
        """Get overall frequency range as (min, max) tuple."""
        if not self.frequency_ranges:
            return (0.0, 0.0)
        min_freq = min(r.min_freq_mhz for r in self.frequency_ranges)
        max_freq = max(r.max_freq_mhz for r in self.frequency_ranges)
        return (min_freq, max_freq)

    @property
    def is_digital(self) -> bool:
        """Check if radio supports digital modes."""
        return len(self.digital_modes) > 0

    @property
    def min_power_watts(self) -> float:
        """Get minimum power level."""
        if not self.power_levels:
            return 0.0
        return min(p.power_watts for p in self.power_levels)

    def supports_band(self, band_name: str) -> bool:
        """Check if radio supports a specific band.

        Args:
            band_name: Band name to check (e.g., "VHF", "UHF")

        Returns:
            True if band is supported
        """
        return band_name in self.supported_bands

    def supports_frequency(self, freq_mhz: float) -> bool:
        """Check if radio supports a specific frequency.

        Args:
            freq_mhz: Frequency in MHz

        Returns:
            True if frequency is within any supported range
        """
        for freq_range in self.frequency_ranges:
            if freq_range.min_freq_mhz <= freq_mhz <= freq_range.max_freq_mhz:
                return True
        return False

    def get_power_for_frequency(self, freq_mhz: float) -> Optional[float]:
        """Get maximum power available for a specific frequency.

        Args:
            freq_mhz: Frequency in MHz

        Returns:
            Maximum power in watts, or None if frequency not supported
        """
        # Find which band this frequency belongs to
        band_name = None
        for freq_range in self.frequency_ranges:
            if freq_range.min_freq_mhz <= freq_mhz <= freq_range.max_freq_mhz:
                band_name = freq_range.band_name
                break

        if not band_name:
            return None

        # Find maximum power for this band
        max_power = 0.0
        for power_level in self.power_levels:
            if not power_level.bands or band_name in power_level.bands:
                max_power = max(max_power, power_level.power_watts)

        return max_power if max_power > 0 else None

    def __str__(self) -> str:
        """Human-readable string representation."""
        bands_str = f"{self.band_count.value}"
        power_str = f"{self.max_power_watts}W"

        return (
            f"{self.manufacturer} {self.model} ({self.radio_version}) - "
            f"{self.form_factor.value}, {bands_str}, {power_str} max"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"EnhancedRadioMetadata(manufacturer='{self.manufacturer}', "
            f"model='{self.model}', radio_version='{self.radio_version}', "
            f"form_factor={self.form_factor}, band_count={self.band_count}, "
            f"max_power_watts={self.max_power_watts})"
        )


def determine_band_count(frequency_ranges: List[FrequencyRange]) -> BandCount:
    """Determine band count from frequency ranges.

    Args:
        frequency_ranges: List of frequency ranges

    Returns:
        Appropriate BandCount enum value
    """
    count = len(frequency_ranges)
    if count <= 1:
        return BandCount.SINGLE_BAND
    elif count == 2:
        return BandCount.DUAL_BAND
    elif count == 3:
        return BandCount.TRI_BAND
    else:
        return BandCount.MULTI_BAND


def determine_form_factor_from_model(model: str) -> FormFactor:
    """Attempt to determine form factor from model name.

    This is a helper function for migration from legacy metadata.

    Args:
        model: Radio model name

    Returns:
        Best-guess FormFactor enum value
    """
    model_lower = model.lower()

    # Mobile indicators
    if any(
        keyword in model_lower for keyword in ["mobile", "car", "dash", "vehicular"]
    ):
        return FormFactor.MOBILE

    # Base station indicators
    if any(keyword in model_lower for keyword in ["base", "desktop", "repeater"]):
        return FormFactor.BASE_STATION

    # Default to handheld for most radios
    return FormFactor.HANDHELD
