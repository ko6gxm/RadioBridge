"""Tests for ham_formatter.detailed_downloader module."""

import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from ham_formatter.detailed_downloader import (
    DetailedRepeaterDownloader,
    download_with_details,
    download_with_details_by_county,
    download_with_details_by_city,
)


class TestDetailedRepeaterDownloader:
    """Test cases for DetailedRepeaterDownloader class."""

    def test_init(self):
        """Test downloader initialization."""
        downloader = DetailedRepeaterDownloader(
            timeout=60, rate_limit=2.0, temp_dir="/tmp"
        )
        assert downloader.timeout == 60
        assert downloader.rate_limit == 2.0
        assert downloader.temp_dir == Path("/tmp")
        assert hasattr(downloader, "logger")
        assert downloader.last_request_time == 0

    def test_init_default_values(self):
        """Test downloader initialization with default values."""
        downloader = DetailedRepeaterDownloader()
        assert downloader.timeout == 30
        assert downloader.rate_limit == 1.0
        assert downloader.temp_dir is None

    def test_apply_rate_limit(self):
        """Test rate limiting functionality."""
        downloader = DetailedRepeaterDownloader(rate_limit=0.1)

        # Should not sleep on first call
        import time

        start_time = time.time()
        downloader._apply_rate_limit()
        first_call_time = time.time() - start_time
        assert first_call_time < 0.05  # Should be immediate

        # Should sleep on second rapid call
        start_time = time.time()
        downloader._apply_rate_limit()
        second_call_time = time.time() - start_time
        assert second_call_time >= 0.1  # Should have slept

    @patch(
        "ham_formatter.detailed_downloader."
        "DetailedRepeaterDownloader._scrape_with_links"
    )
    @patch("ham_formatter.band_filter.filter_by_frequency")
    def test_download_with_details_no_data(self, mock_filter, mock_scrape):
        """Test detailed download when no basic data is found."""
        # Setup mocks
        empty_df = pd.DataFrame()
        mock_scrape.return_value = (empty_df, [])
        mock_filter.return_value = empty_df

        downloader = DetailedRepeaterDownloader()

        result = downloader.download_with_details("state", state="CA", bands=["all"])

        assert result.empty
        mock_scrape.assert_called_once()
        mock_filter.assert_called_once()

    @patch(
        "ham_formatter.detailed_downloader."
        "DetailedRepeaterDownloader._scrape_with_links"
    )
    @patch("ham_formatter.band_filter.filter_by_frequency")
    @patch(
        "ham_formatter.detailed_downloader."
        "DetailedRepeaterDownloader._collect_detailed_data"
    )
    @patch("ham_formatter.detailed_downloader.DetailedRepeaterDownloader._merge_data")
    def test_download_with_details_success(
        self, mock_merge, mock_collect, mock_filter, mock_scrape
    ):
        """Test successful detailed download."""
        # Setup test data
        basic_data = pd.DataFrame(
            {
                "frequency": [145.200, 146.940],
                "call": ["W6ABC", "K6XYZ"],
                "location": ["City A", "City B"],
            }
        )
        detail_links = [
            {"detail_url": "http://example.com/1", "row_index": 0},
            {"detail_url": "http://example.com/2", "row_index": 1},
        ]
        detailed_data = {
            0: {"sponsor": "Club A", "grid_square": "DM13"},
            1: {"sponsor": "Club B", "grid_square": "DM14"},
        }
        enhanced_data = basic_data.copy()
        enhanced_data["detail_sponsor"] = ["Club A", "Club B"]
        enhanced_data["detail_grid_square"] = ["DM13", "DM14"]

        # Setup mocks
        mock_scrape.return_value = (basic_data, detail_links)
        mock_filter.return_value = basic_data
        mock_collect.return_value = detailed_data
        mock_merge.return_value = enhanced_data

        downloader = DetailedRepeaterDownloader()

        result = downloader.download_with_details("state", state="CA", bands=["all"])

        assert len(result) == 2
        assert "detail_sponsor" in result.columns
        assert "detail_grid_square" in result.columns
        mock_scrape.assert_called_once()
        mock_filter.assert_called_once()
        mock_collect.assert_called_once()
        mock_merge.assert_called_once()

    def test_extract_links_from_table(self):
        """Test extracting links from HTML table."""
        from bs4 import BeautifulSoup

        html = """
        <table>
            <tr><th>Frequency</th><th>Call</th></tr>
            <tr>
                <td><a href="details.php?state_id=06&ID=123">145.200</a></td>
                <td>W6ABC</td>
            </tr>
            <tr>
                <td><a href="details.php?state_id=06&ID=456">146.940</a></td>
                <td>K6XYZ</td>
            </tr>
        </table>
        """

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")

        df = pd.DataFrame({"frequency": [145.200, 146.940], "call": ["W6ABC", "K6XYZ"]})

        downloader = DetailedRepeaterDownloader()
        downloader.BASE_URL = "https://www.repeaterbook.com"

        links = downloader._extract_links_from_table(table, df)

        assert len(links) == 2
        assert links[0]["detail_url"].endswith("details.php?state_id=06&ID=123")
        assert links[0]["row_index"] == 0
        assert links[0]["frequency"] == 145.200
        assert links[0]["callsign"] == "W6ABC"

        assert links[1]["detail_url"].endswith("details.php?state_id=06&ID=456")
        assert links[1]["row_index"] == 1
        assert links[1]["frequency"] == 146.940
        assert links[1]["callsign"] == "K6XYZ"

    def test_merge_data(self):
        """Test merging basic and detailed data."""
        basic_data = pd.DataFrame(
            {"frequency": [145.200, 146.940], "call": ["W6ABC", "K6XYZ"]}
        )

        detailed_data = {
            0: {"sponsor": "Club A", "grid_square": "DM13"},
            1: {"sponsor": "Club B", "note": "Test note"},
        }

        downloader = DetailedRepeaterDownloader()
        result = downloader._merge_data(basic_data, detailed_data)

        assert len(result) == 2
        assert "detail_sponsor" in result.columns
        assert "detail_grid_square" in result.columns
        assert "detail_note" in result.columns

        # Check row 0
        assert result.loc[0, "detail_sponsor"] == "Club A"
        assert result.loc[0, "detail_grid_square"] == "DM13"
        assert (
            pd.isna(result.loc[0, "detail_note"])
            or result.loc[0, "detail_note"] is None
        )

        # Check row 1
        assert result.loc[1, "detail_sponsor"] == "Club B"
        assert (
            pd.isna(result.loc[1, "detail_grid_square"])
            or result.loc[1, "detail_grid_square"] is None
        )
        assert result.loc[1, "detail_note"] == "Test note"


class TestDetailedDownloaderFunctions:
    """Test cases for module-level convenience functions."""

    @patch("ham_formatter.detailed_downloader.DetailedRepeaterDownloader")
    def test_download_with_details(self, mock_downloader_class):
        """Test download_with_details convenience function."""
        # Setup mock
        mock_downloader = Mock()
        mock_result = pd.DataFrame({"frequency": [145.200]})
        mock_downloader.download_with_details.return_value = mock_result
        mock_downloader_class.return_value = mock_downloader

        result = download_with_details("CA", "United States", ["2m"], 2.0, Path("/tmp"))

        # Verify downloader was created correctly
        mock_downloader_class.assert_called_once_with(
            rate_limit=2.0, temp_dir=Path("/tmp"), nohammer=False, debug=False
        )

        # Verify download was called correctly
        mock_downloader.download_with_details.assert_called_once_with(
            level="state", state="CA", country="United States", bands=["2m"]
        )

        assert result is mock_result

    @patch("ham_formatter.detailed_downloader.DetailedRepeaterDownloader")
    def test_download_with_details_by_county(self, mock_downloader_class):
        """Test download_with_details_by_county convenience function."""
        # Setup mock
        mock_downloader = Mock()
        mock_result = pd.DataFrame({"frequency": [145.200]})
        mock_downloader.download_with_details.return_value = mock_result
        mock_downloader_class.return_value = mock_downloader

        result = download_with_details_by_county("CA", "Riverside", bands=["2m"])

        # Verify downloader was created with defaults
        mock_downloader_class.assert_called_once_with(
            rate_limit=1.0, temp_dir=None, nohammer=False, debug=False
        )

        # Verify download was called correctly
        mock_downloader.download_with_details.assert_called_once_with(
            level="county",
            state="CA",
            county="Riverside",
            country="United States",
            bands=["2m"],
        )

        assert result is mock_result

    @patch("ham_formatter.detailed_downloader.DetailedRepeaterDownloader")
    def test_download_with_details_by_city(self, mock_downloader_class):
        """Test download_with_details_by_city convenience function."""
        # Setup mock
        mock_downloader = Mock()
        mock_result = pd.DataFrame({"frequency": [145.200]})
        mock_downloader.download_with_details.return_value = mock_result
        mock_downloader_class.return_value = mock_downloader

        result = download_with_details_by_city("TX", "Austin")

        # Verify downloader was created with defaults
        mock_downloader_class.assert_called_once_with(
            rate_limit=1.0, temp_dir=None, nohammer=False, debug=False
        )

        # Verify download was called correctly
        mock_downloader.download_with_details.assert_called_once_with(
            level="city",
            state="TX",
            city="Austin",
            country="United States",
            bands=["all"],
        )

        assert result is mock_result


class TestEchoLinkFunctionality:
    """Test EchoLink extraction and status fetching functionality."""

    def test_extract_echolink_info_basic(self):
        """Test basic EchoLink information extraction."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock HTML with EchoLink information
        html_content = """
        <html><body>
        <p>Repeater Information:</p>
        <p>EchoLink: 12345 (Online)</p>
        <a href="https://www.echolink.org/logins.jsp?call=12345">EchoLink Status</a>
        </body></html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        result = downloader._extract_echolink_info(soup, "test_url")

        assert "echolink_node" in result
        assert result["echolink_node"] == "12345"
        assert "echolink_status_text" in result
        assert "Online" in result["echolink_status_text"]

    def test_extract_echolink_info_no_echolink(self):
        """Test EchoLink extraction when no EchoLink info present."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader()

        html_content = """
        <html><body>
        <p>Repeater Information:</p>
        <p>No EchoLink information here</p>
        </body></html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        result = downloader._extract_echolink_info(soup, "test_url")

        assert result == {}  # Should return empty dict when no EchoLink found

    @patch("requests.Session.get")
    def test_scrape_echolink_status_online(self, mock_get):
        """Test EchoLink status scraping for online node."""
        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock EchoLink status page response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <h1>W6ABC-R Node 12345</h1>
        <p>Status: Online</p>
        <p>Location: Los Angeles, CA</p>
        <p>Last Activity: 2024-01-15 10:30:00</p>
        </body></html>
        """
        mock_get.return_value = mock_response

        result = downloader._scrape_echolink_status(
            "https://www.echolink.org/logins.jsp?call=12345", "12345"
        )

        assert "echolink_node_status" in result
        assert result["echolink_node_status"] == "Online"
        assert "echolink_callsign" in result
        assert "W6ABC" in result["echolink_callsign"]
        assert "echolink_location" in result
        assert "Los Angeles" in result["echolink_location"]
        assert "echolink_last_activity" in result

    @patch("requests.Session.get")
    def test_scrape_echolink_status_error(self, mock_get):
        """Test EchoLink status scraping when request fails."""
        downloader = DetailedRepeaterDownloader()

        # Mock failed request
        mock_get.side_effect = Exception("Connection failed")

        result = downloader._scrape_echolink_status(
            "https://www.echolink.org/logins.jsp?call=12345", "12345"
        )

        assert "echolink_node_status" in result
        assert result["echolink_node_status"] == "Error"
        assert "echolink_error" in result
        assert "Connection failed" in result["echolink_error"]

    def test_extract_echolink_various_formats(self):
        """Test EchoLink extraction with various text formats."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader()

        test_cases = [
            ("EchoLink: 123456", "123456", ""),
            ("echolink: 78901 (Offline)", "78901", "(Offline)"),
            ("ECHOLINK: 555123 Available", "555123", "Available"),
        ]

        for html_text, expected_node, expected_status in test_cases:
            html_content = f"<html><body><p>{html_text}</p></body></html>"
            soup = BeautifulSoup(html_content, "html.parser")
            result = downloader._extract_echolink_info(soup, "test_url")

            assert "echolink_node" in result
            assert result["echolink_node"] == expected_node
            assert "echolink_status_text" in result
            assert expected_status in result["echolink_status_text"]
