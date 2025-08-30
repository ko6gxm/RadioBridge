"""Download repeater data from RepeaterBook.com."""

from typing import Dict, Optional, Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from ham_formatter.logging_config import get_logger


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
            {"User-Agent": "ham-formatter/0.2.0 (Amateur Radio Tool)"}
        )
        self.logger = get_logger(__name__)
        self.logger.debug(f"RepeaterBookDownloader initialized with timeout={timeout}s")

    def download_by_state(
        self, state: str, country: str = "United States"
    ) -> pd.DataFrame:
        """Download all repeaters for a specific state.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            country: Country name (default: 'United States')

        Returns:
            DataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download("state", state=state, country=country)

    def download_by_county(
        self, state: str, county: str, country: str = "United States"
    ) -> pd.DataFrame:
        """Download all repeaters for a specific county.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            county: County name (e.g., 'Los Angeles', 'Harris')
            country: Country name (default: 'United States')

        Returns:
            DataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download("county", state=state, county=county, country=country)

    def download_by_city(
        self, state: str, city: str, country: str = "United States"
    ) -> pd.DataFrame:
        """Download all repeaters for a specific city.

        Args:
            state: State/province code (e.g., 'CA', 'TX')
            city: City name (e.g., 'Los Angeles', 'Austin')
            country: Country name (default: 'United States')

        Returns:
            DataFrame containing repeater information

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        return self._download("city", state=state, city=city, country=country)

    def _download(self, level: str, **kwargs) -> pd.DataFrame:
        """Download repeater data at specified level.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level

        Returns:
            DataFrame containing repeater information
        """
        params = self._build_params(level, **kwargs)
        self.logger.debug(f"Download parameters: {params}")

        # First, try to get CSV export if available
        csv_data = self._try_csv_export(params)
        if csv_data is not None:
            self.logger.info(
                f"Successfully downloaded data via CSV export ({len(csv_data)} rows)"
            )
            return csv_data

        self.logger.info("CSV export not available, falling back to HTML scraping")
        # Fall back to HTML scraping
        return self._scrape_html_table(params)

    def _build_params(self, level: str, **kwargs) -> Dict[str, Any]:
        """Build query parameters for the specified level.

        Args:
            level: Download level ('state', 'county', or 'city')
            **kwargs: Parameters for the specific level

        Returns:
            Dictionary of query parameters
        """
        # Base parameters for all levels
        params = {
            "state_id": kwargs.get("state", ""),
            "loc": kwargs.get("country", "United States"),
            "band": "All",
            "freq": "",
            "band6": "",
            "use": "All",
            "sort": "Distance",
        }

        # Add level-specific parameters
        if level == "county":
            params["county"] = kwargs.get("county", "")
        elif level == "city":
            params["city"] = kwargs.get("city", "")

        return params

    def _try_csv_export(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Attempt to download CSV export if available.

        Args:
            params: Query parameters dictionary

        Returns:
            DataFrame if CSV export is available, None otherwise
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
                f"CSV export response: {response.status_code} {response.headers.get('content-type', 'unknown')}"
            )

            if response.status_code == 200 and "text/csv" in response.headers.get(
                "content-type", ""
            ):
                # Successfully got CSV data
                from io import StringIO

                return pd.read_csv(StringIO(response.text))

        except Exception as e:
            # CSV export not available or failed, will fall back to HTML scraping
            self.logger.debug(f"CSV export failed: {e}")
            pass

        return None

    def _scrape_html_table(self, params: Dict[str, Any]) -> pd.DataFrame:
        """Scrape repeater data from HTML table.

        Args:
            params: Query parameters dictionary

        Returns:
            DataFrame containing scraped repeater data

        Raises:
            requests.RequestException: If download fails
            ValueError: If no data is found or parsing fails
        """
        # RepeaterBook.com search URL (this URL structure may need verification)
        search_url = f"{self.BASE_URL}/repeaters/index.php"

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
            location_desc = params.get("state_id", "unknown")
            if "county" in params:
                location_desc = f"{params['county']} County, {location_desc}"
            elif "city" in params:
                location_desc = f"{params['city']}, {location_desc}"
            location_desc += f", {params.get('loc', 'Unknown Country')}"
            raise ValueError(f"No repeater table found for {location_desc}")

        # Convert HTML table to DataFrame
        try:
            # Use pandas read_html for easier table parsing
            from io import StringIO

            dfs = pd.read_html(StringIO(str(table)))
            if not dfs:
                raise ValueError("No data found in HTML table")

            df = dfs[0]  # Take the first (and likely only) table
            self.logger.info(
                f"Successfully parsed HTML table: {len(df)} rows, {len(df.columns)} columns"
            )
            self.logger.debug(f"Table columns: {list(df.columns)}")

            # Basic cleaning
            df = self._clean_scraped_data(df)
            self.logger.info(f"Data cleaning complete: {len(df)} rows after cleaning")

            return df

        except Exception as e:
            self.logger.error(f"Table parsing failed: {e}")
            raise ValueError(f"Failed to parse repeater table: {e}")

    def _clean_scraped_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean scraped HTML table data.

        Args:
            df: Raw scraped DataFrame

        Returns:
            Cleaned DataFrame
        """
        self.logger.debug(
            f"Starting data cleaning: {len(df)} rows, {len(df.columns)} columns"
        )

        # Remove any completely empty rows
        rows_before = len(df)
        df = df.dropna(how="all")
        if len(df) < rows_before:
            self.logger.debug(f"Removed {rows_before - len(df)} empty rows")

        # Strip whitespace from all string columns and replace empty strings with NaN
        string_columns = df.select_dtypes(include=["object"]).columns
        self.logger.debug(
            f"Cleaning {len(string_columns)} string columns: {list(string_columns)}"
        )
        for col in string_columns:
            if hasattr(df[col], "str"):
                df[col] = df[col].str.strip()
                df[col] = df[col].replace("", pd.NA)

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
        original_columns = list(df.columns)
        df.columns = [
            column_mapping.get(col, col.lower().replace(" ", "_")) for col in df.columns
        ]

        renamed_cols = [
            f"{orig} -> {new}"
            for orig, new in zip(original_columns, df.columns)
            if orig != new
        ]
        if renamed_cols:
            self.logger.debug(f"Column mappings: {', '.join(renamed_cols)}")

        return df


def download_repeater_data(
    state: str, country: str = "United States", timeout: int = 30
) -> pd.DataFrame:
    """Download repeater data from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified location.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds

    Returns:
        DataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_state(state, country)


def download_repeater_data_by_county(
    state: str, county: str, country: str = "United States", timeout: int = 30
) -> pd.DataFrame:
    """Download repeater data for a specific county from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified county.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        county: County name (e.g., 'Los Angeles', 'Harris')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds

    Returns:
        DataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_county(state, county, country)


def download_repeater_data_by_city(
    state: str, city: str, country: str = "United States", timeout: int = 30
) -> pd.DataFrame:
    """Download repeater data for a specific city from RepeaterBook.com.

    This is a convenience function that creates a RepeaterBookDownloader
    and downloads data for the specified city.

    Args:
        state: State/province code (e.g., 'CA', 'TX')
        city: City name (e.g., 'Los Angeles', 'Austin')
        country: Country name (default: 'United States')
        timeout: Request timeout in seconds

    Returns:
        DataFrame containing repeater information

    Raises:
        requests.RequestException: If download fails
        ValueError: If no data is found or parsing fails
    """
    downloader = RepeaterBookDownloader(timeout=timeout)
    return downloader.download_by_city(state, city, country)
