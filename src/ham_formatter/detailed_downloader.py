"""Enhanced downloader with detailed repeater data collection.

This module extends the basic downloader to collect detailed information
from individual repeater pages using temporary files for intermediate storage.
"""

import json
import re
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from ham_formatter.downloader import RepeaterBookDownloader
from ham_formatter.logging_config import get_logger


class DetailedRepeaterDownloader(RepeaterBookDownloader):
    """Enhanced downloader that collects detailed repeater information."""

    def __init__(
        self,
        timeout: int = 30,
        rate_limit: float = 1.0,
        temp_dir: Optional[str] = None,
        nohammer: bool = False,
        debug: bool = False,
    ):
        """Initialize the detailed downloader.

        Args:
            timeout: Request timeout in seconds
            rate_limit: Minimum seconds between requests to avoid overloading the server
            temp_dir: Directory for temporary files (uses system temp if None)
            nohammer: If True, use random delays (1-10s) for each request
                instead of fixed rate_limit
            debug: If True, enable debug logging to show collected data from
                each detail page
        """
        super().__init__(timeout)
        self.rate_limit = rate_limit
        self.temp_dir = Path(temp_dir) if temp_dir else None
        self.nohammer = nohammer
        self.debug = debug
        self.logger = get_logger(__name__)
        self.last_request_time = 0

    def download_with_details(self, level: str, **kwargs) -> pd.DataFrame:
        """Download repeater data including detailed information from individual pages.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level including 'bands'

        Returns:
            DataFrame containing basic + detailed repeater information
        """
        self.logger.info("Starting detailed data collection")

        # Set flag to use enhanced scraping
        self._collecting_details = True

        try:
            # Get basic data and links in one pass
            bands = kwargs.get("bands") or ["all"]
            params = self._build_params(level, **kwargs)

            # Skip CSV export for detailed collection (we need the HTML)
            self.logger.info("Collecting basic data with detail links...")
            basic_data, detail_links = self._scrape_with_links(params)

            # Apply band filtering to basic data
            from ham_formatter.band_filter import filter_by_frequency

            basic_data = filter_by_frequency(basic_data, bands)

            if basic_data.empty:
                self.logger.warning("No basic data found after filtering")
                return basic_data

            self.logger.info(f"Collected {len(basic_data)} basic repeater records")
            self.logger.info(f"Found {len(detail_links)} detail page links to process")

            # Create temporary directory for this download session
            with tempfile.TemporaryDirectory(
                dir=self.temp_dir, prefix="ham_formatter_"
            ) as temp_session_dir:
                session_dir = Path(temp_session_dir)
                self.logger.debug(f"Using temporary directory: {session_dir}")

                # Save basic data
                basic_file = session_dir / "basic_data.csv"
                basic_data.to_csv(basic_file, index=False)
                self.logger.debug(f"Saved basic data to {basic_file}")

                # Collect detailed data with progress tracking
                detailed_data = self._collect_detailed_data(detail_links, session_dir)

                # Merge basic and detailed data
                enhanced_data = self._merge_data(basic_data, detailed_data)

                self.logger.info(
                    f"Enhanced dataset ready with {len(enhanced_data)} records"
                )
                return enhanced_data

        finally:
            # Clean up flag
            self._collecting_details = False

    def _extract_detail_links_from_data(
        self, basic_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Extract detail page URLs from basic data.

        This re-scrapes the original table to get the links since pandas loses the HTML.

        Args:
            basic_data: DataFrame with basic repeater data

        Returns:
            List of dictionaries containing detail URLs and identifying info
        """
        # We need to re-scrape the original page to get the links
        # This is a limitation of using pandas read_html - it strips the HTML

        # Build the search params from the basic data (reverse engineering)
        # For now, we'll implement a simpler approach by reconstructing URLs
        # from available data

        detail_links = []

        # We know the detail URL pattern: details.php?state_id=XX&ID=YYYY
        # We can try to match frequencies to get the IDs, but this requires
        # re-scraping the original page with BeautifulSoup

        self.logger.warning("Link extraction from DataFrame not fully implemented yet")
        self.logger.warning("Need to re-scrape original page to preserve HTML links")

        return detail_links

    def _scrape_with_links(
        self, params: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Scrape the main table while preserving detail page links.

        Args:
            params: Query parameters for the search

        Returns:
            Tuple of (DataFrame with basic data, list of detail links)
        """
        search_url = f"{self.BASE_URL}/repeaters/location_search.php"
        self.logger.debug(
            f"Scraping with links from {search_url} with params: {params}"
        )

        # Rate limiting
        self._apply_rate_limit()

        try:
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            self.logger.debug(
                f"HTML response: {response.status_code} ({len(response.content)} bytes)"
            )

        except Exception as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise

        # Parse HTML with BeautifulSoup to extract both data and links
        soup = BeautifulSoup(response.content, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            raise ValueError("No tables found in response")

        # Find the main repeater table
        main_table = max(tables, key=lambda t: len(t.find_all("tr")))

        # Extract data using pandas (same as before)
        from io import StringIO

        dfs = pd.read_html(StringIO(str(main_table)))
        if not dfs:
            raise ValueError("No data found in HTML table")

        df = dfs[0]
        df = self._clean_scraped_data(df)

        # Extract detail links from the same table
        detail_links = self._extract_links_from_table(main_table, df)

        return df, detail_links

    def _extract_links_from_table(
        self, table, df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Extract detail page links from HTML table.

        Args:
            table: BeautifulSoup table element
            df: Corresponding DataFrame with cleaned data

        Returns:
            List of detail link information
        """
        detail_links = []
        rows = table.find_all("tr")

        # Skip header row
        for i, row in enumerate(rows[1:], 1):  # Start from 1 to match DataFrame index
            cells = row.find_all(["td", "th"])

            if len(cells) == 0:
                continue

            # Look for links in the frequency column (typically first column)
            frequency_cell = cells[0] if cells else None
            if frequency_cell:
                links = frequency_cell.find_all("a")
                for link in links:
                    href = link.get("href")
                    if href and "details.php" in href:
                        # Extract parameters from URL
                        detail_url = urljoin(self.BASE_URL + "/repeaters/", href)

                        # Try to match this row to the DataFrame
                        row_index = i - 1  # Adjust for 0-based DataFrame index
                        if row_index < len(df):
                            detail_links.append(
                                {
                                    "detail_url": detail_url,
                                    "row_index": row_index,
                                    "frequency": df.iloc[row_index].get(
                                        "frequency", ""
                                    ),
                                    "callsign": df.iloc[row_index].get("call", ""),
                                    "location": df.iloc[row_index].get("location", ""),
                                }
                            )

        self.logger.debug(f"Extracted {len(detail_links)} detail links")
        return detail_links

    def _collect_detailed_data(
        self, detail_links: List[Dict[str, Any]], session_dir: Path
    ) -> Dict[int, Dict[str, Any]]:
        """Collect detailed data from individual repeater pages.

        Args:
            detail_links: List of detail page information
            session_dir: Temporary directory for storing intermediate results

        Returns:
            Dictionary mapping row indices to detailed data
        """
        detailed_data = {}
        failed_urls = []

        # Create subdirectory for detailed data
        details_dir = session_dir / "details"
        details_dir.mkdir(exist_ok=True)

        total_links = len(detail_links)
        self.logger.info(f"Processing {total_links} detail pages")

        for i, link_info in enumerate(detail_links, 1):
            detail_url = link_info["detail_url"]
            row_index = link_info["row_index"]

            self.logger.debug(f"Processing {i}/{total_links}: {detail_url}")

            try:
                # Rate limiting
                self._apply_rate_limit()

                # Fetch and parse detail page
                detail_data = self._scrape_detail_page(detail_url)

                if detail_data:
                    detailed_data[row_index] = detail_data

                    # Save individual result to temp file
                    detail_file = details_dir / f"detail_{row_index}.json"
                    with open(detail_file, "w") as f:
                        json.dump(detail_data, f, indent=2)

                    self.logger.debug(f"Saved detail data for row {row_index}")
                else:
                    self.logger.warning(f"No detail data extracted from {detail_url}")

            except Exception as e:
                self.logger.error(f"Failed to process detail page {detail_url}: {e}")
                failed_urls.append(detail_url)

            # Progress reporting every 10 items
            if i % 10 == 0:
                self.logger.info(f"Progress: {i}/{total_links} detail pages processed")

        if failed_urls:
            self.logger.warning(f"Failed to process {len(failed_urls)} detail pages")

        self.logger.info(f"Collected detailed data for {len(detailed_data)} repeaters")
        return detailed_data

    def _scrape_detail_page(self, detail_url: str) -> Dict[str, Any]:
        """Scrape data from an individual repeater detail page.

        Args:
            detail_url: URL of the detail page

        Returns:
            Dictionary with detailed repeater information
        """
        try:
            response = self.session.get(detail_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()

            detail_data = {}

            # Extract repeater ID
            id_match = re.search(r"Repeater ID:\s*(\S+)", text)
            if id_match:
                detail_data["repeater_id"] = id_match.group(1)

            # Extract specific frequency information with targeted patterns
            self._extract_frequency_data(text, detail_data)

            # Extract DMR-specific information
            self._extract_dmr_data(text, detail_data)

            # Extract talkgroup information for DMR repeaters
            self._extract_talkgroup_data(text, detail_data)

            # Extract key-value pairs from text for other information
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if ":" in line and len(line) < 200:  # Filter reasonable length lines
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()

                        # Clean up and standardize key names
                        key_clean = key.lower().replace(" ", "_").replace("-", "_")

                        # Only store non-empty values and skip generic keys
                        if value and key_clean not in ["", "call", "date", "details"]:
                            detail_data[key_clean] = value

            # Extract EchoLink information from HTML
            echolink_data = self._extract_echolink_info(soup, detail_url)
            if echolink_data:
                detail_data.update(echolink_data)

            # Extract grid squares
            grid_matches = re.findall(r"[A-Z]{2}\d{2}[a-z]{2}", text)
            if grid_matches:
                detail_data["grid_squares"] = grid_matches

            # Debug logging: show collected data if debug mode is enabled
            if self.debug and detail_data:
                self.logger.debug(f"Detail page data collected from {detail_url}:")
                for key, value in detail_data.items():
                    self.logger.debug(f"  {key}: {value}")
            elif self.debug:
                self.logger.debug(f"No detail data extracted from {detail_url}")

            return detail_data

        except Exception as e:
            self.logger.error(f"Error scraping detail page {detail_url}: {e}")
            return {}

    def _merge_data(
        self, basic_data: pd.DataFrame, detailed_data: Dict[int, Dict[str, Any]]
    ) -> pd.DataFrame:
        """Merge basic and detailed data into enhanced dataset.

        Args:
            basic_data: DataFrame with basic repeater information
            detailed_data: Dictionary mapping row indices to detailed data

        Returns:
            Enhanced DataFrame with merged data
        """
        enhanced_data = basic_data.copy()

        # Add columns for detailed data fields
        detail_columns = set()
        for row_data in detailed_data.values():
            detail_columns.update(row_data.keys())

        # Initialize new columns
        for col in detail_columns:
            enhanced_data[f"detail_{col}"] = None

        # Merge detailed data
        for row_index, row_detail in detailed_data.items():
            if row_index < len(enhanced_data):
                for key, value in row_detail.items():
                    enhanced_data.loc[row_index, f"detail_{key}"] = str(value)

        self.logger.info(f"Added {len(detail_columns)} detailed data columns")
        return enhanced_data

    def _apply_rate_limit(self):
        """Apply rate limiting to avoid overloading the server."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if self.nohammer:
            # In nohammer mode, use a random delay between 1-10 seconds for each request
            import random

            sleep_time = random.uniform(1.0, 10.0)
            self.logger.debug(
                f"No-hammer mode: sleeping {sleep_time:.2f} seconds (random)"
            )
            time.sleep(sleep_time)
        else:
            # Use fixed rate limiting
            if time_since_last < self.rate_limit:
                sleep_time = self.rate_limit - time_since_last
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _extract_echolink_info(
        self, soup: BeautifulSoup, detail_url: str
    ) -> Dict[str, Any]:
        """Extract EchoLink information from repeater detail page.

        Args:
            soup: BeautifulSoup object of the detail page
            detail_url: URL of the detail page for logging

        Returns:
            Dictionary with EchoLink data including node status
        """
        echolink_data = {}

        try:
            # Look for EchoLink in the HTML content
            text = soup.get_text()

            # Search for EchoLink pattern in text
            echolink_match = re.search(
                r"EchoLink:\s*(\d+)([^\n]*)", text, re.IGNORECASE
            )
            if echolink_match:
                node_number = echolink_match.group(1)
                status_text = echolink_match.group(2).strip()

                echolink_data["echolink_node"] = node_number
                echolink_data["echolink_status_text"] = status_text

                # Look for EchoLink links in HTML
                echolink_links = soup.find_all(
                    "a", href=re.compile(r"echolink", re.IGNORECASE)
                )

                for link in echolink_links:
                    href = link.get("href")
                    if href and node_number in href:
                        # Found EchoLink status link
                        echolink_url = (
                            href
                            if href.startswith("http")
                            else urljoin("https://www.echolink.org/", href)
                        )
                        echolink_data["echolink_url"] = echolink_url

                        # Fetch EchoLink node status
                        node_status = self._scrape_echolink_status(
                            echolink_url, node_number
                        )
                        if node_status:
                            echolink_data.update(node_status)
                        break

                if self.debug:
                    self.logger.debug(
                        f"EchoLink found for {detail_url}: Node {node_number}"
                    )
                    if "echolink_url" in echolink_data:
                        self.logger.debug(f"  Link: {echolink_data['echolink_url']}")
                    if "echolink_node_status" in echolink_data:
                        self.logger.debug(
                            f"  Status: {echolink_data['echolink_node_status']}"
                        )

        except Exception as e:
            self.logger.debug(f"Error extracting EchoLink info from {detail_url}: {e}")

        return echolink_data

    def _scrape_echolink_status(
        self, echolink_url: str, node_number: str
    ) -> Dict[str, Any]:
        """Scrape EchoLink node status from EchoLink website.

        Args:
            echolink_url: URL to the EchoLink node status page
            node_number: EchoLink node number for validation

        Returns:
            Dictionary with EchoLink node status information
        """
        status_data = {}

        try:
            # Apply rate limiting for external requests
            self._apply_rate_limit()

            self.logger.debug(f"Fetching EchoLink status: {echolink_url}")
            response = self.session.get(echolink_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()

            # Extract common EchoLink status information
            # Look for status indicators
            if "online" in text.lower():
                status_data["echolink_node_status"] = "Online"
            elif "offline" in text.lower():
                status_data["echolink_node_status"] = "Offline"
            else:
                status_data["echolink_node_status"] = "Unknown"

            # Look for callsign
            callsign_match = re.search(r"([A-Z0-9]{3,8})", text)
            if callsign_match:
                status_data["echolink_callsign"] = callsign_match.group(1)

            # Look for location information
            location_patterns = [
                r"Location:\s*([^\n]+)",
                r"QTH:\s*([^\n]+)",
                r"City:\s*([^\n]+)",
            ]
            for pattern in location_patterns:
                location_match = re.search(pattern, text, re.IGNORECASE)
                if location_match:
                    status_data["echolink_location"] = location_match.group(1).strip()
                    break

            # Look for last activity
            activity_patterns = [r"Last Activity:\s*([^\n]+)", r"Last Seen:\s*([^\n]+)"]
            for pattern in activity_patterns:
                activity_match = re.search(pattern, text, re.IGNORECASE)
                if activity_match:
                    status_data["echolink_last_activity"] = activity_match.group(
                        1
                    ).strip()
                    break

            if self.debug:
                self.logger.debug(f"EchoLink status data for node {node_number}:")
                for key, value in status_data.items():
                    self.logger.debug(f"  {key}: {value}")

        except Exception as e:
            self.logger.debug(
                f"Error fetching EchoLink status from {echolink_url}: {e}"
            )
            status_data["echolink_node_status"] = "Error"
            status_data["echolink_error"] = str(e)

        return status_data

    def _extract_frequency_data(self, text: str, detail_data: Dict[str, Any]) -> None:
        """Extract frequency information with targeted patterns.

        Args:
            text: Page text to parse
            detail_data: Dictionary to store extracted data
        """
        # Extract downlink frequency
        downlink_match = re.search(r"Downlink:\s*(\d+\.\d+)", text)
        if downlink_match:
            detail_data["downlink_freq"] = downlink_match.group(1)

        # Extract uplink frequency
        uplink_match = re.search(r"Uplink:\s*(\d+\.\d+)", text)
        if uplink_match:
            detail_data["uplink_freq"] = uplink_match.group(1)

        # Extract offset with sign
        offset_match = re.search(r"Offset:\s*([+-]?\d+\.\d+)\s*MHz", text)
        if offset_match:
            detail_data["offset_mhz"] = offset_match.group(1)

    def _extract_dmr_data(self, text: str, detail_data: Dict[str, Any]) -> None:
        """Extract DMR-specific information.

        Args:
            text: Page text to parse
            detail_data: Dictionary to store extracted data
        """
        # Extract color code
        color_code_match = re.search(r"DMR Color Code:\s*(\d+)", text)
        if color_code_match:
            detail_data["dmr_color_code"] = color_code_match.group(1)

        # Extract DMR ID (be specific to avoid matching "Repeater ID")
        dmr_id_match = re.search(r"DMR\s+ID:\s*(\d+)", text)
        if dmr_id_match:
            detail_data["dmr_id"] = dmr_id_match.group(1)

        # Only mark as DMR repeater if it has BOTH color code AND DMR ID
        # (actual operational DMR data, not just mention of DMR)
        has_color_code = "dmr_color_code" in detail_data
        has_dmr_id = "dmr_id" in detail_data

        if has_color_code and has_dmr_id:
            detail_data["is_dmr"] = "true"
        else:
            detail_data["is_dmr"] = "false"

    def _extract_talkgroup_data(self, text: str, detail_data: Dict[str, Any]) -> None:
        """Extract and format talkgroup information for DMR repeaters.

        Args:
            text: Page text to parse
            detail_data: Dictionary to store extracted data
        """
        # Extract talkgroups with format "TS1 TG91 🔊 = 91"
        talkgroup_pattern = r"(TS[12])\s+(TG\d+)\s*🔊\s*=\s*(\d+)"
        talkgroup_matches = re.findall(talkgroup_pattern, text)

        if talkgroup_matches:
            # Format talkgroups as "TS1:TG91,TS2:TG95" etc
            talkgroup_list = []
            for ts, tg, tg_num in talkgroup_matches:
                talkgroup_list.append(f"{ts}:{tg}")

            # Store as comma-separated string
            detail_data["talkgroups"] = ",".join(talkgroup_list)

            # Also store count
            detail_data["talkgroup_count"] = str(len(talkgroup_matches))

            # Separate by timeslot for convenience
            ts1_groups = [f"{tg}" for ts, tg, _ in talkgroup_matches if ts == "TS1"]
            ts2_groups = [f"{tg}" for ts, tg, _ in talkgroup_matches if ts == "TS2"]

            if ts1_groups:
                detail_data["ts1_talkgroups"] = ",".join(ts1_groups)
            if ts2_groups:
                detail_data["ts2_talkgroups"] = ",".join(ts2_groups)

    # Override the base _download method to use our enhanced scraping
    def _download(self, level: str, **kwargs) -> pd.DataFrame:
        """Override base download to preserve links when needed."""
        if hasattr(self, "_collecting_details") and self._collecting_details:
            # Use the enhanced scraping method that preserves links
            bands = kwargs.get("bands") or ["all"]
            params = self._build_params(level, **kwargs)
            self.logger.debug(f"Download parameters: {params}")

            # Skip CSV export for detailed collection (we need the HTML)
            self.logger.info("Skipping CSV export for detailed collection")
            html_data, detail_links = self._scrape_with_links(params)

            # Store links for later use
            self._detail_links = detail_links

            # Apply frequency-based band filtering
            from ham_formatter.band_filter import filter_by_frequency

            return filter_by_frequency(html_data, bands)
        else:
            # Use the standard download method
            return super()._download(level, **kwargs)


# Convenience functions to match the API of the main downloader module
def download_with_details(
    state: str,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
) -> pd.DataFrame:
    """Download repeater data for a state with detailed information.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        country: Country name
        bands: List of amateur radio bands to include
        rate_limit: Minimum seconds between requests (ignored if nohammer=True)
        temp_dir: Directory for temporary files
        nohammer: Use random delays (1-10s) for each request instead of fixed rate_limit
        debug: Enable debug logging to show collected data from each detail page

    Returns:
        DataFrame with basic and detailed repeater data
    """
    downloader = DetailedRepeaterDownloader(
        rate_limit=rate_limit, temp_dir=temp_dir, nohammer=nohammer, debug=debug
    )
    return downloader.download_with_details(
        level="state", state=state, country=country, bands=bands or ["all"]
    )


def download_with_details_by_county(
    state: str,
    county: str,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
) -> pd.DataFrame:
    """Download repeater data for a specific county with detailed information.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        county: County name
        country: Country name
        bands: List of amateur radio bands to include
        rate_limit: Minimum seconds between requests (ignored if nohammer=True)
        temp_dir: Directory for temporary files
        nohammer: Use random delays (1-10s) for each request instead of fixed rate_limit
        debug: Enable debug logging to show collected data from each detail page

    Returns:
        DataFrame with basic and detailed repeater data
    """
    downloader = DetailedRepeaterDownloader(
        rate_limit=rate_limit, temp_dir=temp_dir, nohammer=nohammer, debug=debug
    )
    return downloader.download_with_details(
        level="county",
        state=state,
        county=county,
        country=country,
        bands=bands or ["all"],
    )


def download_with_details_by_city(
    state: str,
    city: str,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
) -> pd.DataFrame:
    """Download repeater data for a specific city with detailed information.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        city: City name
        country: Country name
        bands: List of amateur radio bands to include
        rate_limit: Minimum seconds between requests (ignored if nohammer=True)
        temp_dir: Directory for temporary files
        nohammer: Use random delays (1-10s) for each request instead of fixed rate_limit
        debug: Enable debug logging to show collected data from each detail page

    Returns:
        DataFrame with basic and detailed repeater data
    """
    downloader = DetailedRepeaterDownloader(
        rate_limit=rate_limit, temp_dir=temp_dir, nohammer=nohammer, debug=debug
    )
    return downloader.download_with_details(
        level="city", state=state, city=city, country=country, bands=bands or ["all"]
    )
