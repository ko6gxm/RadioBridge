"""Radio formatters package.

This package contains formatters for various ham radio models.
Each formatter converts generic repeater data into the specific format
required by that radio's programming software.
"""

from typing import Dict, List, Optional, Type

from .base import BaseRadioFormatter
from .anytone_878 import Anytone878Formatter
from .anytone_578 import Anytone578Formatter
from .baofeng_dm32uv import BaofengDM32UVFormatter
from .baofeng_k5 import BaofengK5Formatter

# Registry of all available radio formatters
RADIO_FORMATTERS: Dict[str, Type[BaseRadioFormatter]] = {
    "anytone-878": Anytone878Formatter,
    "anytone-578": Anytone578Formatter,
    "baofeng-dm32uv": BaofengDM32UVFormatter,
    "baofeng-k5": BaofengK5Formatter,
}

# Aliases for common radio names
RADIO_ALIASES: Dict[str, str] = {
    "anytone878": "anytone-878",
    "anytone_878": "anytone-878",
    "878": "anytone-878",
    "anytone578": "anytone-578",
    "anytone_578": "anytone-578",
    "578": "anytone-578",
    "dm32uv": "baofeng-dm32uv",
    "dm32": "baofeng-dm32uv",
    "dm-32uv": "baofeng-dm32uv",
    "k5": "baofeng-k5",
    "k5plus": "baofeng-k5",
    "k5+": "baofeng-k5",
}


def get_supported_radios() -> List[str]:
    """Get a list of all supported radio models.

    Returns:
        List of supported radio model names
    """
    return list(RADIO_FORMATTERS.keys())


def get_radio_formatter(radio_name: str) -> Optional[BaseRadioFormatter]:
    """Get a formatter instance for the specified radio.

    Args:
        radio_name: Name of the radio model (case-insensitive)

    Returns:
        Formatter instance if found, None otherwise
    """
    # Normalize the radio name
    normalized_name = radio_name.lower().strip()

    # Check for direct match
    if normalized_name in RADIO_FORMATTERS:
        formatter_class = RADIO_FORMATTERS[normalized_name]
        return formatter_class()

    # Check for alias match
    if normalized_name in RADIO_ALIASES:
        canonical_name = RADIO_ALIASES[normalized_name]
        formatter_class = RADIO_FORMATTERS[canonical_name]
        return formatter_class()

    return None


def list_radio_info() -> Dict[str, Dict[str, str]]:
    """Get detailed information about all supported radios.

    Returns:
        Dictionary mapping radio names to their information
    """
    info = {}

    for radio_name, formatter_class in RADIO_FORMATTERS.items():
        formatter = formatter_class()
        info[radio_name] = {
            "name": formatter.radio_name,
            "description": formatter.description,
            "manufacturer": getattr(formatter, "manufacturer", "Unknown"),
            "model": getattr(formatter, "model", radio_name),
        }

    return info


__all__ = [
    "BaseRadioFormatter",
    "get_supported_radios",
    "get_radio_formatter",
    "list_radio_info",
    "RADIO_FORMATTERS",
    "RADIO_ALIASES",
]
