"""Tests for the downloader module's new county and city functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import responses

from ham_formatter.downloader import (
    RepeaterBookDownloader,
    download_repeater_data,
    download_repeater_data_by_county,
    download_repeater_data_by_city,
)


class TestRepeaterBookDownloader:
    """Test the RepeaterBookDownloader class."""

    def test_init(self):
        """Test downloader initialization."""
        downloader = RepeaterBookDownloader(timeout=60)
        assert downloader.timeout == 60
        assert downloader.BASE_URL == "https://www.repeaterbook.com"
        assert (
            downloader.session.headers["User-Agent"]
            == "ham-formatter/0.2.0 (Amateur Radio Tool)"
        )

    def test_build_params_state(self):
        """Test parameter building for state-level search."""
        downloader = RepeaterBookDownloader()
        params = downloader._build_params("state", state="CA", country="United States")

        expected = {
            "state_id": "06",  # CA -> 06
            "band": "All",
            "type": "state",
        }
        assert params == expected

    def test_build_params_county(self):
        """Test parameter building for county-level search."""
        downloader = RepeaterBookDownloader()
        params = downloader._build_params(
            "county", state="CA", county="Los Angeles", country="United States"
        )

        expected = {
            "state_id": "06",  # CA -> 06
            "band": "All",
            "type": "county",
            "loc": "Los Angeles",
        }
        assert params == expected

    def test_build_params_city(self):
        """Test parameter building for city-level search."""
        downloader = RepeaterBookDownloader()
        params = downloader._build_params(
            "city", state="TX", city="Austin", country="United States"
        )

        expected = {
            "state_id": "48",  # TX -> 48
            "band": "All",
            "type": "city",
            "loc": "Austin",
        }
        assert params == expected

    def test_get_state_id(self):
        """Test state code to ID mapping."""
        downloader = RepeaterBookDownloader()

        # Test common states
        assert downloader._get_state_id("CA") == "06"
        assert downloader._get_state_id("TX") == "48"
        assert downloader._get_state_id("NY") == "36"
        assert downloader._get_state_id("FL") == "12"

        # Test case insensitivity
        assert downloader._get_state_id("ca") == "06"
        assert downloader._get_state_id("tx") == "48"

        # Test unknown state (should return as-is)
        assert downloader._get_state_id("ZZ") == "ZZ"

    @responses.activate
    def test_download_by_county_success(self):
        """Test successful county-level download."""
        # Load fixture
        fixture_path = Path(__file__).parent / "fixtures" / "county_search_sample.html"
        with open(fixture_path) as f:
            html_content = f.read()

        # Mock the HTTP response with new URL structure
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/downloads/index.php",
            status=404,  # Force fallback to HTML scraping
        )
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/location_search.php",
            body=html_content,
            status=200,
        )

        downloader = RepeaterBookDownloader()
        df = downloader.download_by_county("CA", "Los Angeles")

        # Verify results
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "frequency" in df.columns
        assert df.iloc[0]["frequency"] == 146.52
        assert df.iloc[0]["callsign"] == "W6ABC"
        assert df.iloc[1]["frequency"] == 147.0
        assert df.iloc[1]["callsign"] == "K6XYZ"

    @responses.activate
    def test_download_by_city_success(self):
        """Test successful city-level download."""
        # Load fixture
        fixture_path = Path(__file__).parent / "fixtures" / "city_search_sample.html"
        with open(fixture_path) as f:
            html_content = f.read()

        # Mock the HTTP response with new URL structure
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/downloads/index.php",
            status=404,  # Force fallback to HTML scraping
        )
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/location_search.php",
            body=html_content,
            status=200,
        )

        downloader = RepeaterBookDownloader()
        df = downloader.download_by_city("TX", "Austin")

        # Verify results
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "frequency" in df.columns
        assert df.iloc[0]["frequency"] == 444.125
        assert df.iloc[0]["callsign"] == "N5DEF"

    @responses.activate
    def test_download_by_county_no_table_found(self):
        """Test error when no table is found for county search."""
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/downloads/index.php",
            status=404,  # Force fallback to HTML scraping
        )
        responses.add(
            responses.GET,
            "https://www.repeaterbook.com/repeaters/location_search.php",
            body="<html><body><p>No repeaters found</p></body></html>",
            status=200,
        )

        downloader = RepeaterBookDownloader()
        with pytest.raises(
            ValueError, match="No repeater table found for Los Angeles County, 06"
        ):
            downloader.download_by_county("CA", "Los Angeles")

    def test_clean_scraped_data(self):
        """Test data cleaning functionality."""
        downloader = RepeaterBookDownloader()

        # Create test DataFrame with issues to clean
        df = pd.DataFrame(
            {
                "Frequency": ["  146.520  ", "147.000"],
                "Call Sign": ["W6ABC", "  K6XYZ  "],
                "Tone": ["", "123.0"],
                "Location": ["Test  ", ""],
            }
        )

        cleaned = downloader._clean_scraped_data(df)

        # Check that columns are renamed
        assert "frequency" in cleaned.columns
        assert "callsign" in cleaned.columns

        # Check whitespace stripping
        assert cleaned["frequency"].iloc[0] == "146.520"
        assert cleaned["callsign"].iloc[1] == "K6XYZ"

        # Check empty string handling
        assert pd.isna(cleaned["tone"].iloc[0])
        assert pd.isna(cleaned["location"].iloc[1])


class TestConvenienceFunctions:
    """Test top-level convenience functions."""

    @patch("ham_formatter.downloader.RepeaterBookDownloader")
    def test_download_repeater_data_by_county(self, mock_downloader_class):
        """Test county download convenience function."""
        mock_downloader = Mock()
        mock_downloader.download_by_county.return_value = pd.DataFrame(
            {"test": [1, 2, 3]}
        )
        mock_downloader_class.return_value = mock_downloader

        result = download_repeater_data_by_county(
            "CA", "Los Angeles", "United States", 30
        )

        mock_downloader_class.assert_called_once_with(timeout=30)
        mock_downloader.download_by_county.assert_called_once_with(
            "CA", "Los Angeles", "United States", None
        )
        assert isinstance(result, pd.DataFrame)

    @patch("ham_formatter.downloader.RepeaterBookDownloader")
    def test_download_repeater_data_by_city(self, mock_downloader_class):
        """Test city download convenience function."""
        mock_downloader = Mock()
        mock_downloader.download_by_city.return_value = pd.DataFrame(
            {"test": [1, 2, 3]}
        )
        mock_downloader_class.return_value = mock_downloader

        result = download_repeater_data_by_city("TX", "Austin", "United States", 30)

        mock_downloader_class.assert_called_once_with(timeout=30)
        mock_downloader.download_by_city.assert_called_once_with(
            "TX", "Austin", "United States", None
        )
        assert isinstance(result, pd.DataFrame)

    @patch("ham_formatter.downloader.RepeaterBookDownloader")
    def test_original_download_function_still_works(self, mock_downloader_class):
        """Test that original download function is unchanged."""
        mock_downloader = Mock()
        mock_downloader.download_by_state.return_value = pd.DataFrame(
            {"test": [1, 2, 3]}
        )
        mock_downloader_class.return_value = mock_downloader

        result = download_repeater_data("CA", "United States", 30)

        mock_downloader_class.assert_called_once_with(timeout=30)
        mock_downloader.download_by_state.assert_called_once_with(
            "CA", "United States", None
        )
        assert isinstance(result, pd.DataFrame)

    def test_clean_scraped_data_splits_tone_up_down_column(self):
        """Test that 'Tone Up / Down' column is properly split into separate columns."""
        downloader = RepeaterBookDownloader()

        # Test data with various tone formats
        test_data = pd.DataFrame(
            {
                "Frequency": ["146.520", "147.000", "440.125", "146.640", "147.180"],
                "Tone Up / Down": [
                    "123.0 / 456.0",  # Slash with spaces
                    "67.0 88.5",  # Space separated
                    "100.0/200.0",  # Slash without spaces
                    "150.0",  # Single value
                    "",  # Empty
                ],
                "Call Sign": ["W1ABC", "K2DEF", "N3GHI", "K4JKL", "W5MNO"],
            }
        )

        result = downloader._clean_scraped_data(test_data)

        # Verify the tone columns were split correctly
        assert "tone_up" in result.columns
        assert "tone_down" in result.columns
        assert (
            "Tone Up / Down" not in result.columns
        )  # Original column should be removed

        # Check specific values
        assert result.iloc[0]["tone_up"] == "123.0"
        assert result.iloc[0]["tone_down"] == "456.0"

        assert result.iloc[1]["tone_up"] == "67.0"
        assert result.iloc[1]["tone_down"] == "88.5"

        assert result.iloc[2]["tone_up"] == "100.0"
        assert result.iloc[2]["tone_down"] == "200.0"

        assert result.iloc[3]["tone_up"] == "150.0"
        assert (
            result.iloc[3]["tone_down"] is None
        )  # Single value leaves tone_down empty

        assert result.iloc[4]["tone_up"] is None  # Empty string becomes None
        assert result.iloc[4]["tone_down"] is None

    def test_clean_scraped_data_handles_missing_tone_column(self):
        """Test that data without 'Tone Up / Down' column is processed normally."""
        downloader = RepeaterBookDownloader()

        # Test data without tone up/down column
        test_data = pd.DataFrame(
            {
                "Frequency": ["146.520", "147.000"],
                "Call Sign": ["W1ABC", "K2DEF"],
                "Location": ["City1", "City2"],
            }
        )

        result = downloader._clean_scraped_data(test_data)

        # Should not add tone columns if they weren't in the original data
        assert "tone_up" not in result.columns
        assert "tone_down" not in result.columns

        # Other columns should still be processed normally
        assert "frequency" in result.columns
        assert "callsign" in result.columns
        assert "location" in result.columns
