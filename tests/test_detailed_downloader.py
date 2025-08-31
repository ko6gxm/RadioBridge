"""Tests for radiobridge.detailed_downloader module."""

import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from radiobridge.detailed_downloader import (
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
        "radiobridge.detailed_downloader."
        "DetailedRepeaterDownloader._scrape_with_links"
    )
    @patch("radiobridge.band_filter.filter_by_frequency")
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
        "radiobridge.detailed_downloader."
        "DetailedRepeaterDownloader._scrape_with_links"
    )
    @patch("radiobridge.band_filter.filter_by_frequency")
    @patch(
        "radiobridge.detailed_downloader."
        "DetailedRepeaterDownloader._collect_detailed_data"
    )
    @patch("radiobridge.detailed_downloader.DetailedRepeaterDownloader._merge_data")
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
        """Test merging basic and detailed data into structured format."""
        basic_data = pd.DataFrame(
            {"frequency": [145.200, 146.940], "call": ["W6ABC", "K6XYZ"]}
        )

        detailed_data = {
            0: {"sponsor": "Club A", "grid_squares": ["DM13"]},
            1: {"sponsor": "Club B", "note": "Test note"},
        }

        downloader = DetailedRepeaterDownloader()
        result = downloader._merge_data(basic_data, detailed_data)

        assert len(result) == 2

        # Check that we have the structured columns
        expected_columns = [
            "Downlink",
            "Uplink",
            "Offset",
            "Uplink Tone",
            "Downlink Tone",
            "DMR",
            "Color Code",
            "DMR ID",
            "Call",
            "Sponsor",
            "Grid Square",
            "IRLP",
            "IRLP Node",
            "IRLP Status",
            "IRLP Last Activity",
            "IRLP Callsign",
            "IRLP Location",
            "Notes",
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

        # Check specific values
        assert result.loc[0, "Call"] == "W6ABC"
        assert result.loc[0, "Sponsor"] == "Club A"
        assert result.loc[0, "Grid Square"] == "DM13"
        assert result.loc[1, "Call"] == "K6XYZ"
        assert result.loc[1, "Sponsor"] == "Club B"

        # Check that the note appears in the Notes field
        assert "Note: Test note" in result.loc[1, "Notes"]

    def test_structured_output_with_filtered_indices(self):
        """Test that _create_structured_output handles filtered DataFrame indices correctly.

        This is a regression test for the "single positional indexer is out-of-bounds" error
        that occurred when band filtering removed some rows from the basic data.
        """
        # Create basic data with non-consecutive indices (simulating band filtering)
        basic_data = pd.DataFrame(
            {
                "frequency": [145.200, 146.940, 447.100],
                "call": ["W6ABC", "K6XYZ", "N6TEST"],
                "county": ["County A", "County B", "County C"],
                "use": ["OPEN", "OPEN", "CLUB"],
                "status": ["On Air", "On Air", "On Air"],
            }
        )
        # Simulate filtering by setting non-consecutive indices
        basic_data.index = [
            2,
            5,
            7,
        ]  # Non-consecutive indices like after band filtering

        # Detailed data that corresponds to the filtered indices
        detailed_data = {
            2: {
                "sponsor": "Club A",
                "grid_squares": ["DM13"],
                "downlink_freq": "145.200",
            },
            5: {"sponsor": "Club B", "note": "Test note", "uplink_freq": "146.340"},
            7: {"sponsor": "Club C", "dmr_color_code": "1", "is_dmr": "true"},
        }

        downloader = DetailedRepeaterDownloader()

        # This should NOT raise "single positional indexer is out-of-bounds" error
        result = downloader._create_structured_output(basic_data, detailed_data)

        # Verify the result has the expected structure
        assert len(result) == 3
        assert list(result.index) == [2, 5, 7]  # Preserves original indices

        # Check specific values to ensure data was mapped correctly
        assert result.loc[2, "Call"] == "W6ABC"
        assert result.loc[2, "Sponsor"] == "Club A"
        assert result.loc[2, "Grid Square"] == "DM13"
        assert result.loc[2, "Downlink"] == "145.200"

        assert result.loc[5, "Call"] == "K6XYZ"
        assert result.loc[5, "Sponsor"] == "Club B"
        assert result.loc[5, "Uplink"] == "146.340"
        assert "Note: Test note" in result.loc[5, "Notes"]

        assert result.loc[7, "Call"] == "N6TEST"
        assert result.loc[7, "Sponsor"] == "Club C"
        assert result.loc[7, "DMR"] == "true"
        assert result.loc[7, "Color Code"] == "1"


class TestDetailedDownloaderFunctions:
    """Test cases for module-level convenience functions."""

    @patch("radiobridge.detailed_downloader.DetailedRepeaterDownloader")
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

    @patch("radiobridge.detailed_downloader.DetailedRepeaterDownloader")
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

    @patch("radiobridge.detailed_downloader.DetailedRepeaterDownloader")
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


class TestIRLPFunctionality:
    """Test IRLP extraction and status fetching functionality."""

    def test_extract_irlp_info_minimal(self):
        """Test minimal IRLP information extraction with just node number."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock HTML with minimal IRLP information
        html_content = """
        <html><body>
        <p>Repeater Information:</p>
        <p>IRLP: 3341</p>
        </body></html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        result = downloader._extract_irlp_info(soup, "test_url")

        assert "irlp_node" in result
        assert result["irlp_node"] == "3341"
        # Status text should not be present for minimal case
        assert "irlp_status_text" not in result or result["irlp_status_text"] == ""

    def test_extract_irlp_info_with_status(self):
        """Test IRLP information extraction with status text."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock HTML with IRLP information including status
        html_content = """
        <html><body>
        <p>Repeater Information:</p>
        <p>IRLP: 3341 — IDLE for 0 days, 3 hours, 26 minutes, 46 seconds</p>
        <a href="https://status.irlp.net/index.php?PSTART=3341">IRLP Status</a>
        </body></html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        result = downloader._extract_irlp_info(soup, "test_url")

        assert "irlp_node" in result
        assert result["irlp_node"] == "3341"
        assert "irlp_status_text" in result
        assert (
            "IDLE for 0 days, 3 hours, 26 minutes, 46 seconds"
            in result["irlp_status_text"]
        )
        assert "irlp_url" in result
        assert "3341" in result["irlp_url"]

    def test_extract_irlp_info_no_irlp(self):
        """Test IRLP extraction when no IRLP info present."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader()

        html_content = """
        <html><body>
        <p>Repeater Information:</p>
        <p>No IRLP information here</p>
        </body></html>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        result = downloader._extract_irlp_info(soup, "test_url")

        assert result == {}  # Should return empty dict when no IRLP found

    def test_extract_irlp_various_formats(self):
        """Test IRLP extraction with various text formats."""
        from bs4 import BeautifulSoup

        downloader = DetailedRepeaterDownloader()

        test_cases = [
            ("IRLP: 1234", "1234", ""),
            ("irlp: 5678 (Online)", "5678", "(Online)"),
            ("IRLP: 9999 — CONNECTED to node 1000", "9999", "— CONNECTED to node 1000"),
            ("IRLP: 7777 Available", "7777", "Available"),
        ]

        for html_text, expected_node, expected_status in test_cases:
            html_content = f"<html><body><p>{html_text}</p></body></html>"
            soup = BeautifulSoup(html_content, "html.parser")
            result = downloader._extract_irlp_info(soup, "test_url")

            assert "irlp_node" in result
            assert result["irlp_node"] == expected_node
            if expected_status:
                assert "irlp_status_text" in result
                assert expected_status.strip() in result["irlp_status_text"]

    @patch("requests.Session.get")
    def test_scrape_irlp_status_idle(self, mock_get):
        """Test IRLP status scraping for idle node."""
        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock IRLP status page response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <h1>Node 3341 Status</h1>
        <p>Call: VE7ABC-R</p>
        <p>Status: IDLE for 2 days, 5 hours, 30 minutes</p>
        <p>Location: Vancouver, BC</p>
        <p>Last Activity: 2024-01-15 14:30:00</p>
        <p>Owner: VE7ABC</p>
        <p>Node Name: Vancouver Repeater</p>
        </body></html>
        """
        mock_get.return_value = mock_response

        result = downloader._scrape_irlp_status(
            "https://status.irlp.net/index.php?PSTART=3341", "3341"
        )

        assert "irlp_node_status" in result
        assert result["irlp_node_status"] == "IDLE"
        assert "irlp_status_detail" in result
        assert "2 days, 5 hours, 30 minutes" in result["irlp_status_detail"]
        assert "irlp_callsign" in result
        assert "VE7ABC" in result["irlp_callsign"]
        assert "irlp_location" in result
        assert "Vancouver, BC" in result["irlp_location"]
        assert "irlp_last_activity" in result
        assert "irlp_owner" in result
        assert "VE7ABC" in result["irlp_owner"]
        assert "irlp_node_name" in result
        assert "Vancouver Repeater" in result["irlp_node_name"]

    @patch("requests.Session.get")
    def test_scrape_irlp_status_connected(self, mock_get):
        """Test IRLP status scraping for connected node."""
        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock IRLP status page response for connected node
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"""
        <html><body>
        <h1>Node 1000 Status</h1>
        <p>Call: W6ABC-R</p>
        <p>Status: CONNECTED to reflector REF001C</p>
        <p>Node Location: Los Angeles, CA</p>
        <p>Last Connect: 2024-01-15 16:45:00</p>
        </body></html>
        """
        mock_get.return_value = mock_response

        result = downloader._scrape_irlp_status(
            "https://status.irlp.net/index.php?PSTART=1000", "1000"
        )

        assert "irlp_node_status" in result
        assert result["irlp_node_status"] == "CONNECTED"
        assert "irlp_status_detail" in result
        assert "reflector REF001C" in result["irlp_status_detail"]
        assert "irlp_callsign" in result
        assert "W6ABC" in result["irlp_callsign"]
        assert "irlp_location" in result
        assert "Los Angeles, CA" in result["irlp_location"]
        assert "irlp_last_activity" in result

    @patch("requests.Session.get")
    def test_scrape_irlp_status_error(self, mock_get):
        """Test IRLP status scraping when request fails."""
        downloader = DetailedRepeaterDownloader()

        # Mock failed request
        mock_get.side_effect = Exception("Connection failed")

        result = downloader._scrape_irlp_status(
            "https://status.irlp.net/index.php?PSTART=3341", "3341"
        )

        assert "irlp_node_status" in result
        assert result["irlp_node_status"] == "Error"
        assert "irlp_error" in result
        assert "Connection failed" in result["irlp_error"]

    @patch("requests.Session.get")
    def test_scrape_detail_page_with_irlp_integration(self, mock_get):
        """Test integration of IRLP extraction within _scrape_detail_page method."""
        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock the main detail page response
        detail_response = Mock()
        detail_response.raise_for_status.return_value = None
        detail_response.content = b"""
        <html><body>
        <h1>Repeater Details</h1>
        <p>Repeater ID: RB67890</p>
        <p>Frequency: 146.520 MHz</p>
        <p>IRLP: 2468 - IDLE for 1 day, 2 hours, 15 minutes</p>
        <a href="https://status.irlp.net/index.php?PSTART=2468">IRLP Status</a>
        <p>Location: Test City, WA</p>
        <p>Sponsor: Test Amateur Radio Club</p>
        </body></html>
        """

        # Mock the IRLP status page response
        irlp_response = Mock()
        irlp_response.raise_for_status.return_value = None
        irlp_response.content = b"""
        <html><body>
        <h1>Node 2468 Status</h1>
        <p>Call: K7TEST-R</p>
        <p>Status: IDLE for 1 day, 2 hours, 15 minutes</p>
        <p>Location: Test City, WA</p>
        <p>Last Activity: 2024-01-14 12:15:00</p>
        <p>Owner: K7TEST</p>
        </body></html>
        """

        # Configure mock to return appropriate responses
        def mock_get_side_effect(url, timeout=None):
            if "details.php" in url:
                return detail_response
            elif "status.irlp.net" in url:
                return irlp_response
            else:
                raise ValueError(f"Unexpected URL: {url}")

        mock_get.side_effect = mock_get_side_effect

        # Test the integration
        result = downloader._scrape_detail_page(
            "https://www.repeaterbook.com/repeaters/details.php?state_id=53&ID=67890"
        )

        # Verify basic detail data was extracted
        assert "repeater_id" in result
        assert result["repeater_id"] == "RB67890"

        # Verify IRLP data was extracted and merged
        assert "irlp_node" in result
        assert result["irlp_node"] == "2468"
        assert "irlp_status_text" in result
        assert "IDLE for 1 day, 2 hours, 15 minutes" in result["irlp_status_text"]
        assert "irlp_url" in result
        assert "status.irlp.net" in result["irlp_url"]

        # Verify IRLP status data was fetched and merged
        assert "irlp_node_status" in result
        assert result["irlp_node_status"] == "IDLE"
        assert "irlp_callsign" in result
        assert "K7TEST" in result["irlp_callsign"]
        assert "irlp_location" in result
        assert "Test City" in result["irlp_location"]
        assert "irlp_last_activity" in result
        assert "irlp_owner" in result
        assert "K7TEST" in result["irlp_owner"]

        # Verify both requests were made
        assert mock_get.call_count == 2

    def test_structured_output_with_irlp_data(self):
        """Test that IRLP data is properly included in structured output."""
        basic_data = pd.DataFrame(
            {
                "frequency": [145.200, 146.940],
                "call": ["W6ABC", "K6XYZ"],
                "location": ["City A", "City B"],
            }
        )

        detailed_data = {
            0: {
                "sponsor": "Club A",
                "irlp_node": "3341",
                "irlp_node_status": "IDLE",
                "irlp_last_activity": "2024-01-15 14:30:00",
                "irlp_callsign": "VE7ABC",
                "irlp_location": "Vancouver, BC",
            },
            1: {"sponsor": "Club B"},
        }

        downloader = DetailedRepeaterDownloader()
        result = downloader._merge_data(basic_data, detailed_data)

        assert len(result) == 2

        # Check that IRLP columns are present
        irlp_columns = [
            "IRLP",
            "IRLP Node",
            "IRLP Status",
            "IRLP Last Activity",
            "IRLP Callsign",
            "IRLP Location",
        ]
        for col in irlp_columns:
            assert col in result.columns, f"Missing IRLP column: {col}"

        # Check IRLP data mapping for first row
        assert result.loc[0, "IRLP"] == "3341"
        assert result.loc[0, "IRLP Node"] == "3341"  # Should be same as IRLP
        assert result.loc[0, "IRLP Status"] == "IDLE"
        assert result.loc[0, "IRLP Last Activity"] == "2024-01-15 14:30:00"
        assert result.loc[0, "IRLP Callsign"] == "VE7ABC"
        assert result.loc[0, "IRLP Location"] == "Vancouver, BC"

        # Check that second row has empty IRLP data
        assert result.loc[1, "IRLP"] == ""
        assert result.loc[1, "IRLP Node"] == ""
        assert result.loc[1, "IRLP Status"] == ""
        assert result.loc[1, "IRLP Last Activity"] == ""
        assert result.loc[1, "IRLP Callsign"] == ""
        assert result.loc[1, "IRLP Location"] == ""

        # Verify IRLP data is excluded from Notes field to prevent duplication
        notes = result.loc[0, "Notes"]
        irlp_keys = [
            "irlp_node",
            "irlp_node_status",
            "irlp_last_activity",
            "irlp_callsign",
            "irlp_location",
        ]
        for key in irlp_keys:
            assert (
                key.title().replace("_", " ") not in notes
            ), f"IRLP key {key} should not appear in Notes field"


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

    @patch("requests.Session.get")
    def test_scrape_detail_page_with_echolink_integration(self, mock_get):
        """Test integration of EchoLink extraction within _scrape_detail_page method."""
        downloader = DetailedRepeaterDownloader(debug=True)

        # Mock the main detail page response
        detail_response = Mock()
        detail_response.raise_for_status.return_value = None
        detail_response.content = b"""
        <html><body>
        <h1>Repeater Details</h1>
        <p>Repeater ID: RB12345</p>
        <p>Frequency: 145.200 MHz</p>
        <p>EchoLink: 67890 (Online)</p>
        <a href="https://www.echolink.org/logins.jsp?call=67890">EchoLink Status</a>
        <p>Location: Test City, CA</p>
        <p>Sponsor: Test Radio Club</p>
        </body></html>
        """

        # Mock the EchoLink status page response
        echolink_response = Mock()
        echolink_response.raise_for_status.return_value = None
        echolink_response.content = b"""
        <html><body>
        <h1>K6TEST-R Node 67890</h1>
        <p>Status: Online</p>
        <p>Location: Test City, CA</p>
        <p>Last Activity: 2024-01-15 14:30:00</p>
        </body></html>
        """

        # Configure mock to return appropriate responses
        def mock_get_side_effect(url, timeout=None):
            if "details.php" in url:
                return detail_response
            elif "echolink.org" in url:
                return echolink_response
            else:
                raise ValueError(f"Unexpected URL: {url}")

        mock_get.side_effect = mock_get_side_effect

        # Test the integration
        result = downloader._scrape_detail_page(
            "https://www.repeaterbook.com/repeaters/details.php?state_id=06&ID=12345"
        )

        # Verify basic detail data was extracted
        assert "repeater_id" in result
        assert result["repeater_id"] == "RB12345"

        # Verify EchoLink data was extracted and merged
        assert "echolink_node" in result
        assert result["echolink_node"] == "67890"
        assert "echolink_status_text" in result
        assert "Online" in result["echolink_status_text"]
        assert "echolink_url" in result
        assert "echolink.org" in result["echolink_url"]

        # Verify EchoLink status data was fetched and merged
        assert "echolink_node_status" in result
        assert result["echolink_node_status"] == "Online"
        assert "echolink_callsign" in result
        assert "K6TEST" in result["echolink_callsign"]
        assert "echolink_location" in result
        assert "Test City" in result["echolink_location"]
        assert "echolink_last_activity" in result

        # Verify both requests were made
        assert mock_get.call_count == 2


class TestDMRDetectionImprovements:
    """Test cases for improved DMR detection logic."""

    def test_dmr_detection_color_code_only(self):
        """Test DMR detection with color code but no numeric DMR ID (like WD6AML)."""
        downloader = DetailedRepeaterDownloader(debug=False)

        text = """
        Cactus City, CA WD6AML Repeater ID: 06-16210
        Downlink: 446.06250 Uplink: 441.06250 Offset: -5.000 MHz
        DMR Color Code: 2 DMR ID: DMR ID Needed
        DMR Network: Western States DMR County: Riverside Call: WD6AML
        """

        detail_data = {}
        downloader._extract_dmr_data(text, detail_data)

        assert detail_data["is_dmr"] == "true"
        assert detail_data["dmr_color_code"] == "2"
        assert "dmr_id" not in detail_data  # Should not extract non-numeric ID

    def test_dmr_detection_full_data(self):
        """Test DMR detection with both color code and numeric DMR ID (like K6TMD)."""
        downloader = DetailedRepeaterDownloader(debug=False)

        text = """
        Pine Cove, CA K6TMD Repeater ID: 06-16060
        Downlink: 446.06250 Uplink: 441.06250 Offset: -5.000 MHz
        DMR Color Code: 1 DMR ID: 310724 IPSC Network: Western States
        DMR – Color Code: 1 – TS Linked: TS1 TS2 – Trustee: WA6PYJ
        DMR Network: Western States DMR County: Riverside Call: K6TMD
        """

        detail_data = {}
        downloader._extract_dmr_data(text, detail_data)

        assert detail_data["is_dmr"] == "true"
        assert detail_data["dmr_color_code"] == "1"
        assert detail_data["dmr_id"] == "310724"

    def test_dmr_detection_non_dmr_repeater(self):
        """Test DMR detection for non-DMR repeaters."""
        downloader = DetailedRepeaterDownloader(debug=False)

        text = """
        Downlink: 146.52000 Uplink: 146.52000 Offset: 0.000 MHz
        County: Los Angeles Call: N6ABC Use: OPEN
        Analog FM repeater with no DMR capabilities
        """

        detail_data = {}
        downloader._extract_dmr_data(text, detail_data)

        assert detail_data["is_dmr"] == "false"
        assert "dmr_color_code" not in detail_data
        assert "dmr_id" not in detail_data

    def test_dmr_detection_brandmeister_network(self):
        """Test DMR detection with Brandmeister network indicators."""
        downloader = DetailedRepeaterDownloader(debug=False)

        text = """
        Downlink: 441.12500 Uplink: 446.12500 Offset: +5.000 MHz
        Color Code: 7 Brandmeister DMR Network County: Orange
        Network: BrandMeister United States
        """

        detail_data = {}
        downloader._extract_dmr_data(text, detail_data)

        assert detail_data["is_dmr"] == "true"
        assert detail_data["dmr_color_code"] == "7"

    def test_dmr_detection_various_indicators(self):
        """Test DMR detection with various DMR network indicators."""
        downloader = DetailedRepeaterDownloader(debug=False)

        test_cases = [
            ("Western States DMR network", True),
            ("IPSC Network: Some Network", True),
            ("DMR-Marc network", True),
            ("Regular analog repeater", False),
            ("DMR Network: Test", True),
        ]

        for text, expected_dmr in test_cases:
            detail_data = {}
            downloader._extract_dmr_data(text, detail_data)

            expected_result = "true" if expected_dmr else "false"
            assert detail_data["is_dmr"] == expected_result, f"Failed for text: {text}"

    def test_dmr_id_patterns(self):
        """Test various DMR ID patterns."""
        downloader = DetailedRepeaterDownloader(debug=False)

        test_cases = [
            ("DMR ID: 310724", "310724"),  # Standard format
            ("DMR ID 123456", "123456"),  # No colon
            ("DMRID: 789012", "789012"),  # Alternative format
            ("DMR ID: DMR ID Needed", None),  # Non-numeric
            ("No DMR ID here", None),  # No DMR ID
        ]

        for text, expected_id in test_cases:
            detail_data = {}
            downloader._extract_dmr_data(text, detail_data)

            if expected_id:
                assert "dmr_id" in detail_data
                assert detail_data["dmr_id"] == expected_id
            else:
                assert "dmr_id" not in detail_data

    def test_color_code_patterns(self):
        """Test various color code patterns."""
        downloader = DetailedRepeaterDownloader(debug=False)

        test_cases = [
            ("DMR Color Code: 2", "2"),
            ("Color Code: 7", "7"),
            ("DMR Color Code: 15", "15"),
            ("Color Code: 1", "1"),
        ]

        for text, expected_code in test_cases:
            detail_data = {}
            downloader._extract_dmr_data(text, detail_data)

            assert "dmr_color_code" in detail_data
            assert detail_data["dmr_color_code"] == expected_code
            assert detail_data["is_dmr"] == "true"  # Should detect DMR with color code
