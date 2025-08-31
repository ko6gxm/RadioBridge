"""Tests for CSV utilities module."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from radiobridge.csv_utils import (
    clean_csv_data,
    read_csv,
    validate_csv_columns,
    write_csv,
)


class TestReadWriteCSV:
    """Test CSV reading and writing functions."""

    def test_write_and_read_csv(self):
        """Test basic CSV write and read operations."""
        data = pd.DataFrame(
            {
                "frequency": ["146.520000", "147.000000"],
                "offset": ["+0.600000", "-0.600000"],
                "tone": ["123.0", "146.2"],
                "location": ["Repeater 1", "Repeater 2"],
            }
        )

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Write CSV
            write_csv(data, tmp_path)

            # Read it back
            result = read_csv(tmp_path, dtype=str)  # Read as strings to match input

            # Compare
            pd.testing.assert_frame_equal(data, result)

        finally:
            tmp_path.unlink()

    def test_write_empty_dataframe_raises_error(self):
        """Test that writing empty DataFrame raises ValueError."""
        empty_data = pd.DataFrame()

        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            tmp_path = Path(tmp.name)
            with pytest.raises(ValueError, match="Cannot write empty DataFrame"):
                write_csv(empty_data, tmp_path)

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            read_csv("/nonexistent/file.csv")


class TestValidateCSVColumns:
    """Test CSV column validation."""

    def test_validate_required_columns_present(self):
        """Test validation passes when required columns are present."""
        data = pd.DataFrame(
            {"frequency": ["146.520"], "tone": ["123.0"], "extra": ["value"]}
        )

        required = ["frequency", "tone"]
        assert validate_csv_columns(data, required) is True

    def test_validate_missing_required_columns_raises_error(self):
        """Test validation fails when required columns are missing."""
        data = pd.DataFrame({"frequency": ["146.520"], "extra": ["value"]})

        required = ["frequency", "tone", "offset"]
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_csv_columns(data, required)


class TestCleanCSVData:
    """Test CSV data cleaning functions."""

    def test_clean_csv_data_strips_whitespace(self):
        """Test that cleaning strips whitespace from string columns."""
        data = pd.DataFrame(
            {
                "frequency": ["  146.520  ", "147.000"],
                "location": ["  Test Location  ", "Another  "],
                "numeric": [1, 2],
            }
        )

        cleaned = clean_csv_data(data)

        assert cleaned["frequency"].iloc[0] == "146.520"
        assert cleaned["location"].iloc[0] == "Test Location"
        assert cleaned["location"].iloc[1] == "Another"
        assert cleaned["numeric"].iloc[0] == 1  # Numeric unchanged

    def test_clean_csv_data_replaces_empty_strings(self):
        """Test that empty strings are replaced with NaN."""
        data = pd.DataFrame({"frequency": ["146.520", ""], "tone": ["", "123.0"]})

        cleaned = clean_csv_data(data)

        assert pd.isna(cleaned["frequency"].iloc[1])
        assert pd.isna(cleaned["tone"].iloc[0])
        assert cleaned["tone"].iloc[1] == "123.0"
