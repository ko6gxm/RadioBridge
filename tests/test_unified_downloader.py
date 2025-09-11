"""Tests for UnifiedDownloader facade."""

from pathlib import Path
from unittest.mock import Mock, patch

from radiobridge.unified_downloader import (
    UnifiedDownloader,
    unified_download_state,
    unified_download_by_county,
    unified_download_by_city,
)
from radiobridge.lightweight_data import LightDataFrame


def test_unified_details_true_uses_detailed_downloader():
    with patch("radiobridge.unified_downloader.DetailedRepeaterDownloader") as mock_d:
        mock_inst = Mock()
        mock_inst.download_with_details.return_value = LightDataFrame({"frequency": ["146.520"]})
        mock_d.return_value = mock_inst

        df = unified_download_state(
            "CA",
            details=True,
            rate_limit=1.2,
            retries=2,
            backoff_factor=0.1,
            rate_jitter=0.05,
        )
        assert len(df) == 1
        mock_d.assert_called_once()
        # Ensure details path call
        mock_inst.download_with_details.assert_called_once()


def test_unified_details_false_uses_basic_downloader():
    with patch("radiobridge.unified_downloader.RepeaterBookDownloader") as mock_b:
        mock_inst = Mock()
        mock_inst.download_by_state.return_value = LightDataFrame({"frequency": ["146.520"]})
        mock_b.return_value = mock_inst

        # Create a new instance explicitly
        u = UnifiedDownloader(timeout=30, retries=0, backoff_factor=0.0)
        df = u.download(level="state", state="CA", details=False)
        assert len(df) == 1
        mock_b.assert_called_once()
        mock_inst.download_by_state.assert_called_once_with("CA", "United States", None)

