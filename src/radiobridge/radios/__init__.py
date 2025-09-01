"""Radio formatters package.

This package contains formatters for various ham radio models.
Each formatter converts generic repeater data into the specific format
required by that radio's programming software.
"""

from typing import Dict, List, Optional, Tuple, Type

from radiobridge.logging_config import get_logger
from .base import BaseRadioFormatter
from .metadata import RadioMetadata
from .anytone_878_v3 import Anytone878V3Formatter
from .anytone_878_v4 import Anytone878V4Formatter
from .anytone_578 import Anytone578Formatter
from .baofeng_dm32uv import BaofengDM32UVFormatter
from .baofeng_k5_plus import BaofengK5PlusFormatter
from .baofeng_uv5r import BaofengUV5RFormatter
from .baofeng_uv28 import BaofengUV28Formatter
from .baofeng_uv25 import BaofengUV25Formatter
from .baofeng_uv5rm import BaofengUV5RMFormatter

# Registry of all available radio formatters
RADIO_FORMATTERS: Dict[str, Type[BaseRadioFormatter]] = {
    "anytone-878-v3": Anytone878V3Formatter,
    "anytone-878-v4": Anytone878V4Formatter,
    "anytone-578": Anytone578Formatter,
    "baofeng-dm32uv": BaofengDM32UVFormatter,
    "baofeng-k5-plus": BaofengK5PlusFormatter,
    "baofeng-uv5r": BaofengUV5RFormatter,
    "baofeng-uv28": BaofengUV28Formatter,
    "baofeng-uv25": BaofengUV25Formatter,
    "baofeng-uv5rm": BaofengUV5RMFormatter,
}

# Aliases for common radio names
RADIO_ALIASES: Dict[str, str] = {
    "anytone878": "anytone-878-v3",  # Default to v3 for backward compatibility
    "anytone_878": "anytone-878-v3",
    "878": "anytone-878-v3",
    "anytone878v3": "anytone-878-v3",
    "anytone-878v3": "anytone-878-v3",
    "878v3": "anytone-878-v3",
    "anytone878v4": "anytone-878-v4",
    "anytone-878v4": "anytone-878-v4",
    "878v4": "anytone-878-v4",
    "anytone578": "anytone-578",
    "anytone_578": "anytone-578",
    "578": "anytone-578",
    "dm32uv": "baofeng-dm32uv",
    "dm32": "baofeng-dm32uv",
    "dm-32uv": "baofeng-dm32uv",
    "k5": "baofeng-k5-plus",
    "k5plus": "baofeng-k5-plus",
    "k5+": "baofeng-k5-plus",
    "baofeng-k5": "baofeng-k5-plus",  # Backward compatibility
    "uv5r": "baofeng-uv5r",
    "uv-5r": "baofeng-uv5r",
    "uv_5r": "baofeng-uv5r",
    "5r": "baofeng-uv5r",
    "uv28": "baofeng-uv28",
    "uv-28": "baofeng-uv28",
    "uv_28": "baofeng-uv28",
    "28": "baofeng-uv28",
    "uv25": "baofeng-uv25",
    "uv-25": "baofeng-uv25",
    "uv_25": "baofeng-uv25",
    "25": "baofeng-uv25",
    "uv5rm": "baofeng-uv5rm",
    "uv-5rm": "baofeng-uv5rm",
    "uv_5rm": "baofeng-uv5rm",
    "5rm": "baofeng-uv5rm",
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
    logger = get_logger(__name__)
    logger.debug(
        f"Looking for formatter for radio: {radio_name}, Found aliases: {RADIO_ALIASES}"
    )

    # Normalize the radio name
    normalized_name = radio_name.lower().strip()

    # Check for direct match
    if normalized_name in RADIO_FORMATTERS:
        formatter_class = RADIO_FORMATTERS[normalized_name]
        logger.info(
            f"Found direct match for {radio_name} -> {formatter_class.__name__}"
        )
        return formatter_class()

    # Check for alias match
    if normalized_name in RADIO_ALIASES:
        canonical_name = RADIO_ALIASES[normalized_name]
        formatter_class = RADIO_FORMATTERS[canonical_name]
        logger.info(
            f"Found alias match for {radio_name} -> {canonical_name} -> "
            f"{formatter_class.__name__}"
        )
        return formatter_class()

    logger.warning(f"No formatter found for radio: {radio_name}")
    return None


def list_radio_options() -> List[Tuple[int, RadioMetadata]]:
    """Get numbered list of all radio options with detailed metadata.

    Flattens metadata from all registered formatters into a single numbered list.

    Returns:
        List of tuples (index, RadioMetadata) where index starts at 1
    """
    options = []
    index = 1

    for formatter_class in RADIO_FORMATTERS.values():
        formatter = formatter_class()
        for metadata in formatter.metadata:
            options.append((index, metadata))
            index += 1

    return options


def resolve_by_index(idx: int) -> Optional[BaseRadioFormatter]:
    """Resolve radio formatter by numbered index from list_radio_options.

    Args:
        idx: 1-based index from list_radio_options

    Returns:
        Formatter instance if found, None if index out of range
    """
    options = list_radio_options()

    if 1 <= idx <= len(options):
        _, metadata = options[idx - 1]  # Convert to 0-based
        return get_radio_formatter(metadata.formatter_key)

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
    "RadioMetadata",
    "get_supported_radios",
    "get_radio_formatter",
    "list_radio_info",
    "list_radio_options",
    "resolve_by_index",
    "RADIO_FORMATTERS",
    "RADIO_ALIASES",
]
