"""RepeaterBook JSON API provider.

This module integrates the documented JSON API endpoint to fetch repeater
listings in a structured way, with resilient HTTP handling using typed
RadioBridge errors and optional rate limiting with jitter.

Notes:
- Endpoint: https://www.repeaterbook.com/api/export.php (subject to change).
- Terms: Personal use only without explicit permission; attribution required.
- Rate limiting: honor 429 responses and Retry-After.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import time
import random
from typing import Any, Dict, List, Optional, Tuple

import requests

from radiobridge.errors import HTTPRequestError, ParseError
from radiobridge.lightweight_data import LightDataFrame
from radiobridge.logging_config import get_logger


DEFAULT_TIMEOUT = 20
API_BASE_URL = "https://www.repeaterbook.com/api/export.php"


@dataclass
class APIConfig:
    base_url: str = API_BASE_URL
    retries: int = 3
    retry_backoff: float = 1.5
    rate_jitter: float = 0.5
    timeout: int = DEFAULT_TIMEOUT
    contact_email: Optional[str] = None
    api_key: Optional[str] = None


class RepeaterBookAPIProvider:
    """Thin client around the RepeaterBook JSON API."""

    def __init__(
        self,
        *,
        base_url: str = API_BASE_URL,
        retries: int = 3,
        retry_backoff: float = 1.5,
        rate_jitter: float = 0.5,
        timeout: int = DEFAULT_TIMEOUT,
        contact_email: Optional[str] = None,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url
        self.retries = max(0, int(retries))
        self.retry_backoff = float(retry_backoff)
        self.rate_jitter = max(0.0, float(rate_jitter))
        self.timeout = int(timeout)
        self.contact_email = contact_email or os.getenv("RADIOBRIDGE_RB_CONTACT_EMAIL")
        self.api_key = api_key or os.getenv("RADIOBRIDGE_RB_API_KEY")
        self.session = session or requests.Session()
        self.logger = get_logger(__name__)
        # Identify ourselves politely
        self.session.headers.update(
            {
                "User-Agent": "RadioBridge (+https://github.com/ko6gxm/RadioBridge)",
                "Accept": "application/json",
            }
        )

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {}
        if self.contact_email:
            # The docs request that email be included; header name is not strictly specified
            h["X-Contact-Email"] = self.contact_email
        if self.api_key:
            # Placeholder until official header is confirmed
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _sleep_with_jitter(self, base: float) -> None:
        if base <= 0 and self.rate_jitter <= 0:
            return
        jitter = random.uniform(-self.rate_jitter, self.rate_jitter) if self.rate_jitter > 0 else 0.0
        time.sleep(max(0.0, base + jitter))

    def fetch(self, params: Dict[str, Any]) -> LightDataFrame:
        """Fetch repeater listings from the API and return as LightDataFrame.

        Params should be constructed by the caller according to API docs. Typical keys
        include: country, state, county, city, band.
        """
        # Compose request
        headers = self._headers()
        delay = 0.0

        for attempt in range(self.retries + 1):
            if delay > 0.0:
                self._sleep_with_jitter(delay)

            try:
                self.logger.debug(
                    f"API GET {self.base_url}",
                    extra={"params": params, "timeout": self.timeout},
                )
                start = time.time()
                resp = self.session.get(
                    self.base_url, params=params, headers=headers, timeout=self.timeout
                )
                elapsed = time.time() - start
                self.logger.debug(
                    "API response",
                    extra={
                        "status": resp.status_code,
                        "content_type": resp.headers.get("content-type"),
                        "elapsed_s": f"{elapsed:.3f}",
                    },
                )
            except requests.RequestException as e:
                if attempt < self.retries:
                    delay = max(1.0, self.retry_backoff * (attempt + 1))
                    continue
                raise HTTPRequestError(f"API request failed: {e}") from e

            # Handle rate limiting
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        delay = max(2.0, self.retry_backoff * (attempt + 1))
                else:
                    delay = max(2.0, self.retry_backoff * (attempt + 1))
                if attempt < self.retries:
                    continue
                raise HTTPRequestError("Rate limited (429) after retries; please slow down.")

            # Retry certain server errors
            if 500 <= resp.status_code < 600:
                if attempt < self.retries:
                    delay = max(1.0, self.retry_backoff * (attempt + 1))
                    continue
                raise HTTPRequestError(
                    f"Server error {resp.status_code}; exhausted retries.",
                )

            if resp.status_code != 200:
                raise HTTPRequestError(
                    f"HTTP {resp.status_code} from API; params={params}",
                    url=self.base_url,
                    status=resp.status_code,
                )

            # Parse JSON
            try:
                payload = resp.json()
            except ValueError as e:
                raise ParseError("Response was not valid JSON") from e

            # Accept either a top-level list or an object with 'results'
            if isinstance(payload, list):
                rows = payload
            elif isinstance(payload, dict):
                rows = payload.get("results") or payload.get("data") or []
            else:
                raise ParseError("Unexpected JSON structure from API")

            if not isinstance(rows, list):
                raise ParseError("Unexpected JSON structure (results not a list)")

            # Convert to LightDataFrame directly
            return LightDataFrame.from_records(rows)

        # Should not be reachable
        raise HTTPRequestError("Exhausted retries without a successful response")
