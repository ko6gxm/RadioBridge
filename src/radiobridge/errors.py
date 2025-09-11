"""Common exception types for RadioBridge.

These errors provide clearer semantics for callers while maintaining
backward compatibility with tests that expect ValueError in some parse
failure scenarios. Parse-related errors subclass ValueError.
"""

from typing import Optional


class RadioBridgeError(Exception):
    """Base class for all RadioBridge errors."""


class DownloaderError(RadioBridgeError):
    """Base class for downloader-specific errors."""


class HTTPRequestError(DownloaderError):
    """Raised when an HTTP request fails irrecoverably."""

    def __init__(self, message: str, *, url: Optional[str] = None, status: Optional[int] = None):
        self.url = url
        self.status = status
        super().__init__(message)


class ParseError(DownloaderError, ValueError):
    """Raised when parsing downloaded content fails.

    Subclasses ValueError to remain compatible with callers/tests
    that catch ValueError for parsing problems.
    """


class NoRepeaterTableError(ParseError):
    """Raised when no suitable repeater table is found in the HTML page."""


class NoValidFrequencyDataError(ParseError):
    """Raised when no valid numeric frequency values are present after parsing/cleaning."""
