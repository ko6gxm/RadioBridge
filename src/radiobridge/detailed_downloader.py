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

from bs4 import BeautifulSoup

from radiobridge.downloader import RepeaterBookDownloader
from radiobridge.lightweight_data import LightDataFrame, LightSeries, is_null, write_csv_light
from radiobridge.logging_config import get_logger


class DetailedRepeaterDownloader(RepeaterBookDownloader):
    """Enhanced downloader that collects detailed repeater information.

    This downloader extends the basic RepeaterBookDownloader to collect detailed
    information from individual repeater pages. It handles band filtering while
    preserving original DataFrame indices.
    """

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

    def download_with_details(self, level: str, **kwargs) -> LightDataFrame:
        """Download repeater data including detailed information from individual pages.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level including 'bands'

        Returns:
            LightDataFrame containing basic + detailed repeater information
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
            from radiobridge.band_filter import filter_by_frequency

            basic_data = filter_by_frequency(basic_data, bands)

            if basic_data.empty:
                self.logger.warning("No basic data found after filtering")
                return basic_data

            # Filter detail links to match the filtered basic data
            filtered_detail_links = self._filter_detail_links_by_data(
                detail_links, basic_data
            )

            self.logger.info(f"Collected {len(basic_data)} basic repeater records")
            self.logger.info(
                f"Found {len(detail_links)} total detail links, {len(filtered_detail_links)} match filtered data"
            )

            # Create temporary directory for this download session
            with tempfile.TemporaryDirectory(
                dir=self.temp_dir, prefix="radiobridge_"
            ) as temp_session_dir:
                session_dir = Path(temp_session_dir)
                self.logger.debug(f"Using temporary directory: {session_dir}")

                # Save basic data
                basic_file = session_dir / "basic_data.csv"
                write_csv_light(basic_data, basic_file, index=False)
                self.logger.debug(f"Saved basic data to {basic_file}")

                # Collect detailed data with progress tracking
                detailed_data = self._collect_detailed_data(
                    filtered_detail_links, session_dir
                )

                # Merge basic and detailed data
                enhanced_data = self._merge_data(basic_data, detailed_data)

                self.logger.info(
                    f"Enhanced dataset ready with {len(enhanced_data)} records"
                )
                return enhanced_data

        finally:
            # Clean up flag
            self._collecting_details = False

    def _scrape_with_links(
        self, params: Dict[str, Any]
    ) -> Tuple[LightDataFrame, List[Dict[str, Any]]]:
        """Scrape the main table while preserving detail page links.

        Args:
            params: Query parameters for the search

        Returns:
            Tuple of (LightDataFrame with basic data, list of detail links)
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

        # Extract data using BeautifulSoup and LightDataFrame
        table_data = self._parse_table_with_bs4(main_table)
        if not table_data:
            raise ValueError("No data found in HTML table")
        df = LightDataFrame.from_records(table_data)

        # Extract detail links from the same table
        detail_links = self._extract_links_from_table(main_table, df)

        return df, detail_links

    def _extract_links_from_table(
        self, table, df: LightDataFrame
    ) -> List[Dict[str, Any]]:
        """Extract detail page links from HTML table.

        Args:
            table: BeautifulSoup table element
            df: Corresponding LightDataFrame with cleaned data

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
                            # Get row data safely
                            row_series = df.iloc(row_index)
                            detail_links.append(
                                {
                                    "detail_url": detail_url,
                                    "row_index": row_index,
                                    "frequency": row_series.get("frequency", ""),
                                    "callsign": row_series.get("call", ""),
                                    "location": row_series.get("location", ""),
                                }
                            )

        self.logger.debug(f"Extracted {len(detail_links)} detail links")
        return detail_links

    def _filter_detail_links_by_data(
        self, detail_links: List[Dict[str, Any]], filtered_data: LightDataFrame
    ) -> List[Dict[str, Any]]:
        """Filter detail links to only include those matching the filtered basic data.

        Args:
            detail_links: List of all detail links from the original scraping
            filtered_data: LightDataFrame containing the filtered basic data

        Returns:
            List of detail links that correspond to rows in the filtered data
        """
        # Create a set of valid indices from the filtered data
        # LightDataFrame uses row positions as indices
        remaining_indices = set(range(len(filtered_data)))

        # Filter detail links to only include those whose row_index is in remaining_indices
        filtered_links = [
            link for link in detail_links if link["row_index"] in remaining_indices
        ]

        self.logger.debug(
            f"Filtered detail links from {len(detail_links)} to {len(filtered_links)} "
            f"based on filtered data indices: {sorted(remaining_indices)}"
        )

        return filtered_links

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

            # Extract IRLP information from HTML
            irlp_data = self._extract_irlp_info(soup, detail_url)
            if irlp_data:
                detail_data.update(irlp_data)

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
        self, basic_data: LightDataFrame, detailed_data: Dict[int, Dict[str, Any]]
    ) -> LightDataFrame:
        """Merge basic and detailed data into structured format.

        Args:
            basic_data: LightDataFrame with basic repeater information
            detailed_data: Dictionary mapping row indices to detailed data

        Returns:
            Structured LightDataFrame with specific columns and consolidated notes
        """
        # Create structured output with specific columns
        structured_data = self._create_structured_output(basic_data, detailed_data)

        self.logger.info(
            f"Created structured dataset with {len(structured_data.columns)} columns"
        )
        return structured_data

    def _create_structured_output(
        self, basic_data: LightDataFrame, detailed_data: Dict[int, Dict[str, Any]]
    ) -> LightDataFrame:
        """Create structured output with specific columns and consolidated notes.

        Args:
            basic_data: LightDataFrame with basic repeater information
            detailed_data: Dictionary mapping row indices to detailed data

        Returns:
            Structured LightDataFrame with specific columns and notes
        """
        # Define the specific columns we want in the output
        target_columns = [
            "Downlink",
            "Uplink", 
            "Offset",
            "Uplink Tone",
            "Downlink Tone",
            "DMR",
            "Color Code",
            "DMR ID",
            "SYSTEM FUSION",
            "DG‑ID",
            "WIRES‑X",
            "County",
            "Grid Square",
            "Call",
            "Use",
            "Status",
            "Sponsor",
            "Affiliate",
            "FM",
            "EchoLink",
            "Coordination",
            "Updated",
            "Reviewed",
            "EchoLink Node",
            "EchoLink Status",
            "EchoLink Callsign",
            "EchoLink Location",
            "EchoLink Last Activity",
            "IRLP",
            "IRLP Node",
            "IRLP Status",
            "IRLP Last Activity",
            "IRLP Callsign",
            "IRLP Location",
            "Notes",
        ]

        # Initialize structured data dictionary
        structured_dict = {col: [] for col in target_columns}

        # Process each row in the basic data
        for row_idx in range(len(basic_data)):
            # Get row data from LightDataFrame
            basic_row = basic_data.iloc(row_idx)
            row_detail = detailed_data.get(row_idx, {})

            # Extract and map specific fields
            structured_dict["Downlink"].append(row_detail.get("downlink_freq", ""))
            structured_dict["Uplink"].append(row_detail.get("uplink_freq", ""))
            structured_dict["Offset"].append(row_detail.get("offset_mhz", ""))

            # For tone data, we need to extract from basic data or detailed data
            structured_dict["Uplink Tone"].append(
                self._get_tone_data(basic_row, row_detail, "up")
            )
            structured_dict["Downlink Tone"].append(
                self._get_tone_data(basic_row, row_detail, "down")
            )

            # DMR information
            structured_dict["DMR"].append(row_detail.get("is_dmr", "false"))
            structured_dict["Color Code"].append(row_detail.get("dmr_color_code", ""))
            structured_dict["DMR ID"].append(row_detail.get("dmr_id", ""))

            # System Fusion and WIRES-X (extract from detail data)
            structured_dict["SYSTEM FUSION"].append(self._extract_system_fusion(row_detail))
            structured_dict["DG‑ID"].append(self._extract_dg_id(row_detail))
            structured_dict["WIRES‑X"].append(self._extract_wires_x(row_detail))

            # Basic information (from basic data with detail fallback)
            structured_dict["County"].append(
                row_detail.get("county", basic_row.get("county", ""))
            )
            structured_dict["Grid Square"].append(self._extract_grid_square(row_detail))
            structured_dict["Call"].append(
                row_detail.get("call", basic_row.get("call", basic_row.get("callsign", "")))
            )
            structured_dict["Use"].append(
                row_detail.get("use", basic_row.get("use", ""))
            )
            structured_dict["Status"].append(
                row_detail.get("status", basic_row.get("status", ""))
            )

            # Sponsor and coordination info
            structured_dict["Sponsor"].append(row_detail.get("sponsor", ""))
            structured_dict["Affiliate"].append(row_detail.get("affiliate", ""))
            structured_dict["Coordination"].append(row_detail.get("coordination", ""))

            # FM capability
            structured_dict["FM"].append(self._extract_fm_capability(row_detail))

            # Dates
            structured_dict["Updated"].append(row_detail.get("updated", ""))
            structured_dict["Reviewed"].append(row_detail.get("reviewed", ""))

            # EchoLink information
            structured_dict["EchoLink"].append(row_detail.get("echolink_node", ""))
            structured_dict["EchoLink Node"].append(row_detail.get("echolink_node", ""))
            structured_dict["EchoLink Status"].append(
                row_detail.get("echolink_node_status", "")
            )
            structured_dict["EchoLink Callsign"].append(
                row_detail.get("echolink_callsign", "")
            )
            structured_dict["EchoLink Location"].append(
                row_detail.get("echolink_location", "")
            )
            structured_dict["EchoLink Last Activity"].append(
                row_detail.get("echolink_last_activity", "")
            )

            # IRLP information
            structured_dict["IRLP"].append(row_detail.get("irlp_node", ""))
            structured_dict["IRLP Node"].append(row_detail.get("irlp_node", ""))
            structured_dict["IRLP Status"].append(
                row_detail.get("irlp_node_status", "")
            )
            structured_dict["IRLP Last Activity"].append(
                row_detail.get("irlp_last_activity", "")
            )
            structured_dict["IRLP Callsign"].append(
                row_detail.get("irlp_callsign", "")
            )
            structured_dict["IRLP Location"].append(
                row_detail.get("irlp_location", "")
            )

            # Consolidate remaining data into notes
            structured_dict["Notes"].append(
                self._create_notes_field(basic_row, row_detail, target_columns)
            )

        return LightDataFrame(structured_dict, target_columns)

    def _get_tone_data(
        self, basic_row: LightSeries, detail_data: Dict[str, Any], direction: str
    ) -> str:
        """Extract tone data for uplink or downlink."""
        if direction == "up":
            # Check detail data first, then basic data
            tone = detail_data.get(
                "tone_up", basic_row.get("tone_up", basic_row.get("tone", ""))
            )
        else:  # direction == "down"
            tone = detail_data.get(
                "tone_down", basic_row.get("tone_down", basic_row.get("tone", ""))
            )

        return str(tone) if tone else ""

    def _extract_system_fusion(self, detail_data: Dict[str, Any]) -> str:
        """Extract System Fusion information."""
        for key, value in detail_data.items():
            if "fusion" in key.lower() or "system fusion" in str(value).lower():
                return str(value)
        return ""

    def _extract_dg_id(self, detail_data: Dict[str, Any]) -> str:
        """Extract DG-ID information."""
        for key, value in detail_data.items():
            if "dg" in key.lower() and "id" in key.lower():
                return str(value)
        return ""

    def _extract_wires_x(self, detail_data: Dict[str, Any]) -> str:
        """Extract WIRES-X information."""
        for key, value in detail_data.items():
            if "wires" in key.lower():
                return str(value)
        return ""

    def _extract_grid_square(self, detail_data: Dict[str, Any]) -> str:
        """Extract grid square information."""
        grid_squares = detail_data.get("grid_squares", [])
        if grid_squares:
            return (
                grid_squares[0] if isinstance(grid_squares, list) else str(grid_squares)
            )

        # Look for grid square in other fields
        for key, value in detail_data.items():
            if "grid" in key.lower():
                return str(value)
        return ""

    def _extract_fm_capability(self, detail_data: Dict[str, Any]) -> str:
        """Extract FM capability information."""
        fm_value = detail_data.get("fm", "")
        if fm_value:
            return str(fm_value)

        # Look for analog capability mentions
        for key, value in detail_data.items():
            if "analog" in key.lower() or "fm" in key.lower():
                return str(value)
        return ""

    def _create_notes_field(
        self, basic_row: LightSeries, detail_data: Dict[str, Any], used_columns: List[str]
    ) -> str:
        """Create notes field with all remaining data."""
        notes = []

        # Add talkgroup information for DMR repeaters
        if detail_data.get("is_dmr") == "true":
            talkgroups = detail_data.get("talkgroups", "")
            if talkgroups:
                notes.append(f"Talkgroups: {talkgroups}")

            ts1_tgs = detail_data.get("ts1_talkgroups", "")
            ts2_tgs = detail_data.get("ts2_talkgroups", "")
            if ts1_tgs:
                notes.append(f"TS1: {ts1_tgs}")
            if ts2_tgs:
                notes.append(f"TS2: {ts2_tgs}")

        # Add other detail data that wasn't used in specific columns
        excluded_keys = {
            "downlink_freq",
            "uplink_freq",
            "offset_mhz",
            "tone_up",
            "tone_down",
            "tone",
            "is_dmr",
            "dmr_color_code",
            "dmr_id",
            "county",
            "call",
            "callsign",
            "use",
            "status",
            "sponsor",
            "affiliate",
            "coordination",
            "fm",
            "updated",
            "reviewed",
            "echolink_node",
            "echolink_node_status",
            "echolink_callsign",
            "echolink_location",
            "echolink_last_activity",
            "echolink_status_text",
            "echolink_url",
            "echolink_error",
            "irlp_node",
            "irlp_node_status",
            "irlp_callsign",
            "irlp_location",
            "irlp_last_activity",
            "irlp_status_text",
            "irlp_status_detail",
            "irlp_url",
            "irlp_error",
            "irlp_owner",
            "irlp_node_name",
            "grid_squares",
            "talkgroups",
            "ts1_talkgroups",
            "ts2_talkgroups",
            "talkgroup_count",
        }

        for key, value in detail_data.items():
            if key not in excluded_keys and value and str(value).strip():
                # Clean up key for display
                display_key = key.replace("_", " ").title()
                notes.append(f"{display_key}: {value}")

        # Add basic data that wasn't used - iterate through basic_row data
        basic_row_dict = basic_row.to_dict()
        for col, value in basic_row_dict.items():
            if (
                col not in ["frequency", "call", "callsign", "county", "use", "status"]
                and not is_null(value)
                and str(value).strip()
            ):
                display_col = col.replace("_", " ").title()
                notes.append(f"{display_col}: {value}")

        return "; ".join(notes)

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

    def _extract_irlp_info(
        self, soup: BeautifulSoup, detail_url: str
    ) -> Dict[str, Any]:
        """Extract IRLP information from repeater detail page.

        Args:
            soup: BeautifulSoup object of the detail page
            detail_url: URL of the detail page for logging

        Returns:
            Dictionary with IRLP data including node status
        """
        irlp_data = {}

        try:
            # Look for IRLP in the HTML content
            text = soup.get_text()

            # Search for IRLP pattern in text
            # Pattern: "IRLP: 3341 — IDLE for 0 days, 3 hours, 26 minutes, 46 seconds"
            irlp_match = re.search(r"IRLP:\s*(\d+)([^\n]*)", text, re.IGNORECASE)
            if irlp_match:
                node_number = irlp_match.group(1)
                status_text = irlp_match.group(2).strip()

                irlp_data["irlp_node"] = node_number
                if status_text:
                    irlp_data["irlp_status_text"] = status_text

                # Look for IRLP links in HTML
                irlp_links = soup.find_all(
                    "a", href=re.compile(r"irlp|status\.irlp\.net", re.IGNORECASE)
                )

                for link in irlp_links:
                    href = link.get("href")
                    if href and node_number in href:
                        # Found IRLP status link
                        irlp_url = (
                            href
                            if href.startswith("http")
                            else urljoin("https://status.irlp.net/", href)
                        )
                        irlp_data["irlp_url"] = irlp_url

                        # Fetch IRLP node status
                        node_status = self._scrape_irlp_status(irlp_url, node_number)
                        if node_status:
                            irlp_data.update(node_status)
                        break

                if self.debug:
                    self.logger.debug(
                        f"IRLP found for {detail_url}: Node {node_number}"
                    )
                    if "irlp_url" in irlp_data:
                        self.logger.debug(f"  Link: {irlp_data['irlp_url']}")
                    if "irlp_node_status" in irlp_data:
                        self.logger.debug(f"  Status: {irlp_data['irlp_node_status']}")

        except Exception as e:
            self.logger.debug(f"Error extracting IRLP info from {detail_url}: {e}")

        return irlp_data

    def _scrape_irlp_status(self, irlp_url: str, node_number: str) -> Dict[str, Any]:
        """Scrape IRLP node status from IRLP website.

        Args:
            irlp_url: URL to the IRLP node status page
            node_number: IRLP node number for validation

        Returns:
            Dictionary with IRLP node status information
        """
        status_data = {}

        try:
            # Apply rate limiting for external requests
            self._apply_rate_limit()

            self.logger.debug(f"Fetching IRLP status: {irlp_url}")
            response = self.session.get(irlp_url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()

            # Extract common IRLP status information
            # Look for status indicators (IDLE, ONLINE, OFFLINE, CONNECTED, etc.)
            status_indicators = [
                (r"IDLE\s+for\s+([^\n]+)", "IDLE"),
                (r"CONNECTED\s+to\s+([^\n]+)", "CONNECTED"),
                (r"ONLINE\s+([^\n]*)", "ONLINE"),
                (r"OFFLINE\s+([^\n]*)", "OFFLINE"),
                (r"Status:\s*([^\n]+)", None),  # Generic status pattern
            ]

            for pattern, default_status in status_indicators:
                status_match = re.search(pattern, text, re.IGNORECASE)
                if status_match:
                    status_info = status_match.group(1).strip()
                    if default_status:
                        status_data["irlp_node_status"] = default_status
                        if status_info:
                            status_data["irlp_status_detail"] = status_info
                    else:
                        status_data["irlp_node_status"] = status_info
                    break

            # If no specific status found, look for general online/offline indicators
            if "irlp_node_status" not in status_data:
                if "online" in text.lower():
                    status_data["irlp_node_status"] = "Online"
                elif "offline" in text.lower():
                    status_data["irlp_node_status"] = "Offline"
                elif "idle" in text.lower():
                    status_data["irlp_node_status"] = "IDLE"
                else:
                    status_data["irlp_node_status"] = "Unknown"

            # Look for callsign (more specific patterns)
            callsign_patterns = [
                r"Call:\s*([A-Z0-9]{3,8}(?:-[A-Z0-9]+)?)",  # "Call: W6ABC-R"
                r"Callsign:\s*([A-Z0-9]{3,8}(?:-[A-Z0-9]+)?)",  # "Callsign: W6ABC-R"
                r"([A-Z]{1,2}[0-9][A-Z]{1,3}(?:-[A-Z0-9]+)?)",  # General amateur radio callsign pattern
            ]

            for pattern in callsign_patterns:
                callsign_match = re.search(pattern, text, re.IGNORECASE)
                if callsign_match:
                    callsign = callsign_match.group(1)
                    # Validate that this looks like a callsign and not a node number
                    if not callsign.isdigit() and len(callsign) >= 3:
                        status_data["irlp_callsign"] = callsign
                        break

            # Look for location information
            location_patterns = [
                r"Location:\s*([^\n]+)",
                r"QTH:\s*([^\n]+)",
                r"City:\s*([^\n]+)",
                r"Node\s+Location:\s*([^\n]+)",
            ]
            for pattern in location_patterns:
                location_match = re.search(pattern, text, re.IGNORECASE)
                if location_match:
                    status_data["irlp_location"] = location_match.group(1).strip()
                    break

            # Look for last activity/connection information
            activity_patterns = [
                r"Last\s+Activity:\s*([^\n]+)",
                r"Last\s+Connect:\s*([^\n]+)",
                r"Last\s+Connection:\s*([^\n]+)",
                r"Last\s+Heard:\s*([^\n]+)",
            ]
            for pattern in activity_patterns:
                activity_match = re.search(pattern, text, re.IGNORECASE)
                if activity_match:
                    status_data["irlp_last_activity"] = activity_match.group(1).strip()
                    break

            # Look for node owner/trustee information
            owner_patterns = [
                r"Owner:\s*([^\n]+)",
                r"Trustee:\s*([^\n]+)",
                r"Contact:\s*([^\n]+)",
            ]
            for pattern in owner_patterns:
                owner_match = re.search(pattern, text, re.IGNORECASE)
                if owner_match:
                    status_data["irlp_owner"] = owner_match.group(1).strip()
                    break

            # Look for node description/name
            name_patterns = [
                r"Node\s+Name:\s*([^\n]+)",
                r"Description:\s*([^\n]+)",
                r"Node\s+Description:\s*([^\n]+)",
            ]
            for pattern in name_patterns:
                name_match = re.search(pattern, text, re.IGNORECASE)
                if name_match:
                    status_data["irlp_node_name"] = name_match.group(1).strip()
                    break

            if self.debug:
                self.logger.debug(f"IRLP status data for node {node_number}:")
                for key, value in status_data.items():
                    self.logger.debug(f"  {key}: {value}")

        except Exception as e:
            self.logger.debug(f"Error fetching IRLP status from {irlp_url}: {e}")
            status_data["irlp_node_status"] = "Error"
            status_data["irlp_error"] = str(e)

        return status_data

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
        # Extract color code with multiple patterns
        color_code_patterns = [
            r"DMR Color Code:\s*(\d+)",
            r"Color Code:\s*(\d+)",
            r"DMR\s+Color\s+Code:\s*(\d+)",
            r"Color\s+Code\s*:\s*(\d+)",
        ]

        for pattern in color_code_patterns:
            color_code_match = re.search(pattern, text, re.IGNORECASE)
            if color_code_match:
                detail_data["dmr_color_code"] = color_code_match.group(1)
                break

        # Extract DMR ID with multiple patterns
        dmr_id_patterns = [
            r"DMR\s+ID:\s*(\d+)",  # "DMR ID: 310724"
            r"DMR\s+ID\s+(\d+)",  # "DMR ID 310724" (no colon)
            r"DMRID:\s*(\d+)",  # "DMRID: 310724"
        ]

        for pattern in dmr_id_patterns:
            dmr_id_match = re.search(pattern, text, re.IGNORECASE)
            if dmr_id_match:
                detail_data["dmr_id"] = dmr_id_match.group(1)
                break

        # Check for DMR indicators in the text (to detect DMR even without numeric ID)
        dmr_indicators = [
            r"DMR\s+Color\s+Code",
            r"DMR\s+Network",
            r"DMR\s+ID",
            r"Western\s+States\s+DMR",
            r"Brandmeister",
            r"IPSC",
            r"DMR\s*-?\s*Marc",
        ]

        has_dmr_indicators = any(
            re.search(pattern, text, re.IGNORECASE) for pattern in dmr_indicators
        )

        # Enhanced DMR detection logic
        has_color_code = "dmr_color_code" in detail_data
        has_dmr_id = "dmr_id" in detail_data
        has_talkgroups = bool(detail_data.get("talkgroups"))

        # DMR detection logic (more flexible):
        # 1. Has DMR color code (strong indicator)
        # 2. Has numeric DMR ID
        # 3. Has talkgroups (DMR-specific)
        # 4. Has DMR-related text indicators
        if has_color_code or has_dmr_id or has_talkgroups or has_dmr_indicators:
            detail_data["is_dmr"] = "true"

            # Debug logging for DMR detection
            if self.debug:
                reasons = []
                if has_color_code:
                    reasons.append(f"color_code={detail_data['dmr_color_code']}")
                if has_dmr_id:
                    reasons.append(f"dmr_id={detail_data['dmr_id']}")
                if has_talkgroups:
                    reasons.append("talkgroups")
                if has_dmr_indicators:
                    reasons.append("dmr_indicators")
                self.logger.debug(f"DMR detected due to: {', '.join(reasons)}")
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
    def _download(self, level: str, **kwargs) -> LightDataFrame:
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
            from radiobridge.band_filter import filter_by_frequency

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
) -> LightDataFrame:
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
        LightDataFrame with basic and detailed repeater data
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
) -> LightDataFrame:
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
        LightDataFrame with basic and detailed repeater data
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
) -> LightDataFrame:
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
        LightDataFrame with basic and detailed repeater data
    """
    downloader = DetailedRepeaterDownloader(
        rate_limit=rate_limit, temp_dir=temp_dir, nohammer=nohammer, debug=debug
    )
    return downloader.download_with_details(
        level="city", state=state, city=city, country=country, bands=bands or ["all"]
    )
