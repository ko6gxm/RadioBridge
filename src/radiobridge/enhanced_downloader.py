"""Enhanced downloader with static frequency list support.

This module extends the base downloader functionality to include
generation of static frequency lists alongside repeater data.
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd

from radiobridge.downloader import RepeaterBookDownloader
from radiobridge.static_lists import StaticFrequencyGenerator
from radiobridge.logging_config import get_logger


class EnhancedDownloader:
    """Enhanced downloader that can combine repeater data with static frequency lists."""

    def __init__(self, timeout: int = 30):
        """Initialize the enhanced downloader.

        Args:
            timeout: Request timeout in seconds for repeater downloads
        """
        self.repeater_downloader = RepeaterBookDownloader(timeout=timeout)
        self.static_generator = StaticFrequencyGenerator()
        self.logger = get_logger(__name__)

    def download_with_static_lists(
        self,
        location_type: str,
        static_lists: Optional[List[str]] = None,
        combine_data: bool = True,
        **kwargs,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Download repeater data and generate static frequency lists.

        Args:
            location_type: Type of location download ('state', 'county', 'city')
            static_lists: List of static frequency lists to generate
                         ('national_calling', 'emergency_simplex')
            combine_data: If True, combine all data into single DataFrame.
                         If False, return separate DataFrames in dict.
            **kwargs: Arguments for location-specific download (state, county, city, etc.)

        Returns:
            Combined DataFrame if combine_data=True, otherwise dict with separate DataFrames

        Raises:
            ValueError: If invalid location_type or static_lists specified
        """
        self.logger.info(f"Starting enhanced download for {location_type}")

        # Validate location type
        valid_location_types = ["state", "county", "city"]
        if location_type not in valid_location_types:
            raise ValueError(
                f"Invalid location_type: {location_type}. Valid types: {valid_location_types}"
            )

        # Download repeater data
        repeater_data = self._download_repeater_data(location_type, **kwargs)
        self.logger.info(f"Downloaded {len(repeater_data)} repeaters")

        # Generate static frequency lists
        static_data = {}
        if static_lists:
            for list_name in static_lists:
                static_df = self._generate_static_list(list_name, **kwargs)
                static_data[list_name] = static_df
                self.logger.info(f"Generated {len(static_df)} {list_name} frequencies")

        # Return combined or separate data
        if combine_data:
            return self._combine_data(repeater_data, static_data)
        else:
            result = {"repeaters": repeater_data}
            result.update(static_data)
            return result

    def download_static_only(
        self,
        static_lists: List[str],
        bands: Optional[List[str]] = None,
        location: str = "National",
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Generate only static frequency lists without repeater data.

        Args:
            static_lists: List of static frequency lists to generate
            bands: List of bands to include in generated lists
            location: Location description for the frequencies

        Returns:
            Combined DataFrame if single list, dict of DataFrames if multiple lists
        """
        self.logger.info(f"Generating static frequency lists: {static_lists}")

        static_data = {}
        for list_name in static_lists:
            static_df = self._generate_static_list(
                list_name, bands=bands, location=location
            )
            static_data[list_name] = static_df
            self.logger.info(f"Generated {len(static_df)} {list_name} frequencies")

        # Return single DataFrame if only one list, otherwise return dict
        if len(static_data) == 1:
            return list(static_data.values())[0]
        else:
            return static_data

    def get_available_static_lists(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available static frequency lists.

        Returns:
            Dictionary with list names and their metadata
        """
        return self.static_generator.get_available_lists()

    def _download_repeater_data(self, location_type: str, **kwargs) -> pd.DataFrame:
        """Download repeater data using the appropriate method.

        Args:
            location_type: Type of location download
            **kwargs: Arguments for location-specific download

        Returns:
            DataFrame with repeater data
        """
        if location_type == "state":
            return self.repeater_downloader.download_by_state(**kwargs)
        elif location_type == "county":
            return self.repeater_downloader.download_by_county(**kwargs)
        elif location_type == "city":
            return self.repeater_downloader.download_by_city(**kwargs)
        else:
            raise ValueError(f"Unsupported location_type: {location_type}")

    def _generate_static_list(self, list_name: str, **kwargs) -> pd.DataFrame:
        """Generate a specific static frequency list.

        Args:
            list_name: Name of the static list to generate
            **kwargs: Additional arguments for list generation

        Returns:
            DataFrame with static frequency data

        Raises:
            ValueError: If list_name is not supported
        """
        available_lists = self.static_generator.get_available_lists()

        if list_name not in available_lists:
            valid_lists = list(available_lists.keys())
            raise ValueError(
                f"Invalid static list: {list_name}. Valid lists: {valid_lists}"
            )

        # Get the generator method and call it
        method_name = available_lists[list_name]["generator_method"]
        generator_method = getattr(self.static_generator, method_name)

        # Filter kwargs to only include parameters the method accepts
        import inspect

        sig = inspect.signature(generator_method)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

        return generator_method(**filtered_kwargs)

    def _combine_data(
        self, repeater_data: pd.DataFrame, static_data: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """Combine repeater data with static frequency lists.

        Args:
            repeater_data: DataFrame with repeater data
            static_data: Dict of DataFrames with static frequency data

        Returns:
            Combined DataFrame with all frequency data
        """
        if not static_data:
            return repeater_data

        # Combine all static DataFrames
        static_dfs = list(static_data.values())
        if len(static_dfs) == 1:
            combined_static = static_dfs[0]
        else:
            combined_static = pd.concat(static_dfs, ignore_index=True)

        # Combine repeater data with static data
        # Put static frequencies first (they're typically lower priority channels)
        combined_df = pd.concat([combined_static, repeater_data], ignore_index=True)

        self.logger.info(
            f"Combined data: {len(combined_static)} static + {len(repeater_data)} repeaters = {len(combined_df)} total"
        )

        return combined_df


class StaticOnlyDownloader:
    """Simple interface for generating only static frequency lists."""

    def __init__(self):
        """Initialize the static-only downloader."""
        self.static_generator = StaticFrequencyGenerator()
        self.logger = get_logger(__name__)

    def generate_national_calling_frequencies(
        self, bands: Optional[List[str]] = None, location: str = "National"
    ) -> pd.DataFrame:
        """Generate National Calling Frequencies.

        Args:
            bands: List of bands to include ('2m', '1.25m', '70cm')
            location: Location description

        Returns:
            DataFrame with national calling frequencies
        """
        return self.static_generator.generate_national_calling_frequencies(
            bands, location
        )

    def generate_emergency_simplex_frequencies(
        self, bands: Optional[List[str]] = None, location: str = "National"
    ) -> pd.DataFrame:
        """Generate Emergency Simplex Frequencies.

        Args:
            bands: List of bands to include ('2m', '70cm')
            location: Location description

        Returns:
            DataFrame with emergency simplex frequencies
        """
        return self.static_generator.generate_emergency_simplex_frequencies(
            bands, location
        )

    def download_static_only(
        self,
        static_lists: List[str],
        bands: Optional[List[str]] = None,
        location: str = "National",
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Generate only static frequency lists without repeater data.

        Args:
            static_lists: List of static frequency lists to generate
            bands: List of bands to include in generated lists
            location: Location description for the frequencies

        Returns:
            Combined DataFrame if single list, dict of DataFrames if multiple lists
        """
        self.logger.info(f"Generating static frequency lists: {static_lists}")

        static_data = {}
        for list_name in static_lists:
            if list_name == "national_calling":
                static_df = self.generate_national_calling_frequencies(bands, location)
            elif list_name == "emergency_simplex":
                static_df = self.generate_emergency_simplex_frequencies(bands, location)
            else:
                available = self.get_available_lists()
                valid_lists = list(available.keys())
                raise ValueError(
                    f"Invalid static list: {list_name}. Valid lists: {valid_lists}"
                )

            static_data[list_name] = static_df
            self.logger.info(f"Generated {len(static_df)} {list_name} frequencies")

        # Return single DataFrame if only one list, otherwise return dict
        if len(static_data) == 1:
            return list(static_data.values())[0]
        else:
            return static_data

    def get_available_lists(self) -> Dict[str, Dict[str, Any]]:
        """Get available static frequency lists."""
        return self.static_generator.get_available_lists()
