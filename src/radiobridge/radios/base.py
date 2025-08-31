"""Base class for radio formatters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from radiobridge.logging_config import get_logger


class BaseRadioFormatter(ABC):
    """Abstract base class for radio formatters.

    All radio formatters must inherit from this class and implement
    the required methods for converting repeater data to their specific format.

    This base class also provides common utilities for:
    - Cleaning and formatting frequencies/offsets/tones
    - Extracting tone values from multiple possible column names
    - Deriving callsign and location values from varied input schemas
    - Building channel names in a consistent CallSign-Location format
    """

    def __init__(self):
        """Initialize the formatter."""
        self.logger = get_logger(self.__class__.__module__)
        self.logger.info(f"Initialized {self.radio_name} formatter")

    @property
    @abstractmethod
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        pass

    @property
    @abstractmethod
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        pass

    @property
    @abstractmethod
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        pass

    @abstractmethod
    def format(self, data: pd.DataFrame, start_channel: int = 1) -> pd.DataFrame:
        """Format repeater data for this radio.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)

        Returns:
            Formatted DataFrame ready for radio programming software

        Raises:
            ValueError: If input data is invalid or missing required columns
        """
        pass

    def validate_input(self, data: pd.DataFrame) -> bool:
        """Validate that input data has required columns.

        Args:
            data: Input DataFrame to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        self.logger.debug(
            f"Validating input data: {len(data)} rows, {len(data.columns)} columns"
        )
        self.logger.debug(f"Required columns: {self.required_columns}")
        self.logger.debug(f"Available columns: {list(data.columns)}")

        if data.empty:
            self.logger.error("Input data is empty")
            raise ValueError("Input data is empty")

        missing_columns = [
            col for col in self.required_columns if col not in data.columns
        ]

        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            raise ValueError(
                f"Missing required columns for {self.radio_name}: {missing_columns}. "
                f"Available columns: {list(data.columns)}"
            )

        self.logger.info(f"Input validation passed for {self.radio_name} formatter")
        return True

    def clean_frequency(self, freq: Any) -> Optional[str]:
        """Clean and format frequency data.

        Args:
            freq: Frequency value (string or numeric)

        Returns:
            Cleaned frequency string or None if invalid
        """
        if pd.isna(freq):
            return None

        freq_str = str(freq).strip()
        if not freq_str:
            return None

        # Remove common formatting
        freq_str = freq_str.replace(" MHz", "").replace("MHz", "").replace(" ", "")

        try:
            # Convert to float and back to string for consistency
            freq_float = float(freq_str)
            return f"{freq_float:.6f}"
        except ValueError:
            return None

    def clean_tone(self, tone: Any) -> Optional[str]:
        """Clean and format tone data.

        Args:
            tone: Tone value

        Returns:
            Cleaned tone string or None if invalid
        """
        if pd.isna(tone):
            return None

        tone_str = str(tone).strip()
        if not tone_str or tone_str.lower() in ("none", "n/a", "na", ""):
            return None

        # Remove common formatting
        tone_str = tone_str.replace(" Hz", "").replace("Hz", "").replace(" ", "")

        try:
            # Validate it's a reasonable tone frequency
            tone_float = float(tone_str)
            if 50.0 <= tone_float <= 300.0:  # Reasonable range for CTCSS tones
                return f"{tone_float:.1f}"
        except ValueError:
            pass

        return tone_str  # Return as-is if it's not numeric but not empty

    def get_tone_values(
        self, row: pd.Series, fallback_tone_column: str = "tone"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get tone_up and tone_down values from row data.

        Order of precedence:
        1) Explicit columns: tone_up / tone_down
        2) Common alt names: "Uplink Tone" (up), "Downlink Tone" (down)
        3) Fallback single tone column (same for up/down)
        """
        # First, try to get separate tone values
        tone_up = None
        tone_down = None

        if "tone_up" in row:
            tone_up = self.clean_tone(row.get("tone_up"))
        if "tone_down" in row:
            tone_down = self.clean_tone(row.get("tone_down"))

        # Try common alternate column names if still missing
        if tone_up is None and "Uplink Tone" in row:
            tone_up = self.clean_tone(row.get("Uplink Tone"))
        if tone_down is None and "Downlink Tone" in row:
            tone_down = self.clean_tone(row.get("Downlink Tone"))

        # If we have separate values, use them
        if tone_up is not None or tone_down is not None:
            return (tone_up, tone_down)

        # Fall back to single tone column for both values
        if fallback_tone_column in row:
            tone_value = self.clean_tone(row.get(fallback_tone_column))
            return (tone_value, tone_value)

        # No tone information available
        return (None, None)

    def get_rx_frequency(self, row: pd.Series) -> Any:
        """Retrieve RX frequency from common column names.

        Checks for both basic downloader format ('frequency') and
        detailed downloader format ('Downlink').
        """
        # Try detailed downloader format first
        if "Downlink" in row:
            return row.get("Downlink")
        # Fall back to basic downloader format
        if "frequency" in row:
            return row.get("frequency")
        return None

    def get_tx_frequency(self, row: pd.Series) -> Any:
        """Retrieve TX frequency from common column names.

        Checks for detailed downloader format ('Uplink').
        If not available, should calculate from RX + offset.
        """
        if "Uplink" in row:
            return row.get("Uplink")
        return None

    def get_offset_value(self, row: pd.Series) -> Any:
        """Retrieve an offset value from common column names.

        Looks for lowercase 'offset' first, then titlecase 'Offset'.
        Returns 0 if neither is present.
        """
        if "offset" in row:
            return row.get("offset")
        if "Offset" in row:
            return row.get("Offset")
        return 0

    def clean_offset(self, offset: Any) -> Optional[str]:
        """Clean and format offset data.

        Args:
            offset: Offset value

        Returns:
            Cleaned offset string or None if invalid
        """
        if pd.isna(offset):
            return None

        offset_str = str(offset).strip()
        if not offset_str:
            return None

        # Standardize common offset formats
        offset_str = offset_str.replace(" MHz", "").replace("MHz", "").replace(" ", "")

        # Handle +/- prefixes
        if offset_str.startswith(("+", "-")):
            try:
                offset_float = float(offset_str)
                return f"{offset_float:+.6f}"
            except ValueError:
                return offset_str

        try:
            offset_float = float(offset_str)
            if offset_float != 0:
                return f"{offset_float:+.6f}"  # Add + prefix for positive values
            else:
                return "0.000000"
        except ValueError:
            return offset_str

    # ------------------------- Callsign/Location helpers -------------------------
    def get_callsign(self, row: pd.Series) -> Optional[str]:
        """Extract callsign from common column names.

        Checks: 'callsign', 'call', 'Call' (in that order). Returns None if not found.
        """
        for key in ("callsign", "call", "Call"):
            if key in row:
                val = row.get(key)
                if pd.notna(val) and str(val).strip():
                    return str(val).strip()
        return None

    def get_location(self, row: pd.Series) -> Optional[str]:
        """Extract location from common columns or parse from Notes.

        Checks 'location', 'city'. If not present, attempts to parse 'Notes' for
        a pattern like 'Location: <value>' and returns the first clause up to
        a comma/semicolon/newline. Removes common suffix ', CA'.
        """
        for key in ("location", "city"):
            if key in row:
                val = row.get(key)
                if pd.notna(val) and str(val).strip():
                    return str(val).strip()

        # Try parsing from Notes
        if "Notes" in row and pd.notna(row.get("Notes")):
            import re

            notes = str(row.get("Notes"))
            match = re.search(r"Location:\s*([^;,\n]+)", notes)
            if match:
                loc = match.group(1).strip()
                loc = loc.replace(", CA", "").replace(" CA", "")
                if "," in loc:
                    loc = loc.split(",")[0].strip()
                return loc
        return None

    def build_channel_name(
        self,
        row: pd.Series,
        max_length: int,
        location_slice: int = 8,
        separator: str = "-",
    ) -> str:
        """Build a channel name in CallSign-Location format with fallbacks.

        - Uses callsign-location when both are available
        - If only one is available, returns that
        - Otherwise returns a placeholder (to be handled by caller if desired)
        The final string is truncated to max_length characters.
        """
        callsign = self.get_callsign(row) or ""
        location = self.get_location(row) or ""

        if callsign and location:
            name = f"{callsign}{separator}{location[:location_slice]}"
        elif callsign:
            name = callsign
        elif location:
            name = location[:location_slice]
        else:
            name = ""

        return name[:max_length]

    def resolve_channel_name_conflicts(
        self, channel_names: List[str], max_length: int
    ) -> List[str]:
        """Resolve channel name conflicts by adding numbers.

        Uses a global numbering approach to ensure all names are unique.

        Args:
            channel_names: List of channel names that may have conflicts
            max_length: Maximum length for channel names

        Returns:
            List of unique channel names with conflicts resolved
        """
        used_names = set()
        resolved_names = []

        for name in channel_names:
            if name not in used_names:
                # Name is unique, use as-is
                resolved_names.append(name)
                used_names.add(name)
            else:
                # Name conflicts, find a unique variant
                unique_name = self._find_unique_name(name, used_names, max_length)
                resolved_names.append(unique_name)
                used_names.add(unique_name)

        return resolved_names

    def _find_unique_name(
        self, base_name: str, used_names: set, max_length: int
    ) -> str:
        """Find a unique variant of base_name that hasn't been used.

        Strategy:
        1. Try shortening the location part and adding numbers
        2. If base_name has format 'CALLSIGN-LOCATION', progressively shorten LOCATION
        3. Add numbers until we find an unused name

        Args:
            base_name: The conflicting name to make unique
            used_names: Set of names already in use
            max_length: Maximum length for the name

        Returns:
            A unique name that fits within max_length
        """
        if "-" in base_name:
            callsign, location = base_name.split("-", 1)

            # Try progressively shorter location names with numbers
            for loc_len in range(len(location), 0, -1):
                for num in range(1, 100):  # Try numbers 1-99
                    # Calculate space needed for the number
                    num_str = str(num)
                    available_for_location = (
                        max_length - len(callsign) - 1 - len(num_str)
                    )

                    if available_for_location > 0:
                        shortened_loc = location[: min(loc_len, available_for_location)]
                        candidate = f"{callsign}-{shortened_loc}{num}"

                        if candidate not in used_names and len(candidate) <= max_length:
                            return candidate
        else:
            # For names without "-", just add numbers to the end
            for num in range(1, 100):
                num_str = str(num)
                available_for_base = max_length - len(num_str)
                base_part = base_name[:available_for_base]
                candidate = f"{base_part}{num}"

                if candidate not in used_names:
                    return candidate

        # Fallback: use a very short name with number if nothing else works
        for num in range(1, 1000):
            candidate = f"CH{num}"
            if candidate not in used_names and len(candidate) <= max_length:
                return candidate

        # Should never reach here, but provide a final fallback
        return f"CH{len(used_names)}"

    def _generate_unique_names(
        self, base_name: str, count: int, max_length: int, iteration: int = 0
    ) -> List[str]:
        """Generate unique names for a conflict group.

        Strategy:
        1. If base_name has format 'CALLSIGN-LOCATION', shorten LOCATION
        2. Add numbers (1, 2, 3, ...) to make unique
        3. Ensure total length stays within max_length

        Args:
            base_name: The conflicting name
            count: Number of unique names needed
            max_length: Maximum length constraint

        Returns:
            List of unique names
        """
        if "-" in base_name:
            # Split callsign and location parts
            callsign, location = base_name.split("-", 1)

            # Calculate space needed for numbers
            # For up to 9 conflicts: "1", "2", etc. (1 char)
            # For 10-99 conflicts: "10", "11", etc. (2 chars)
            max_num_digits = len(str(count))

            # Reserve space for separator and number
            available_for_location = max_length - len(callsign) - 1 - max_num_digits

            # Ensure we have at least 1 character for location
            if available_for_location < 1:
                available_for_location = 1

            # Shorten location to make room for numbers
            shortened_location = location[:available_for_location]

            # Generate numbered variants
            unique_names = []
            for i in range(1, count + 1):
                name = f"{callsign}-{shortened_location}{i}"
                unique_names.append(name[:max_length])

            return unique_names

    # ------------------------- Zone functionality -------------------------

    def supports_zone_files(self) -> bool:
        """Check if this radio supports zone files.

        Returns:
            True if the radio supports zone file generation
        """
        # Check if the subclass has overridden format_zones
        return (
            hasattr(self, "format_zones")
            and self.__class__.format_zones is not BaseRadioFormatter.format_zones
        )

    def format_zones(
        self,
        formatted_data: pd.DataFrame,
        csv_metadata: Optional[Dict[str, str]] = None,
        zone_strategy: str = "location",
        max_zones: int = 250,
        max_channels_per_zone: int = 64,
    ) -> pd.DataFrame:
        """Format zone data for this radio (optional).

        Args:
            formatted_data: DataFrame with formatted channel information
            csv_metadata: Metadata from CSV comments (contains county, state, city, etc.)
            zone_strategy: Strategy for creating zones ('location', 'band', 'service')
            max_zones: Maximum number of zones to create
            max_channels_per_zone: Maximum channels per zone

        Returns:
            Formatted DataFrame with zone information

        Raises:
            NotImplementedError: If this radio doesn't support zone files
        """
        raise NotImplementedError(
            f"{self.radio_name} does not support zone file generation"
        )

    def _get_zone_name_from_metadata(
        self,
        csv_metadata: Optional[Dict[str, str]] = None,
        zone_strategy: str = "location",
        max_length: int = 16,
    ) -> str:
        """Get zone name from CSV metadata based on strategy.

        Args:
            csv_metadata: Metadata from CSV comments
            zone_strategy: Zone naming strategy
            max_length: Maximum zone name length

        Returns:
            Zone name string
        """
        if not csv_metadata:
            return "Unknown"

        if zone_strategy == "location":
            # Priority: county -> city -> state
            if "county" in csv_metadata:
                zone_name = csv_metadata["county"]
            elif "city" in csv_metadata:
                zone_name = csv_metadata["city"]
            elif "state" in csv_metadata:
                zone_name = csv_metadata["state"]
            else:
                zone_name = "Unknown"

            # Add state abbreviation if we have county/city and state
            if (
                zone_name != "Unknown"
                and "state" in csv_metadata
                and zone_strategy == "location"
            ):
                state = csv_metadata["state"]
                # Try to fit both location and state within limit
                combined = f"{zone_name} {state}"
                if len(combined) <= max_length:
                    zone_name = combined

            return zone_name[:max_length]

        elif zone_strategy == "state":
            return csv_metadata.get("state", "Unknown")[:max_length]

        elif zone_strategy == "country":
            return csv_metadata.get("country", "Unknown")[:max_length]

        else:
            return "Mixed"[:max_length]
