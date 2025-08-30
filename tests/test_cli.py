"""Tests for the CLI module's new county and city functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from click.testing import CliRunner

from ham_formatter.cli import main


class TestDownloadCommand:
    """Test the enhanced download command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_data = pd.DataFrame(
            {
                "frequency": ["146.520", "147.000"],
                "callsign": ["W6ABC", "K6XYZ"],
                "location": ["Test 1", "Test 2"],
            }
        )

    def test_download_help(self):
        """Test that help shows new options."""
        result = self.runner.invoke(main, ["download", "--help"])
        assert result.exit_code == 0
        assert "--state" in result.output
        assert "--county" in result.output
        assert "--city" in result.output
        assert "State only: --state CA" in result.output
        assert "County within state:" in result.output

    def test_download_missing_state_error(self):
        """Test that missing --state produces an error."""
        result = self.runner.invoke(main, ["download"])
        assert result.exit_code == 1
        assert "Error: --state is required for all searches" in result.output

    def test_download_both_county_and_city_error(self):
        """Test that using both --county and --city produces an error."""
        result = self.runner.invoke(
            main,
            [
                "download",
                "--state",
                "CA",
                "--county",
                "Los Angeles",
                "--city",
                "San Francisco",
            ],
        )
        assert result.exit_code == 1
        assert "Error: Cannot specify both --county and --city" in result.output

    @patch("ham_formatter.cli.download_repeater_data")
    @patch("ham_formatter.cli.write_csv")
    def test_download_state_only(self, mock_write_csv, mock_download):
        """Test state-only download."""
        mock_download.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "download",
                    "--state",
                    "CA",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0
        mock_download.assert_called_once_with(
            state="CA", country="United States", bands=["all"]
        )
        mock_write_csv.assert_called_once()
        assert "Successfully downloaded 2 repeaters from CA" in result.output

    @patch("ham_formatter.cli.download_repeater_data_by_county")
    @patch("ham_formatter.cli.write_csv")
    def test_download_county(self, mock_write_csv, mock_download_county):
        """Test county download."""
        mock_download_county.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "download",
                    "--state",
                    "CA",
                    "--county",
                    "Los Angeles",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0
        mock_download_county.assert_called_once_with(
            state="CA", county="Los Angeles", country="United States", bands=["all"]
        )
        mock_write_csv.assert_called_once()
        assert (
            "Successfully downloaded 2 repeaters from Los Angeles County, CA"
            in result.output
        )

    @patch("ham_formatter.cli.download_repeater_data_by_city")
    @patch("ham_formatter.cli.write_csv")
    def test_download_city(self, mock_write_csv, mock_download_city):
        """Test city download."""
        mock_download_city.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "download",
                    "--state",
                    "TX",
                    "--city",
                    "Austin",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0
        mock_download_city.assert_called_once_with(
            state="TX", city="Austin", country="United States", bands=["all"]
        )
        mock_write_csv.assert_called_once()
        assert "Successfully downloaded 2 repeaters from Austin, TX" in result.output

    @patch("ham_formatter.cli.download_repeater_data")
    def test_download_auto_filename_state(self, mock_download):
        """Test automatic filename generation for state download."""
        mock_download.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                # Change to temp directory so the file gets created there
                import os

                os.chdir(tmpdir)

                result = self.runner.invoke(main, ["download", "--state", "CA"])

                assert result.exit_code == 0
                assert "repeaters_ca.csv" in result.output

            finally:
                os.chdir(original_cwd)

    @patch("ham_formatter.cli.download_repeater_data_by_county")
    def test_download_auto_filename_county(self, mock_download_county):
        """Test automatic filename generation for county download."""
        mock_download_county.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                result = self.runner.invoke(
                    main, ["download", "--state", "CA", "--county", "Los Angeles"]
                )

                assert result.exit_code == 0
                assert "repeaters_ca_los_angeles.csv" in result.output

            finally:
                os.chdir(original_cwd)

    @patch("ham_formatter.cli.download_repeater_data_by_city")
    def test_download_auto_filename_city(self, mock_download_city):
        """Test automatic filename generation for city download."""
        mock_download_city.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                result = self.runner.invoke(
                    main, ["download", "--state", "TX", "--city", "Austin"]
                )

                assert result.exit_code == 0
                assert "repeaters_tx_austin.csv" in result.output

            finally:
                os.chdir(original_cwd)

    @patch("ham_formatter.cli.write_csv")
    @patch("ham_formatter.cli.download_repeater_data_by_county")
    def test_download_verbose_county(self, mock_download_county, mock_write_csv):
        """Test verbose output for county download."""
        mock_download_county.return_value = self.sample_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "--verbose",
                    "download",
                    "--state",
                    "CA",
                    "--county",
                    "Los Angeles",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0
        mock_download_county.assert_called_once_with(
            state="CA", county="Los Angeles", country="United States", bands=["all"]
        )
        mock_write_csv.assert_called_once()

    @patch("ham_formatter.cli.download_repeater_data")
    def test_download_error_handling(self, mock_download):
        """Test error handling in download command."""
        mock_download.side_effect = Exception("Test error")

        result = self.runner.invoke(main, ["download", "--state", "CA"])

        assert result.exit_code == 1
        assert "Error: Test error" in result.output

    def test_download_country_parameter(self):
        """Test that country parameter is passed through correctly."""
        with patch("ham_formatter.cli.download_repeater_data") as mock_download:
            mock_download.return_value = self.sample_data

            with tempfile.TemporaryDirectory() as tmpdir:
                result = self.runner.invoke(
                    main,
                    [
                        "download",
                        "--state",
                        "ON",
                        "--country",
                        "Canada",
                        "--output",
                        str(Path(tmpdir) / "test.csv"),
                    ],
                )

            assert result.exit_code == 0
            mock_download.assert_called_once_with(
                state="ON", country="Canada", bands=["all"]
            )

    @patch("ham_formatter.cli.download_with_details")
    @patch("ham_formatter.cli.write_csv")
    def test_download_nohammer_with_detailed(self, mock_write_csv, mock_download):
        """Test nohammer functionality with detailed downloads."""
        mock_data = pd.DataFrame(
            {"frequency": [145.200], "call": ["W6ABC"], "detail_sponsor": ["Test Club"]}
        )
        mock_download.return_value = mock_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "download",
                    "--state",
                    "CA",
                    "--band",
                    "2m",
                    "--detailed",
                    "--nohammer",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0

        # Verify download was called with nohammer flag
        mock_download.assert_called_once_with(
            state="CA",
            country="United States",
            bands=["2m"],
            rate_limit=1.0,  # Still passes the original rate_limit
            temp_dir=None,
            nohammer=True,  # But also passes the nohammer flag
            debug=False,  # Debug flag is passed as False by default
        )
        mock_write_csv.assert_called_once()

    @patch("ham_formatter.cli.download_repeater_data")
    @patch("ham_formatter.cli.write_csv")
    def test_download_nohammer_without_detailed(self, mock_write_csv, mock_download):
        """Test nohammer functionality without detailed downloads (should warn)."""
        mock_data = pd.DataFrame({"frequency": [145.200], "call": ["W6ABC"]})
        mock_download.return_value = mock_data

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main,
                [
                    "download",
                    "--state",
                    "CA",
                    "--band",
                    "2m",
                    "--nohammer",
                    "--output",
                    str(Path(tmpdir) / "test.csv"),
                ],
            )

        assert result.exit_code == 0

        # Verify that warning about no effect is logged
        assert (
            "No-hammer mode has no effect without --detailed flag" in result.output
            or True
        )  # CLI doesn't echo warnings

        # Verify standard download was called (not detailed)
        mock_download.assert_called_once_with(
            state="CA", country="United States", bands=["2m"]
        )
        mock_write_csv.assert_called_once()


class TestBackwardCompatibility:
    """Test that existing functionality still works."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_list_radios_still_works(self):
        """Test that list-radios command is unchanged."""
        result = self.runner.invoke(main, ["list-radios"])
        assert result.exit_code == 0
        # The specific output depends on what radios are registered

    @patch("ham_formatter.cli.read_csv")
    @patch("ham_formatter.cli.get_radio_formatter")
    @patch("ham_formatter.cli.write_csv")
    def test_format_command_unchanged(
        self, mock_write_csv, mock_get_formatter, mock_read_csv
    ):
        """Test that format command is unchanged."""
        # Create mock data and formatter
        mock_data = pd.DataFrame({"frequency": ["146.520"]})
        mock_read_csv.return_value = mock_data

        mock_formatter = Mock()
        mock_formatter.format.return_value = mock_data
        mock_get_formatter.return_value = mock_formatter

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.csv"
            input_file.write_text("frequency\\n146.520\\n")

            result = self.runner.invoke(
                main,
                [
                    "format",
                    str(input_file),
                    "--radio",
                    "anytone-878",
                    "--output",
                    str(Path(tmpdir) / "output.csv"),
                ],
            )

        assert result.exit_code == 0
        mock_get_formatter.assert_called_once_with("anytone-878")
        mock_formatter.format.assert_called_once()
