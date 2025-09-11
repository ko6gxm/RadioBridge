"""Unified downloader facade that selects between basic and detailed strategies.

This provides a single entry point to perform state/county/city downloads,
choosing either the basic RepeaterBookDownloader (CSV/HTML only) or the
DetailedRepeaterDownloader (with per-repeater detail enrichment).

Public API is additive and does not replace existing functions to preserve
backward compatibility with callers/tests that patch current entry points.
"""
from pathlib import Path
from typing import List, Optional

from .downloader import RepeaterBookDownloader
from .detailed_downloader import DetailedRepeaterDownloader
from .lightweight_data import LightDataFrame


class UnifiedDownloader:
    """Facade for unified download flow.

    Parameters align with existing downloaders to keep ergonomics consistent.
    """

    def __init__(
        self,
        *,
        timeout: int = 30,
        retries: int = 3,
        backoff_factor: float = 0.0,
        # Detailed collection parameters (used only when details=True)
        rate_limit: float = 1.0,
        temp_dir: Optional[Path] = None,
        nohammer: bool = False,
        debug: bool = False,
        rate_jitter: float = 0.0,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.rate_limit = rate_limit
        self.temp_dir = temp_dir
        self.nohammer = nohammer
        self.debug = debug
        self.rate_jitter = rate_jitter

    def download(
        self,
        *,
        level: str,
        state: str,
        country: str = "United States",
        bands: Optional[List[str]] = None,
        county: Optional[str] = None,
        city: Optional[str] = None,
        details: bool = True,
    ) -> LightDataFrame:
        """Perform a download with unified strategy selection.

        Args:
            level: 'state' | 'county' | 'city'
            state: State/province code
            country: Country name
            bands: Band filters
            county/city: location refinement for levels 'county' or 'city'
            details: whether to use the detailed downloader (True) or basic (False)
        """
        if details:
            d = DetailedRepeaterDownloader(
                timeout=self.timeout,
                rate_limit=self.rate_limit,
                temp_dir=str(self.temp_dir) if self.temp_dir else None,
                nohammer=self.nohammer,
                debug=self.debug,
                retries=self.retries,
                retry_backoff=self.backoff_factor,
                rate_jitter=self.rate_jitter,
            )
            if level == "state":
                return d.download_with_details(
                    level="state", state=state, country=country, bands=bands or ["all"]
                )
            if level == "county":
                if not county:
                    raise ValueError("county must be provided for level='county'")
                return d.download_with_details(
                    level="county",
                    state=state,
                    county=county,
                    country=country,
                    bands=bands or ["all"],
                )
            if level == "city":
                if not city:
                    raise ValueError("city must be provided for level='city'")
                return d.download_with_details(
                    level="city",
                    state=state,
                    city=city,
                    country=country,
                    bands=bands or ["all"],
                )
            raise ValueError(f"Unsupported level: {level}")
        else:
            b = RepeaterBookDownloader(
                timeout=self.timeout,
                retries=self.retries,
                backoff_factor=self.backoff_factor,
            )
            if level == "state":
                return b.download_by_state(state, country, bands)
            if level == "county":
                if not county:
                    raise ValueError("county must be provided for level='county'")
                return b.download_by_county(state, county, country, bands)
            if level == "city":
                if not city:
                    raise ValueError("city must be provided for level='city'")
                return b.download_by_city(state, city, country, bands)
            raise ValueError(f"Unsupported level: {level}")


# Convenience wrappers

def unified_download_state(
    state: str,
    *,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    details: bool = True,
    timeout: int = 30,
    retries: int = 3,
    backoff_factor: float = 0.0,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
    rate_jitter: float = 0.0,
) -> LightDataFrame:
    u = UnifiedDownloader(
        timeout=timeout,
        retries=retries,
        backoff_factor=backoff_factor,
        rate_limit=rate_limit,
        temp_dir=temp_dir,
        nohammer=nohammer,
        debug=debug,
        rate_jitter=rate_jitter,
    )
    return u.download(
        level="state",
        state=state,
        country=country,
        bands=bands,
        details=details,
    )


def unified_download_by_county(
    state: str,
    county: str,
    *,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    details: bool = True,
    timeout: int = 30,
    retries: int = 3,
    backoff_factor: float = 0.0,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
    rate_jitter: float = 0.0,
) -> LightDataFrame:
    u = UnifiedDownloader(
        timeout=timeout,
        retries=retries,
        backoff_factor=backoff_factor,
        rate_limit=rate_limit,
        temp_dir=temp_dir,
        nohammer=nohammer,
        debug=debug,
        rate_jitter=rate_jitter,
    )
    return u.download(
        level="county",
        state=state,
        county=county,
        country=country,
        bands=bands,
        details=details,
    )


def unified_download_by_city(
    state: str,
    city: str,
    *,
    country: str = "United States",
    bands: Optional[List[str]] = None,
    details: bool = True,
    timeout: int = 30,
    retries: int = 3,
    backoff_factor: float = 0.0,
    rate_limit: float = 1.0,
    temp_dir: Optional[Path] = None,
    nohammer: bool = False,
    debug: bool = False,
    rate_jitter: float = 0.0,
) -> LightDataFrame:
    u = UnifiedDownloader(
        timeout=timeout,
        retries=retries,
        backoff_factor=backoff_factor,
        rate_limit=rate_limit,
        temp_dir=temp_dir,
        nohammer=nohammer,
        debug=debug,
        rate_jitter=rate_jitter,
    )
    return u.download(
        level="city",
        state=state,
        city=city,
        country=country,
        bands=bands,
        details=details,
    )

