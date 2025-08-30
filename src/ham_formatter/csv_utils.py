"""CSV utilities for reading and writing repeater data."""

from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd

from ham_formatter.logging_config import get_logger

logger = get_logger(__name__)


def read_csv(
    file_path: Union[str, Path], encoding: str = "utf-8", **kwargs: Any
) -> pd.DataFrame:
    """Read a CSV file into a pandas DataFrame.

    Args:
        file_path: Path to the CSV file
        encoding: File encoding (default: utf-8)
        **kwargs: Additional arguments passed to pandas.read_csv()

    Returns:
        DataFrame containing the CSV data

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed as CSV
    """
    logger.info(f"Reading CSV file: {file_path}")

    try:
        df = pd.read_csv(file_path, encoding=encoding, **kwargs)
        logger.info(f"Successfully read CSV: {len(df)} rows, {len(df.columns)} columns")
        logger.debug(f"CSV columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    except Exception as e:
        logger.error(f"Failed to parse CSV file {file_path}: {e}")
        raise ValueError(f"Error reading CSV file {file_path}: {e}")


def write_csv(
    data: pd.DataFrame,
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    index: bool = False,
    **kwargs: Any,
) -> None:
    """Write a pandas DataFrame to a CSV file.

    Args:
        data: DataFrame to write
        file_path: Output file path
        encoding: File encoding (default: utf-8)
        index: Whether to write row indices (default: False)
        **kwargs: Additional arguments passed to pandas.DataFrame.to_csv()

    Raises:
        ValueError: If data is empty or invalid
        OSError: If the file cannot be written
    """
    logger.info(
        f"Writing CSV file: {file_path} ({len(data)} rows, {len(data.columns)} columns)"
    )

    if data.empty:
        logger.error("Cannot write empty DataFrame")
        raise ValueError("Cannot write empty DataFrame to CSV")

    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created parent directory: {Path(file_path).parent}")

    try:
        logger.debug(f"CSV write options: encoding={encoding}, index={index}")
        data.to_csv(file_path, encoding=encoding, index=index, **kwargs)
        logger.info(f"Successfully wrote CSV file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to write CSV file {file_path}: {e}")
        raise OSError(f"Error writing CSV file {file_path}: {e}")


def validate_csv_columns(
    data: pd.DataFrame,
    required_columns: list[str],
    optional_columns: Optional[list[str]] = None,
) -> bool:
    """Validate that a DataFrame has the required columns.

    Args:
        data: DataFrame to validate
        required_columns: List of column names that must be present
        optional_columns: List of column names that may be present

    Returns:
        True if validation passes

    Raises:
        ValueError: If required columns are missing
    """
    logger.debug(
        f"Validating columns. Required: {required_columns}, Present: {list(data.columns)}"
    )

    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Available columns: {list(data.columns)}"
        )

    logger.info(
        f"Column validation passed: all {len(required_columns)} required columns present"
    )
    return True


def clean_csv_data(data: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize CSV data.

    Args:
        data: Raw DataFrame to clean

    Returns:
        Cleaned DataFrame
    """
    logger.debug(
        f"Starting CSV data cleaning: {len(data)} rows, {len(data.columns)} columns"
    )

    # Make a copy to avoid modifying the original
    cleaned = data.copy()

    # Strip whitespace from string columns
    string_columns = cleaned.select_dtypes(include=["object"]).columns
    logger.debug(
        f"Cleaning {len(string_columns)} string columns: {list(string_columns)}"
    )

    cleaned[string_columns] = cleaned[string_columns].apply(
        lambda x: x.str.strip() if hasattr(x, "str") else x
    )

    # Replace empty strings with NaN for consistency
    empty_count = (cleaned == "").sum().sum()
    cleaned = cleaned.replace("", pd.NA)

    if empty_count > 0:
        logger.debug(f"Replaced {empty_count} empty strings with NaN")

    logger.debug("CSV data cleaning complete")
    return cleaned
