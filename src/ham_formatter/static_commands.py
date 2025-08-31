"""Helper functions for static frequency list commands.

This module contains the core business logic for static frequency list generation,
separated from CLI presentation logic so it can be shared between different
command interfaces.
"""

from typing import Dict, List, Optional, Union
import pandas as pd

from ham_formatter.enhanced_downloader import StaticOnlyDownloader
from ham_formatter.logging_config import get_logger


def list_available_static_lists() -> Dict[str, Dict[str, any]]:
    """Get available static frequency lists.

    Returns:
        Dictionary with list names and their metadata
    """
    downloader = StaticOnlyDownloader()
    return downloader.get_available_lists()


def validate_static_list_names(list_names: List[str]) -> None:
    """Validate that all provided list names are supported.

    Args:
        list_names: List of static frequency list names to validate

    Raises:
        ValueError: If any list names are invalid
    """
    available = list_available_static_lists()
    invalid_lists = set(list_names) - set(available.keys())
    if invalid_lists:
        valid_lists = list(available.keys())
        raise ValueError(f"Invalid lists: {invalid_lists}. Valid lists: {valid_lists}")


def validate_static_bands(bands: Optional[List[str]]) -> None:
    """Validate that all provided band names are supported for static lists.

    Args:
        bands: List of band names to validate

    Raises:
        ValueError: If any band names are invalid
    """
    if not bands:
        return

    # Get all supported bands from available lists
    available_lists = list_available_static_lists()
    all_supported_bands = set()
    for list_info in available_lists.values():
        all_supported_bands.update(list_info["supported_bands"])

    invalid_bands = set(bands) - all_supported_bands
    if invalid_bands:
        valid_bands = sorted(all_supported_bands)
        raise ValueError(
            f"Invalid bands: {invalid_bands}. Valid bands for static lists: {valid_bands}"
        )


def generate_static_lists(
    list_names: List[str], bands: Optional[List[str]] = None, location: str = "National"
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Generate specified static frequency lists.

    Args:
        list_names: Names of lists to generate
        bands: Optional band filtering
        location: Location description for the frequencies

    Returns:
        Single DataFrame if only one list requested, otherwise dict of DataFrames

    Raises:
        ValueError: If invalid list names or bands specified
    """
    logger = get_logger(__name__)

    # Validate inputs
    validate_static_list_names(list_names)
    validate_static_bands(bands)

    logger.info(f"Generating static frequency lists: {list_names}")
    if bands:
        logger.info(f"Filtering to bands: {bands}")

    # Generate the lists
    downloader = StaticOnlyDownloader()
    result_data = downloader.download_static_only(
        list_names, bands=bands, location=location
    )

    # Convert single DataFrame to dict format for consistency
    if isinstance(result_data, pd.DataFrame):
        result_data = {list_names[0]: result_data}

    return result_data


def save_static_output(
    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
    output_path: Optional[str],
    separate: bool = False,
) -> None:
    """Save generated frequency data to files or stdout.

    Args:
        data: DataFrame or dict of DataFrames with frequency data
        output_path: Output file path (may contain {} placeholder for separate files)
        separate: Whether to save separate files for each list

    Raises:
        ValueError: If separate=True but output_path doesn't contain {} placeholder
    """
    logger = get_logger(__name__)

    # Convert single DataFrame to dict for consistent handling
    if isinstance(data, pd.DataFrame):
        # Try to infer the list name, fallback to 'static'
        list_name = "static"
        if "category" in data.columns and not data["category"].empty:
            # Use first category as list name
            first_category = data["category"].iloc[0]
            if "Calling" in first_category:
                list_name = "national_calling"
            elif "Emergency" in first_category:
                list_name = "emergency_simplex"
        data = {list_name: data}

    if separate and len(data) > 1:
        if not output_path or "{}" not in output_path:
            raise ValueError(
                "Separate file output requires --output with {} placeholder "
                "(e.g., 'freqs_{}.csv')"
            )

        for list_name, df in data.items():
            file_path = output_path.format(list_name)
            df.to_csv(file_path, index=False)
            logger.info(f"Saved {len(df)} {list_name} frequencies to {file_path}")
    else:
        # Combine all DataFrames
        if len(data) == 1:
            combined_df = list(data.values())[0]
        else:
            combined_df = pd.concat(list(data.values()), ignore_index=True)

        if output_path:
            combined_df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(combined_df)} frequencies to {output_path}")
        else:
            # Print to stdout
            print(combined_df.to_csv(index=False), end="")


def format_static_list_info(list_info: Dict[str, any]) -> str:
    """Format static list information for display.

    Args:
        list_info: Dictionary with list metadata

    Returns:
        Formatted string describing the list
    """
    return (
        f"  Name: {list_info['name']}\n"
        f"  Description: {list_info['description']}\n"
        f"  Supported Bands: {', '.join(list_info['supported_bands'])}\n"
        f"  Frequency Count: {list_info['count']}"
    )
