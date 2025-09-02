"""Lightweight base class for radio formatters without pandas dependency.

This module provides the same functionality as base.py but using lightweight
data structures instead of pandas, for faster startup times.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from ..lightweight_data import LightDataFrame, LightSeries, is_null
import logging
from .metadata import RadioMetadata

# Pandas has been completely removed from RadioBridge


class BaseRadioFormatter(ABC):
    """Abstract base class for radio formatters using lightweight data structures.

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
        self.logger = logging.getLogger(self.__class__.__module__)
        self.logger.debug(f"Initialized {self.radio_name} formatter")

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

    @property
    @abstractmethod
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions.

        Returns:
            List of RadioMetadata objects representing all supported combinations
            of manufacturer, model, radio_version, firmware_versions, and cps_versions
            for this formatter.
        """
        pass

    @abstractmethod
    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        """Format repeater data for this radio.

        Args:
            data: Input LightDataFrame with repeater information
            start_channel: Starting channel number (default: 1)
            cps_version: CPS version to optimize output for (optional)

        Returns:
            Formatted LightDataFrame ready for radio programming software

        Raises:
            ValueError: If input data is invalid or missing required columns
        """
        pass

    def validate_input(self, data: LightDataFrame) -> bool:
        """Validate that input data has required columns.

        Args:
            data: Input LightDataFrame to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        self.logger.debug(
            f"Validating input data: {len(data)} rows, {len(data.columns)} columns"
        )
        self.logger.debug(f"Required columns: {self.required_columns}")
        self.logger.debug(f"Available columns: {data.columns}")

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
                f"Available columns: {data.columns}"
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
        if is_null(freq):
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
        if is_null(tone):
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
        self, row: LightSeries, fallback_tone_column: str = "tone"
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

        # Fallback to single tone column for both if neither was found
        if tone_up is None and tone_down is None:
            # Try common single tone column names
            tone_value = None
            for col in ["PL", fallback_tone_column, "tone", "ctcss"]:
                if col in row:
                    tone_value = self.clean_tone(row.get(col))
                    if tone_value:
                        break
            
            if tone_value:
                tone_up = tone_value
                tone_down = tone_value

        return tone_up, tone_down

    def get_offset_direction_and_freq(self, row: LightSeries) -> Tuple[Optional[str], Optional[str]]:
        """Extract offset direction and frequency from row data.

        Args:
            row: Row data

        Returns:
            Tuple of (offset_direction, offset_frequency)
        """
        offset_direction = None
        offset_frequency = None

        # Try to get offset information
        if "offset" in row:
            offset_str = row.get("offset", "").strip()
            if offset_str:
                # Parse offset string like "+0.600000" or "-0.600000"
                if offset_str.startswith("+"):
                    offset_direction = "+"
                    offset_frequency = offset_str[1:].strip()
                elif offset_str.startswith("-"):
                    offset_direction = "-"
                    offset_frequency = offset_str[1:].strip()
                else:
                    offset_frequency = offset_str

        # Try separate columns
        if "offset_direction" in row:
            offset_direction = row.get("offset_direction", "").strip()
        if "offset_frequency" in row or "offset_freq" in row:
            offset_frequency = row.get("offset_frequency") or row.get("offset_freq", "")
            if offset_frequency:
                offset_frequency = str(offset_frequency).strip()

        return offset_direction, offset_frequency


    def parse_frequency_mhz(self, freq_str: str) -> Optional[float]:
        """Parse frequency string to MHz float.

        Args:
            freq_str: Frequency string

        Returns:
            Frequency in MHz or None if invalid
        """
        if not freq_str:
            return None

        try:
            # Remove common suffixes and parse
            clean_freq = freq_str.replace(" MHz", "").replace("MHz", "").strip()
            return float(clean_freq)
        except ValueError:
            return None

    def format_frequency_mhz(self, freq: float, decimals: int = 6) -> str:
        """Format frequency as MHz string.

        Args:
            freq: Frequency in MHz
            decimals: Number of decimal places

        Returns:
            Formatted frequency string
        """
        return f"{freq:.{decimals}f}"

    def create_output_dataframe(self, data_dict: Dict[str, List[Any]]) -> LightDataFrame:
        """Create output LightDataFrame from dictionary of column data.

        Args:
            data_dict: Dictionary mapping column names to lists of values

        Returns:
            LightDataFrame with the data
        """
        return LightDataFrame(data_dict, list(data_dict.keys()))
    
    def _normalize_input_data(self, data: Union[LightDataFrame, Any]) -> LightDataFrame:
        """Normalize input data to LightDataFrame for consistent processing.
        
        Args:
            data: Input data (must be LightDataFrame)
            
        Returns:
            LightDataFrame equivalent of the input data
        """
        # If data is already LightDataFrame, return as-is
        if isinstance(data, LightDataFrame):
            return data
            
        # If it looks like a DataFrame but isn't recognized, try to work with it
        # This handles cases where someone passes something else with similar interface
        try:
            # Try to convert using common DataFrame interface
            records = data.to_dict(orient='records')
            return LightDataFrame.from_records(records)
        except (AttributeError, TypeError):
            pass
            
        # If all else fails, raise an error
        raise TypeError(f"Unsupported data type: {type(data)}. Expected LightDataFrame.")
    
    def _normalize_row_data(self, row: Any, row_index: int = 0) -> LightSeries:
        """Normalize row data to LightSeries for consistent processing.
        
        Args:
            row: Row data (LightSeries or dict-like)
            row_index: Row index for error reporting
            
        Returns:
            LightSeries equivalent of the row data
        """
        # If row is already LightSeries, return as-is
        if isinstance(row, LightSeries):
            return row
            
        # If it's a dict-like object, convert it  
        if hasattr(row, 'keys') and hasattr(row, '__getitem__'):
            try:
                row_dict = {str(key): row[key] for key in row.keys()}
                return LightSeries(row_dict)
            except Exception:
                pass
                
        # If it looks like it has a to_dict method, try that
        if hasattr(row, 'to_dict'):
            try:
                return LightSeries(row.to_dict())
            except Exception:
                pass
                
        # If all else fails, raise an error
        raise TypeError(f"Unsupported row type at index {row_index}: {type(row)}. Expected LightSeries or dict-like object.")
    
    def get_rx_frequency(self, row: LightSeries) -> Any:
        """Get RX frequency from row data.
        
        Args:
            row: Row data
            
        Returns:
            RX frequency value
        """
        return (
            row.get("Downlink") or
            row.get("Input_Freq") or 
            row.get("frequency") or 
            row.get("rx_frequency") or 
            row.get("rx_freq")
        )
    
    def get_tx_frequency(self, row: LightSeries) -> Any:
        """Get TX frequency from row data.
        
        Args:
            row: Row data
            
        Returns:
            TX frequency value
        """
        return (
            row.get("Uplink") or
            row.get("tx_frequency") or 
            row.get("tx_freq")
        )
    
    def get_offset_value(self, row: LightSeries) -> Any:
        """Get offset value from row data.
        
        Args:
            row: Row data
            
        Returns:
            Offset value
        """
        return row.get("Offset") or row.get("offset")
    
    def clean_offset(self, offset: Any) -> Optional[str]:
        """Clean and format offset data.
        
        Args:
            offset: Offset value
            
        Returns:
            Cleaned offset string or None if invalid
        """
        if is_null(offset):
            return None
            
        offset_str = str(offset).strip()
        if not offset_str:
            return None
            
        # Handle signed offsets
        if offset_str.startswith(('+', '-')):
            try:
                # Convert to float and back for consistency
                offset_float = float(offset_str)
                return f"{offset_float:+.6f}"  # Include sign
            except ValueError:
                return None
        
        try:
            offset_float = float(offset_str)
            # Explicitly include '+' sign for positive non-zero offsets to match expectations
            if offset_float == 0.0:
                return f"{offset_float:.6f}"
            return f"{offset_float:+.6f}"
        except ValueError:
            return None
    
    def build_channel_name(self, row: LightSeries, max_length: int = 16, location_slice: int = 8) -> str:
        """Build a channel name from callsign and location.

        Args:
            row: Row data
            max_length: Maximum length for channel name
            location_slice: Maximum characters to use from location

        Returns:
            Formatted channel name
        """
        # Get callsign and location
        callsign = (row.get("Callsign") or row.get("callsign") or "").strip()
        location = (row.get("Location") or row.get("location") or "").strip()

        if not callsign and not location:
            return "Unknown"

        # Build name
        if callsign and location:
            # Truncate location if needed
            if len(location) > location_slice:
                location = location[:location_slice]
            channel_name = f"{callsign}-{location}"
        elif callsign:
            channel_name = callsign
        else:
            channel_name = location

        # Truncate if too long
        if len(channel_name) > max_length:
            channel_name = channel_name[:max_length]

        return channel_name
    
    def resolve_channel_name_conflicts(self, names: List[str], max_length: int = 16) -> List[str]:
        """Resolve duplicate channel names by adding suffixes.
        
        Args:
            names: List of channel names
            max_length: Maximum length for channel names
            
        Returns:
            List of unique channel names
        """
        seen = {}
        result = []
        
        for name in names:
            if name not in seen:
                seen[name] = 0
                result.append(name)
            else:
                seen[name] += 1
                suffix = f"_{seen[name]}"
                # Truncate base name to fit suffix
                base_length = max_length - len(suffix)
                if base_length > 0:
                    unique_name = name[:base_length] + suffix
                else:
                    unique_name = f"CH{seen[name]}"
                result.append(unique_name)
        
        return result

    # ------------------------- Zone functionality -------------------------
    def _get_zone_name_from_metadata(
        self,
        csv_metadata: Optional[Dict[str, str]] = None,
        zone_strategy: str = "location",
        max_length: int = 16,
    ) -> str:
        """Get zone name from CSV metadata based on strategy.

        Args:
            csv_metadata: Metadata from CSV comments
            zone_strategy: Zone naming strategy (e.g., 'location', 'state', 'country')
            max_length: Maximum zone name length

        Returns:
            Zone name string (truncated to max_length)
        """
        if not csv_metadata:
            return "Unknown"

        # Normalize metadata keys to lowercase to be tolerant of input like {'County': 'X'}
        meta = {str(k).lower(): v for k, v in csv_metadata.items()}

        if zone_strategy == "location":
            # Priority: county -> city -> state
            zone_name = (
                meta.get("county")
                or meta.get("city")
                or meta.get("state")
                or "Unknown"
            )

            # Append state if available and it fits, e.g., "Los Angeles CA"
            state = meta.get("state")
            if zone_name != "Unknown" and state:
                combined = f"{zone_name} {state}"
                if len(combined) <= max_length:
                    zone_name = combined

            return str(zone_name)[:max_length]

        if zone_strategy == "state":
            return str(meta.get("state", "Unknown"))[:max_length]

        if zone_strategy == "country":
            return str(meta.get("country", "Unknown"))[:max_length]

        # Default fallback
        return "Mixed"[:max_length]

    def validate_cps_version(self, cps_version: str) -> bool:
        """Validate that the specified CPS version is supported by this radio.

        Args:
            cps_version: CPS version string to validate

        Returns:
            True if the CPS version is supported, False otherwise
        """
        if not cps_version:
            return True  # None/empty is always valid (use default behavior)

        # Get all supported CPS versions from metadata
        supported_versions = set()
        for metadata in self.metadata:
            supported_versions.update(metadata.cps_versions)

        # Normalize user input: convert spaces to underscores for comparison
        normalized_user = cps_version.replace(" ", "_")

        # Check for exact match first (after normalization)
        if normalized_user in supported_versions:
            return True

        # Check for version range matches
        for supported in supported_versions:
            if self._version_matches_range(normalized_user, supported):
                return True

        # Check for partial matches (e.g., "CHIRP next" matching CHIRP ranges)
        cps_lower = cps_version.lower()
        for supported in supported_versions:
            supported_lower = supported.lower()

            # Handle CHIRP-style matching (user says "CHIRP next DATE"
            # matches "CHIRP_next_DATE1_DATE2")
            if "chirp" in cps_lower and "chirp" in supported_lower:
                # Extract date from user input if present
                user_words = cps_lower.split()
                if (
                    len(user_words) >= 3
                    and user_words[0] == "chirp"
                    and user_words[1] == "next"
                ):
                    user_date_part = user_words[2]

                    # Handle dash-separated date ranges like "20240901-20250401"
                    if "-" in user_date_part:
                        # For exact range matches, normalize to underscore format
                        date_range = user_date_part.replace("-", "_")
                        expected_format = f"chirp_next_{date_range}"
                        if expected_format in supported_lower:
                            return True
                    else:
                        # Single date - check if it falls within any range
                        if self._date_in_chirp_range(user_date_part, supported):
                            return True
                # Also match if user just says "CHIRP next" without specific date
                elif (
                    len(user_words) == 2
                    and user_words[0] == "chirp"
                    and user_words[1] == "next"
                ):
                    if "chirp_next" in supported_lower:
                        return True

        return False

    def _version_matches_range(self, user_version: str, supported_range: str) -> bool:
        """Check if a user-specified version falls within a supported range.

        Args:
            user_version: Version string from user (e.g., "Anytone_CPS_3.05")
            supported_range: Range string from metadata (e.g., "Anytone_CPS_3.00_3.08")

        Returns:
            True if the user version is within the supported range
        """
        try:
            # Handle CPS version ranges like "Anytone_CPS_3.00_3.08"
            if "_CPS_" in supported_range and "_CPS_" in user_version:
                range_parts = supported_range.split("_")
                user_parts = user_version.split("_")

                # Find CPS position in both range and user parts
                range_cps_idx = -1
                user_cps_idx = -1

                for i, part in enumerate(range_parts):
                    if part == "CPS":
                        range_cps_idx = i
                        break

                for i, part in enumerate(user_parts):
                    if part == "CPS":
                        user_cps_idx = i
                        break

                # Check if we found CPS in both and have enough parts for a range
                if (
                    range_cps_idx >= 1
                    and user_cps_idx >= 1
                    and len(range_parts) >= range_cps_idx + 3  # CPS + start + end
                    and len(user_parts) >= user_cps_idx + 2
                ):  # CPS + version

                    # Check if base names match (everything before and including CPS)
                    range_base = "_".join(
                        range_parts[: range_cps_idx + 1]
                    )  # e.g., "DM_32UV_CPS"
                    user_base = "_".join(
                        user_parts[: user_cps_idx + 1]
                    )  # e.g., "DM_32UV_CPS"

                    if range_base == user_base:
                        # Extract version components
                        user_ver = user_parts[user_cps_idx + 1]  # e.g., "2.10"
                        range_start = range_parts[range_cps_idx + 1]  # e.g., "2.08"
                        range_end = range_parts[range_cps_idx + 2]  # e.g., "2.12"

                        # Version comparison - handle both simple and complex versions
                        try:
                            # Try simple float comparison first
                            user_float = float(user_ver)
                            start_float = float(range_start)
                            end_float = float(range_end)
                            return start_float <= user_float <= end_float
                        except ValueError:
                            # Handle complex version numbers like "2.0.6" or "1.2.3.4"
                            try:
                                return self._compare_version_strings(
                                    user_ver, range_start, range_end
                                )
                            except Exception:
                                pass

            return False
        except (IndexError, ValueError):
            return False

    def _date_in_chirp_range(self, user_date: str, supported_range: str) -> bool:
        """Check if a user date falls within a CHIRP date range.

        Args:
            user_date: Date string from user (e.g., "20241201")
            supported_range: CHIRP range string (e.g., "CHIRP_next_20240801_20250401")

        Returns:
            True if the user date is within the supported range
        """
        try:
            # Extract start and end dates from supported range
            if "chirp_next" in supported_range.lower():
                parts = supported_range.split("_")
                if len(parts) >= 4:  # ["CHIRP", "next", start_date, end_date]
                    start_date = parts[2]
                    end_date = parts[3]

                    # Simple string comparison for YYYYMMDD dates
                    if (
                        len(user_date) == 8
                        and len(start_date) == 8
                        and len(end_date) == 8
                    ):
                        return start_date <= user_date <= end_date

            return False
        except (IndexError, ValueError):
            return False

    def _compare_version_strings(
        self, user_ver: str, range_start: str, range_end: str
    ) -> bool:
        """Compare complex version strings like '2.0.6' with range '2.0.6' to '2.1.8'.

        Args:
            user_ver: User version string (e.g., "2.0.6")
            range_start: Start of range (e.g., "2.0.6")
            range_end: End of range (e.g., "2.1.8")

        Returns:
            True if user_ver falls within the range
        """
        try:

            def parse_version(version_str: str):
                """Parse version string into list of integers."""
                return [int(x) for x in version_str.split(".")]

            user_parts = parse_version(user_ver)
            start_parts = parse_version(range_start)
            end_parts = parse_version(range_end)

            # Pad shorter versions with zeros for comparison
            max_len = max(len(user_parts), len(start_parts), len(end_parts))

            user_parts += [0] * (max_len - len(user_parts))
            start_parts += [0] * (max_len - len(start_parts))
            end_parts += [0] * (max_len - len(end_parts))

            # Compare as tuples
            return tuple(start_parts) <= tuple(user_parts) <= tuple(end_parts)
        except (ValueError, TypeError):
            # Fallback to string comparison if numeric parsing fails
            return range_start <= user_ver <= range_end

    def get_supported_cps_versions(self) -> List[str]:
        """Get all supported CPS versions for this radio.

        Returns:
            List of supported CPS version strings
        """
        supported_versions = set()
        for metadata in self.metadata:
            supported_versions.update(metadata.cps_versions)
        return sorted(list(supported_versions))
