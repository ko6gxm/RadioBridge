"""Static frequency list generators for amateur radio.

This module provides functionality to generate static lists of important
amateur radio frequencies that can be used alongside repeater data.
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from radiobridge.logging_config import get_logger


class StaticFrequencyGenerator:
    """Generate static frequency lists for amateur radio operations."""

    def __init__(self):
        """Initialize the static frequency generator."""
        self.logger = get_logger(__name__)

    def generate_national_calling_frequencies(
        self, bands: Optional[List[str]] = None, location: str = "National"
    ) -> pd.DataFrame:
        """Generate National Calling Frequencies for VHF/UHF bands.

        National calling frequencies are designated simplex frequencies used
        for initial contact attempts and emergency communications.

        Args:
            bands: List of bands to include ('2m', '1.25m', '70cm').
                   If None, includes all supported bands.
            location: Location description for the frequencies (default: "National")

        Returns:
            DataFrame with calling frequency data compatible with radio formatters

        Raises:
            ValueError: If invalid band specified
        """
        self.logger.info("Generating National Calling Frequencies")

        # Define national calling frequencies
        calling_frequencies = {
            "2m": {
                "frequency": 146.52,
                "band_name": "2 Meter",
                "description": "National 2m Calling Frequency",
                "mode": "FM",
                "offset": 0.0,
                "tone": None,
                "usage": "Simplex calling and emergency",
            },
            "1.25m": {
                "frequency": 223.5,
                "band_name": "1.25 Meter",
                "description": "National 1.25m Calling Frequency",
                "mode": "FM",
                "offset": 0.0,
                "tone": None,
                "usage": "Simplex calling and emergency",
            },
            "70cm": {
                "frequency": 446.0,
                "band_name": "70 Centimeter",
                "description": "National 70cm Calling Frequency",
                "mode": "FM",
                "offset": 0.0,
                "tone": None,
                "usage": "Simplex calling and emergency",
            },
        }

        # Filter by requested bands if specified
        if bands:
            # Validate bands
            valid_bands = set(calling_frequencies.keys())
            invalid_bands = set(bands) - valid_bands
            if invalid_bands:
                raise ValueError(
                    f"Invalid bands: {invalid_bands}. Valid bands: {valid_bands}"
                )

            # Filter to requested bands
            filtered_frequencies = {
                band: freq_data
                for band, freq_data in calling_frequencies.items()
                if band in bands
            }
        else:
            filtered_frequencies = calling_frequencies

        # Convert to DataFrame format compatible with radio formatters
        frequency_list = []

        for band, freq_data in filtered_frequencies.items():
            row = {
                # Standard columns expected by radio formatters
                "frequency": freq_data["frequency"],
                "offset": freq_data["offset"],
                "tone": freq_data["tone"],
                "mode": freq_data["mode"],
                "type": "Simplex",
                "service": "Amateur",
                # Naming and description
                "callsign": f"CALL-{band.upper()}",
                "location": location,
                "name": freq_data["description"],
                "notes": freq_data["usage"],
                # Additional metadata
                "band": band,
                "band_name": freq_data["band_name"],
                "use": "Calling",
                "category": "National Calling",
            }
            frequency_list.append(row)

        result_df = pd.DataFrame(frequency_list)

        self.logger.info(f"Generated {len(result_df)} national calling frequencies")
        self.logger.debug(f"Bands included: {list(filtered_frequencies.keys())}")

        return result_df

    def generate_emergency_simplex_frequencies(
        self, bands: Optional[List[str]] = None, location: str = "National"
    ) -> pd.DataFrame:
        """Generate emergency simplex frequencies for VHF/UHF bands.

        Args:
            bands: List of bands to include ('2m', '70cm').
                   If None, includes all supported bands.
            location: Location description for the frequencies

        Returns:
            DataFrame with emergency simplex frequency data
        """
        self.logger.info("Generating Emergency Simplex Frequencies")

        # Define emergency simplex frequencies
        emergency_frequencies = {
            "2m": [
                {
                    "frequency": 146.49,
                    "description": "2m Emergency Simplex",
                    "usage": "Emergency communications",
                },
                {
                    "frequency": 146.58,
                    "description": "2m ARES/RACES Simplex",
                    "usage": "ARES/RACES emergency operations",
                },
            ],
            "70cm": [
                {
                    "frequency": 446.5,
                    "description": "70cm Emergency Simplex",
                    "usage": "Emergency communications",
                }
            ],
        }

        # Filter by requested bands if specified
        if bands:
            valid_bands = set(emergency_frequencies.keys())
            invalid_bands = set(bands) - valid_bands
            if invalid_bands:
                raise ValueError(
                    f"Invalid bands: {invalid_bands}. Valid bands: {valid_bands}"
                )

            filtered_frequencies = {
                band: freqs
                for band, freqs in emergency_frequencies.items()
                if band in bands
            }
        else:
            filtered_frequencies = emergency_frequencies

        # Convert to DataFrame format
        frequency_list = []

        for band, freq_list in filtered_frequencies.items():
            for i, freq_data in enumerate(freq_list, 1):
                row = {
                    "frequency": freq_data["frequency"],
                    "offset": 0.0,
                    "tone": None,
                    "mode": "FM",
                    "type": "Simplex",
                    "service": "Amateur",
                    "callsign": f"EMRG-{band.upper()}-{i}",
                    "location": location,
                    "name": freq_data["description"],
                    "notes": freq_data["usage"],
                    "band": band,
                    "use": "Emergency",
                    "category": "Emergency Simplex",
                }
                frequency_list.append(row)

        result_df = pd.DataFrame(frequency_list)

        self.logger.info(f"Generated {len(result_df)} emergency simplex frequencies")
        return result_df

    def get_available_lists(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available static frequency lists.

        Returns:
            Dictionary with list names and their metadata
        """
        return {
            "national_calling": {
                "name": "National Calling Frequencies",
                "description": "National calling frequencies for 2m, 1.25m, and 70cm bands",
                "supported_bands": ["2m", "1.25m", "70cm"],
                "count": 3,
                "generator_method": "generate_national_calling_frequencies",
            },
            "emergency_simplex": {
                "name": "Emergency Simplex Frequencies",
                "description": "Emergency and ARES/RACES simplex frequencies",
                "supported_bands": ["2m", "70cm"],
                "count": 3,
                "generator_method": "generate_emergency_simplex_frequencies",
            },
        }
