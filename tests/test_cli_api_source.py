from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from radiobridge.cli import main
from radiobridge.lightweight_data import LightDataFrame


def test_cli_download_with_api_source_uses_provider_and_writes_csv(tmp_path):
    runner = CliRunner()

    sample = LightDataFrame({
        "frequency": ["146.520"],
        "callsign": ["W6ABC"],
    })

    mock_instance = Mock()
    mock_instance.fetch.return_value = sample

    with patch("radiobridge.providers.RepeaterBookAPIProvider", return_value=mock_instance) as mock_cls:
        with patch("radiobridge.cli.write_csv_with_comments") as mock_write:
            result = runner.invoke(
                main,
                [
                    "download",
                    "--state", "CA",
                    "--source", "api",
                    "--contact-email", "me@example.com",
                    "--band", "2m",
                    "--output", str(tmp_path / "out.csv"),
                ],
            )

    assert result.exit_code == 0
    mock_cls.assert_called_once()
    mock_instance.fetch.assert_called_once()
    # Ensure CSV writer called and metadata includes download_type 'api'
    args, kwargs = mock_write.call_args
    assert "comments" in kwargs
    comments = kwargs["comments"]
    assert comments.get("download_type") == "api"
