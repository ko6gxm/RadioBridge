"""Tests for CSV utilities module."""

import tempfile
from pathlib import Path

import pytest

from radiobridge.csv_utils import (
    clean_csv_data,
    read_csv,
    validate_csv_columns,
    write_csv,
)
from radiobridge.lightweight_data import LightDataFrame, is_null


class TestReadWriteCSV:
    """Test CSV reading and writing functions."""

    def test_write_and_read_csv(self):
        """Test basic CSV write and read operations."""
        data = LightDataFrame(
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
            assert isinstance(result, LightDataFrame)
            assert len(result) == len(data)
            assert result.columns == data.columns
            for col in data.columns:
                assert result[col] == data[col]

        finally:
            tmp_path.unlink()

    def test_write_empty_dataframe_raises_error(self):
        """Test that writing empty LightDataFrame raises ValueError."""
        empty_data = LightDataFrame()

        with tempfile.NamedTemporaryFile(suffix=".csv") as tmp:
            tmp_path = Path(tmp.name)
            with pytest.raises(ValueError, match="Cannot write empty"):
                write_csv(empty_data, tmp_path)

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            read_csv("/nonexistent/file.csv")


class TestValidateCSVColumns:
    """Test CSV column validation."""

    def test_validate_required_columns_present(self):
        """Test validation passes when required columns are present."""
        data = LightDataFrame(
            {"frequency": ["146.520"], "tone": ["123.0"], "extra": ["value"]}
        )

        required = ["frequency", "tone"]
        assert validate_csv_columns(data, required) is True

    def test_validate_missing_required_columns_raises_error(self):
        """Test validation fails when required columns are missing."""
        data = LightDataFrame({"frequency": ["146.520"], "extra": ["value"]})

        required = ["frequency", "tone", "offset"]
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_csv_columns(data, required)


class TestCleanCSVData:
    """Test CSV data cleaning functions."""

    def test_clean_csv_data_strips_whitespace(self):
        """Test that cleaning strips whitespace from string columns."""
        data = LightDataFrame(
            {
                "frequency": ["  146.520  ", "147.000"],
                "location": ["  Test Location  ", "Another  "],
                "numeric": [1, 2],
            }
        )

        cleaned = clean_csv_data(data)

        assert cleaned["frequency"][0] == "146.520"
        assert cleaned["location"][0] == "Test Location"
        assert cleaned["location"][1] == "Another"
        assert cleaned["numeric"][0] == 1  # Numeric unchanged

    def test_clean_csv_data_replaces_empty_strings(self):
        """Test that empty strings are replaced with None."""
        data = LightDataFrame({"frequency": ["146.520", ""], "tone": ["", "123.0"]})

        cleaned = clean_csv_data(data)

        assert is_null(cleaned["frequency"][1])
        assert is_null(cleaned["tone"][0])
        assert cleaned["tone"][1] == "123.0"
