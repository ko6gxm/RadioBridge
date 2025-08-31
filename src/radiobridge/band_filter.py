"""Amateur radio band filtering utilities.

This module provides constants and utilities for filtering repeater data
by amateur radio bands (2m, 70cm, etc.).
"""

from typing import Dict, List, Tuple

from radiobridge.logging_config import get_logger

logger = get_logger(__name__)

# Amateur radio band definitions (frequency ranges in MHz)
AMATEUR_BANDS: Dict[str, Tuple[float, float]] = {
    # VHF Bands
    "6m": (50.0, 54.0),  # 6 meters
    "4m": (70.0, 70.5),  # 4 meters (Region 2)
    "2m": (144.0, 148.0),  # 2 meters
    # UHF Bands
    "70cm": (420.0, 450.0),  # 70 centimeters
    "33cm": (902.0, 928.0),  # 33 centimeters
    "23cm": (1240.0, 1300.0),  # 23 centimeters
    # Common aliases
    "vhf": (144.0, 148.0),  # VHF alias for 2m
    "uhf": (420.0, 450.0),  # UHF alias for 70cm
}

# RepeaterBook.com band parameter mappings
REPEATERBOOK_BAND_PARAMS: Dict[str, str] = {
    "6m": "6m",
    "4m": "4m",
    "2m": "2m",
    "vhf": "2m",
    "70cm": "440",
    "uhf": "440",
    "33cm": "900",
    "23cm": "1200",
    "all": "All",
}


def get_supported_bands() -> List[str]:
    """Get list of supported amateur radio bands.

    Returns:
        List of supported band names
    """
    # Return main bands (exclude aliases like vhf/uhf)
    return ["6m", "4m", "2m", "70cm", "33cm", "23cm", "all"]


def validate_bands(bands: List[str]) -> List[str]:
    """Validate and normalize band specifications.

    Args:
        bands: List of band names to validate

    Returns:
        List of validated and normalized band names

    Raises:
        ValueError: If any band is not supported
    """
    if not bands:
        return ["all"]

    normalized_bands = []
    supported = set(AMATEUR_BANDS.keys()) | {"all"}

    for band in bands:
        band_lower = band.lower().strip()

        if band_lower not in supported:
            supported_list = ", ".join(sorted(get_supported_bands()))
            raise ValueError(
                f"Unsupported band '{band}'. Supported bands: {supported_list}"
            )

        # Normalize aliases
        if band_lower == "vhf":
            band_lower = "2m"
        elif band_lower == "uhf":
            band_lower = "70cm"

        if band_lower not in normalized_bands:
            normalized_bands.append(band_lower)

    logger.debug(f"Validated bands: {bands} -> {normalized_bands}")
    return normalized_bands


def get_repeaterbook_band_param(bands: List[str]) -> str:
    """Get RepeaterBook.com band parameter for given bands.

    Args:
        bands: List of normalized band names

    Returns:
        RepeaterBook band parameter string
    """
    if "all" in bands or len(bands) > 1:
        # Use "All" for multiple bands or explicit "all"
        return "All"

    band = bands[0]
    param = REPEATERBOOK_BAND_PARAMS.get(band, "All")
    logger.debug(f"Band {band} -> RepeaterBook parameter: {param}")
    return param


def filter_by_frequency(data, bands: List[str]):
    """Filter DataFrame by frequency ranges for specified bands.

    Args:
        data: DataFrame with 'frequency' column
        bands: List of band names to include

    Returns:
        Filtered DataFrame containing only specified bands
    """
    import pandas as pd

    if "all" in bands:
        logger.debug("Band filter set to 'all', returning all data")
        return data

    if "frequency" not in data.columns:
        logger.warning("No 'frequency' column found, returning unfiltered data")
        return data

    logger.debug(f"Filtering {len(data)} rows by bands: {bands}")

    # Create frequency mask
    mask = pd.Series([False] * len(data), index=data.index)

    for band in bands:
        if band in AMATEUR_BANDS:
            freq_min, freq_max = AMATEUR_BANDS[band]

            # Convert frequency column to numeric, handling various formats
            freq_numeric = pd.to_numeric(data["frequency"], errors="coerce")

            # Create mask for this band
            band_mask = (freq_numeric >= freq_min) & (freq_numeric <= freq_max)
            mask = mask | band_mask

            matches = band_mask.sum()
            logger.debug(f"Band {band} ({freq_min}-{freq_max} MHz): {matches} matches")

    filtered_data = data[mask].copy()
    logger.info(
        f"Band filtering complete: {len(filtered_data)} of {len(data)} rows "
        f"match bands {bands}"
    )

    return filtered_data


def format_band_list(bands: List[str]) -> str:
    """Format band list for display purposes.

    Args:
        bands: List of band names

    Returns:
        Formatted string representation
    """
    if not bands or "all" in bands:
        return "all bands"

    if len(bands) == 1:
        return f"{bands[0]} band"

    if len(bands) == 2:
        return f"{bands[0]} and {bands[1]} bands"

    return f"{', '.join(bands[:-1])}, and {bands[-1]} bands"
