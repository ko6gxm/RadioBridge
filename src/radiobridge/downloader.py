"""Download repeater data from RepeaterBook.com."""

import tempfile
from typing import Dict, List, Optional, Any
from io import StringIO

import requests
from bs4 import BeautifulSoup

from radiobridge.band_filter import (
    get_repeaterbook_band_param,
    filter_by_frequency,
)
from radiobridge.csv_utils import read_csv
from radiobridge.lightweight_data import LightDataFrame, is_null
from radiobridge.logging_config import get_logger


class RepeaterBookDownloader:
    """Download repeater data from RepeaterBook.com."""

    BASE_URL = "https://www.repeaterbook.com"

    def __init__(self, timeout: int = 30):
        """Initialize the downloader.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "radiobridge/0.2.0 (Amateur Radio Tool)"}
        )
        self.logger = get_logger(__name__)
        self.logger.debug(f"RepeaterBookDownloader initialized with timeout={timeout}s")

    def download_by_state(
        self,
        state: str,
        country: str = "United States",
        bands: Optional[List[str]] = None,
    ) -> LightDataFrame:
        """Download all repeaters for a specific state.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            country: Country name (default: 'United States')
            bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

        Returns:
            LightDataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download("state", state=state, country=country, bands=bands)

    def download_by_county(
        self,
        state: str,
        county: str,
        country: str = "United States",
        bands: Optional[List[str]] = None,
    ) -> LightDataFrame:
        """Download all repeaters for a specific county.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            county: County name (e.g., 'Los Angeles', 'Harris')
            country: Country name (default: 'United States')
            bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

        Returns:
            LightDataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download(
            "county", state=state, county=county, country=country, bands=bands
        )

    def download_by_city(
        self,
        state: str,
        city: str,
        country: str = "United States",
        bands: Optional[List[str]] = None,
    ) -> LightDataFrame:
        """Download all repeaters for a specific city.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            city: City name (e.g., 'Los Angeles', 'Austin')
            country: Country name (default: 'United States')
            bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

        Returns:
            LightDataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download(
            "city", state=state, city=city, country=country, bands=bands
        )

    def _download(self, level: str, **kwargs) -> LightDataFrame:
        """Download repeater data at specified level.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level including 'bands'

        Returns:
            LightDataFrame containing repeater information
        """
        bands = kwargs.get("bands") or ["all"]
        params = self._build_params(level, **kwargs)
        self.logger.debug(f"Download parameters: {params}")

        # First, try to get CSV export if available
        csv_data = self._try_csv_export(params)
        if csv_data is not None:
            self.logger.info(
                f"Successfully downloaded data via CSV export ({len(csv_data)} rows)"
            )
            # Apply frequency-based band filtering
            return filter_by_frequency(csv_data, bands)

        self.logger.info("CSV export not available, falling back to HTML scraping")
        # Fall back to HTML scraping
        html_data = self._scrape_html_table(params)

        # Apply frequency-based band filtering
        return filter_by_frequency(html_data, bands)

    def _build_params(self, level: str, **kwargs) -> Dict[str, Any]:
        """Build query parameters for the specified level.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level including 'bands'

        Returns:
            Dictionary of query parameters
        """
        # Get band filtering parameter
        bands = kwargs.get("bands") or ["all"]
        band_param = get_repeaterbook_band_param(bands)

        # Convert state code to numeric ID for RepeaterBook
        state_code = kwargs.get("state", "")
        state_id = self._get_state_id(state_code)

        # Base parameters for RepeaterBook location search
        params = {
            "state_id": state_id,
            "band": band_param,
        }

        # Add level-specific parameters
        if level == "county":
            params["type"] = "county"
            params["loc"] = kwargs.get("county", "")
        elif level == "city":
            params["type"] = "city"
            params["loc"] = kwargs.get("city", "")
        elif level == "state":
            params["type"] = "state"
            # For state-level, loc is not needed

        self.logger.debug(f"Built params for bands {bands}: {params}")
        return params

    def _get_state_id(self, state_code: str) -> str:
        """Convert state code to RepeaterBook numeric state ID.

        Args:
            state_code: Two-letter state code (e.g., 'CA', 'TX')

        Returns:
            Numeric state ID string
        """
        # RepeaterBook state ID mapping (US states)
        state_mapping = {
            "AL": "01",
            "AK": "02", 
            "AZ": "04",
            "AR": "05",
            "CA": "06",
            "CO": "08",
            "CT": "09",
            "DE": "10",
            "FL": "12",
            "GA": "13",
            "HI": "15",
            "ID": "16",
            "IL": "17",
            "IN": "18",
            "IA": "19",
            "KS": "20",
            "KY": "21",
            "LA": "22",
            "ME": "23",
            "MD": "24",
            "MA": "25",
            "MI": "26",
            "MN": "27",
            "MS": "28",
            "MO": "29",
            "MT": "30",
            "NE": "31",
            "NV": "32",
            "NH": "33",
            "NJ": "34",
            "NM": "35",
            "NY": "36",
            "NC": "37",
            "ND": "38",
            "OH": "39",
            "OK": "40",
            "OR": "41",
            "PA": "42",
            "RI": "44",
            "SC": "45",
            "SD": "46",
            "TN": "47",
            "TX": "48",
            "UT": "49",
            "VT": "50",
            "VA": "51",
            "WA": "53",
            "WV": "54",
            "WI": "55",
            "WY": "56",
            "DC": "11",
        }

        state_id = state_mapping.get(state_code.upper(), state_code)
        self.logger.debug(f"Mapped state code '{state_code}' to ID '{state_id}'")
        return state_id

    def _try_csv_export(self, params: Dict[str, Any]) -> Optional[LightDataFrame]:
        """Attempt to download CSV export if available.

        Args:
            params: Query parameters dictionary

        Returns:
            LightDataFrame if CSV export is available, None otherwise
        """
        # RepeaterBook.com CSV export URL pattern (this may need adjustment)
        csv_url = f"{self.BASE_URL}/repeaters/downloads/index.php"

        # Build CSV export params from search params
        csv_params = {
            "state_id": params.get("state_id", ""),
            "country": params.get("loc", "United States"),
            "format": "csv",
        }

        # Add county/city params if present
        if "county" in params:
            csv_params["county"] = params["county"]
        if "city" in params:
            csv_params["city"] = params["city"]

        self.logger.debug(
            f"Attempting CSV export from {csv_url} with params: {csv_params}"
        )

        try:
            response = self.session.get(
                csv_url, params=csv_params, timeout=self.timeout
            )

            self.logger.debug(
                f"CSV export response: {response.status_code} "
                f"{response.headers.get('content-type', 'unknown')}"
            )

            if response.status_code == 200 and "text/csv" in response.headers.get(
                "content-type", ""
            ):
                # Successfully got CSV data - save to temp file and read with our CSV reader
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
                    temp_file.write(response.text)
                    temp_file.flush()
                    return read_csv(temp_file.name)

        except Exception as e:
            # CSV export not available or failed, will fall back to HTML scraping
            self.logger.debug(f"CSV export failed: {e}")
            pass

        return None

    def _scrape_html_table(self, params: Dict[str, Any]) -> LightDataFrame:
        """Scrape repeater data from HTML table.

        Args:
            params: Query parameters dictionary

        Returns:
            LightDataFrame containing scraped repeater data

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        # RepeaterBook.com location search URL
        search_url = f"{self.BASE_URL}/repeaters/location_search.php"

        self.logger.debug(f"Scraping HTML from {search_url} with params: {params}")

        try:
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            self.logger.debug(
                f"HTML response: {response.status_code} ({len(response.content)} bytes)"
            )

        except requests.RequestException as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise requests.RequestException(f"Failed to download repeater data: {e}")

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")
        self.logger.debug("Parsing HTML content for repeater table")

        # Find the repeater table (this selector may need adjustment)
        table = soup.find(
            "table", class_="w3-table"
        )  # Common class for RepeaterBook tables

        if not table:
            self.logger.debug("w3-table class not found, trying alternative selectors")
            # Try alternative selectors
            table = soup.find("table", id="repeaters")
            if not table:
                tables = soup.find_all("table")
                self.logger.debug(f"Found {len(tables)} tables, selecting largest")
                if tables:
                    # Take the largest table assuming it's the repeater data
                    table = max(tables, key=lambda t: len(t.find_all("tr")))

        if not table:
            # Build error message from params
            state_id = params.get("state_id", "unknown")
            if params.get("type") == "county" and "loc" in params:
                location_desc = f"{params['loc']} County, {state_id}"
            elif params.get("type") == "city" and "loc" in params:
                location_desc = f"{params['loc']}, {state_id}"
            elif params.get("type") == "state":
                location_desc = f"State {state_id}"
            else:
                location_desc = f"Location {state_id}"
            raise ValueError(f"No repeater table found for {location_desc}")

        # Parse table with BeautifulSoup instead of pandas
        try:
            table_data = self._parse_table_with_bs4(table)
            if not table_data:
                raise ValueError("No data found in HTML table")

            # Convert to LightDataFrame
            df = LightDataFrame.from_records(table_data)
            self.logger.info(
                f"Successfully parsed HTML table: {len(df)} rows, "
                f"{len(df.columns)} columns"
            )
            self.logger.debug(f"Table columns: {df.columns}")

            # Basic cleaning
            df = self._clean_scraped_data(df)
            self.logger.info(f"Data cleaning complete: {len(df)} rows after cleaning")

            return df

        except Exception as e:
            self.logger.error(f"Table parsing failed: {e}")
            raise ValueError(f"Failed to parse repeater table: {e}")

    def _parse_table_with_bs4(self, table) -> List[Dict[str, Any]]:
        """Parse HTML table using BeautifulSoup instead of pandas.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            List of dictionaries representing table rows
        """
        rows = []
        
        # Get headers from first row
        header_row = table.find('tr')
        if not header_row:
            return rows
            
        headers = []
        for th in header_row.find_all(['th', 'td']):
            header_text = th.get_text(strip=True)
            headers.append(header_text)
        
        if not headers:
            return rows
        
        # Get data rows (skip header row)
        data_rows = table.find_all('tr')[1:]
        
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                row_dict = {}
                for i, cell in enumerate(cells[:len(headers)]):
                    cell_text = cell.get_text(strip=True)
                    # Convert empty strings to None for consistency
                    cell_value = cell_text if cell_text else None
                    row_dict[headers[i]] = cell_value
                rows.append(row_dict)
        
        return rows

    def _clean_scraped_data(self, df: LightDataFrame) -> LightDataFrame:
        """Clean scraped HTML table data.

        Args:
            df: Raw scraped LightDataFrame

        Returns:
            Cleaned LightDataFrame
        """
        self.logger.debug(
            f"Starting data cleaning: {len(df)} rows, {len(df.columns)} columns"
        )

        # Remove completely empty rows
        rows_before = len(df)
        # Create a new dataframe with non-empty rows  
        cleaned_rows = []
        for i in range(len(df)):
            row = df.iloc(i)
            # Check if all values in the row are null/empty
            all_empty = all(is_null(row.get(col)) for col in df.columns)
            if not all_empty:
                cleaned_rows.append(row.to_dict())
        
        if len(cleaned_rows) < rows_before:
            self.logger.debug(f"Removed {rows_before - len(cleaned_rows)} empty rows")
        
        if not cleaned_rows:
            return LightDataFrame()
            
        df = LightDataFrame.from_records(cleaned_rows)

        # Strip whitespace from string columns
        df.strip_strings()
        self.logger.debug(f"Stripped whitespace from string columns")

        # Handle special case: "Tone Up / Down" column contains two tone values
        tone_up_down_cols = [
            col
            for col in df.columns
            if "tone" in str(col).lower()
            and (
                "up" in str(col).lower()
                or "down" in str(col).lower()
                or "/" in str(col)
            )
        ]
        
        if tone_up_down_cols:
            tone_col = tone_up_down_cols[0]
            self.logger.debug(
                f"Found combined tone column: '{tone_col}', "
                "splitting into separate columns"
            )

            # Split the tone column into tone_up and tone_down
            tone_up_values = []
            tone_down_values = []

            tone_col_data = df[tone_col] if tone_col in df._data else [None] * len(df)
            
            for value in tone_col_data:
                if is_null(value) or str(value).strip() in ["", "nan", "None"]:
                    tone_up_values.append(None)
                    tone_down_values.append(None)
                else:
                    # Convert to string and clean up
                    value_str = str(value).strip()

                    # Split on common delimiters (space, slash, comma, etc.)
                    # Look for patterns like "123.0 / 456.0" or "123.0 456.0"
                    if "/" in value_str:
                        parts = value_str.split("/", 1)
                    elif " " in value_str and len(value_str.split()) >= 2:
                        # Handle space-separated values, but be careful with
                        # single values that have spaces
                        parts = value_str.split(
                            None, 1
                        )  # Split on any whitespace, max 2 parts
                    else:
                        # Single value - treat as tone_up, leave tone_down empty
                        parts = [value_str, ""]

                    # Clean and extract the tone values
                    tone_up = parts[0].strip() if len(parts) > 0 else ""
                    tone_down = parts[1].strip() if len(parts) > 1 else ""

                    # Convert empty strings to None
                    tone_up_values.append(tone_up if tone_up else None)
                    tone_down_values.append(tone_down if tone_down else None)

            # Add the new columns and remove the original
            # Create new data dict with the additional columns
            new_data = df._data.copy()
            new_data["tone_up"] = tone_up_values
            new_data["tone_down"] = tone_down_values
            
            # Remove the original tone column
            if tone_col in new_data:
                del new_data[tone_col]
                
            # Update columns list
            new_columns = [col for col in df.columns if col != tone_col] + ["tone_up", "tone_down"]
            df = LightDataFrame(new_data, new_columns)

            self.logger.debug(
                f"Split '{tone_col}' into 'tone_up' and 'tone_down' columns"
            )

        # Try to standardize common column names
        column_mapping = {
            "Frequency": "frequency",
            "Offset": "offset", 
            "Tone": "tone",
            "Call Sign": "callsign",
            "Callsign": "callsign",
            "Location": "location",
            "City": "city",
            "County": "county",
            "State": "state",
            "Use": "use",
            "Operational Status": "status",
        }

        # Rename columns if they match our mapping
        original_columns = df.columns.copy()
        new_columns = [
            column_mapping.get(col, str(col).lower().replace(" ", "_"))
            for col in df.columns
        ]
        
        # Create new data with renamed columns
        new_data = {}
        for old_col, new_col in zip(original_columns, new_columns):
            if old_col in df._data:
                new_data[new_col] = df._data[old_col]
                
        df = LightDataFrame(new_data, new_columns)

        renamed_cols = [
            f"{orig} -> {new}"
            for orig, new in zip(original_columns, new_columns)
            if orig != new
        ]
        if renamed_cols:
            self.logger.debug(f"Column mappings: {', '.join(renamed_cols)}")

        return df


def download_repeater_data(
    state: str,
    country: str = "United States",
    timeout: int = 30,
    bands: Optional[List[str]] = None,
) -> LightDataFrame:
    """Download repeater data from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified location.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds
        bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

    Returns:
        LightDataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_state(state, country, bands)


def download_repeater_data_by_county(
    state: str,
    county: str,
    country: str = "United States",
    timeout: int = 30,
    bands: Optional[List[str]] = None,
) -> LightDataFrame:
    """Download repeater data for a specific county from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified county.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        county: County name (e.g., 'Los Angeles', 'Harris')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds
        bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

    Returns:
        LightDataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_county(state, county, country, bands)


def download_repeater_data_by_city(
    state: str,
    city: str,
    country: str = "United States",
    timeout: int = 30,
    bands: Optional[List[str]] = None,
) -> LightDataFrame:
    """Download repeater data for a specific city from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified city.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        city: City name (e.g., 'Los Angeles', 'Austin')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds
        bands: List of amateur radio bands to include (e.g., ['2m', '70cm'])

    Returns:
        LightDataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_city(state, city, country, bands)
