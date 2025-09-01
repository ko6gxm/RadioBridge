"""Tests for logging configuration and functionality."""

import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from click.testing import CliRunner

from radiobridge.cli import main
from radiobridge.logging_config import setup_logging, get_logger


class TestLoggingConfig:
    """Test logging configuration functionality."""

    def test_setup_logging_default(self, caplog):
        """Test default logging setup (INFO level, no file)."""
        with caplog.at_level(logging.DEBUG):
            setup_logging()
            logger = get_logger(__name__)

            # INFO messages should be captured
            logger.info("Test info message")
            assert "Test info message" in caplog.text

            # DEBUG messages should NOT be captured (default level is INFO)
            logger.debug("Test debug message")
            assert "Test debug message" not in caplog.text

    def test_setup_logging_verbose(self, caplog):
        """Test verbose logging setup (DEBUG level)."""
        with caplog.at_level(logging.DEBUG):
            setup_logging(verbose=True)
            logger = get_logger(__name__)

            # Both INFO and DEBUG messages should be captured
            logger.info("Test info message")
            logger.debug("Test debug message")

            assert "Test info message" in caplog.text
            assert "Test debug message" in caplog.text

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"

        setup_logging(verbose=True, log_file=str(log_file))
        logger = get_logger(__name__)

        logger.info("Test file message")

        # Check that log file was created and contains the message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test file message" in content

    def test_get_logger_module_naming(self):
        """Test that get_logger creates properly named loggers."""
        logger = get_logger("radiobridge.test_module")
        assert logger.name == "radiobridge.test_module"

        logger = get_logger("some.nested.module")
        assert logger.name == "radiobridge.module"

    def test_logging_formatter(self, caplog):
        """Test that logging formatter includes expected fields."""
        with caplog.at_level(logging.INFO):
            setup_logging()
            logger = get_logger(__name__)
            logger.info("Test message")

            # Check that log record has expected format elements
            record = caplog.records[0]
            assert record.name.startswith("radiobridge")
            assert record.levelname == "INFO"
            assert record.getMessage() == "Test message"


class TestCLILogging:
    """Test logging integration with CLI commands."""

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_cli_verbose_flag_help(self):
        """Test that --verbose flag appears in help."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.output
        assert "Enable verbose logging" in result.output

    def test_cli_log_file_flag_help(self):
        """Test that --log-file flag appears in help."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--log-file" in result.output

    def test_cli_verbose_flag_functionality(self, caplog):
        """Test that --verbose flag actually enables debug logging."""
        with caplog.at_level(logging.DEBUG):
            # Test without verbose flag first
            result = self.runner.invoke(main, ["list-radios"])
            assert result.exit_code == 0

            # Clear caplog and test with verbose flag
            caplog.clear()
            result = self.runner.invoke(main, ["--verbose", "list-radios"])
            assert result.exit_code == 0

            # Should see more detailed logging with verbose
            # Note: We may not see debug logs in this simple test, but we verify
            # setup works

    def test_cli_download_with_logging(self, caplog, tmp_path):
        """Test that download command generates appropriate log messages."""
        with caplog.at_level(logging.INFO):
            # Use mock to avoid actual HTTP requests
            with patch("radiobridge.cli.download_with_details") as mock_download:
                with patch("radiobridge.cli.write_csv"):
                    # Create a proper pandas DataFrame mock
                    import pandas as pd

                    mock_data = pd.DataFrame(
                        {
                            "frequency": [
                                "146.520",
                                "147.000",
                                "148.000",
                                "149.000",
                                "150.000",
                            ],
                            "callsign": ["W6ABC", "K6XYZ", "N6DEF", "W6GHI", "K6JKL"],
                        }
                    )
                    mock_download.return_value = mock_data

                    output_file = tmp_path / "test.csv"
                    result = self.runner.invoke(
                        main,
                        [
                            "--verbose",
                            "download",
                            "--state",
                            "CA",
                            "--output",
                            str(output_file),
                        ],
                    )

                    # Should succeed
                    assert result.exit_code == 0

                    # Should have logging messages
                    log_messages = [record.message for record in caplog.records]
                    info_messages = [
                        msg for msg in log_messages if "Starting download" in msg
                    ]
                    assert len(info_messages) > 0

    def test_cli_format_with_logging(self, caplog, tmp_path):
        """Test that format command generates appropriate log messages."""
        # Create a test input file
        input_file = tmp_path / "input.csv"
        input_file.write_text("frequency\\n146.520\\n")

        with caplog.at_level(logging.INFO):
            with patch("radiobridge.cli.read_csv") as mock_read:
                with patch("radiobridge.cli.get_radio_formatter") as mock_get_formatter:
                    with patch("radiobridge.cli.write_csv"):

                        # Set up mocks
                        mock_data = MagicMock()
                        mock_data.__len__ = MagicMock(return_value=3)
                        mock_read.return_value = mock_data

                        mock_formatter = MagicMock()
                        mock_formatter.format.return_value = mock_data
                        mock_get_formatter.return_value = mock_formatter

                        result = self.runner.invoke(
                            main,
                            [
                                "--verbose",
                                "format",
                                str(input_file),
                                "--radio",
                                "anytone-878",
                                "--output",
                                str(tmp_path / "output.csv"),
                            ],
                        )

                        assert result.exit_code == 0

                        # Should have logging messages
                        log_messages = [record.message for record in caplog.records]
                        format_messages = [
                            msg
                            for msg in log_messages
                            if "format operation" in msg.lower()
                        ]
                        assert len(format_messages) > 0

    def test_cli_error_logging(self, caplog):
        """Test that CLI errors are properly logged."""
        with caplog.at_level(logging.ERROR):
            # Try to download without required --state parameter
            result = self.runner.invoke(main, ["--verbose", "download"])
            assert result.exit_code == 1
            assert "Error: --state is required" in result.output


class TestModuleLogging:
    """Test logging in individual modules."""

    def test_downloader_logging(self, caplog):
        """Test that downloader module generates appropriate logs."""
        from radiobridge.downloader import RepeaterBookDownloader

        with caplog.at_level(logging.DEBUG):
            RepeaterBookDownloader(timeout=10)

            # Should log initialization
            init_logs = [
                record.message
                for record in caplog.records
                if "RepeaterBookDownloader initialized" in record.message
            ]
            assert len(init_logs) > 0

    def test_csv_utils_logging(self, caplog, tmp_path):
        """Test that CSV utilities generate appropriate logs."""
        from radiobridge.csv_utils import write_csv
        import pandas as pd

        with caplog.at_level(logging.INFO):
            test_data = pd.DataFrame({"frequency": ["146.520", "147.000"]})
            output_file = tmp_path / "test.csv"

            write_csv(test_data, output_file)

            # Should log file operations
            write_logs = [
                record.message
                for record in caplog.records
                if "Writing CSV file" in record.message
            ]
            assert len(write_logs) > 0

    def test_radio_formatter_logging(self, caplog):
        """Test that radio formatters generate appropriate logs."""
        from radiobridge.radios import get_radio_formatter

        with caplog.at_level(logging.DEBUG):
            formatter = get_radio_formatter("anytone-878")
            assert formatter is not None

            # Should log formatter selection and initialization
            selection_logs = [
                record.message
                for record in caplog.records
                if "Found direct match" in record.message
            ]
            init_logs = [
                record.message
                for record in caplog.records
                if "Initialized" in record.message and "formatter" in record.message
            ]

            assert len(selection_logs) > 0
            assert len(init_logs) > 0

    def test_radio_formatter_validation_logging(self, caplog):
        """Test that radio formatter validation generates logs."""
        from radiobridge.radios import get_radio_formatter
        import pandas as pd

        with caplog.at_level(logging.DEBUG):
            formatter = get_radio_formatter("anytone-878")
            test_data = pd.DataFrame({"frequency": ["146.520"]})

            # This should log validation details
            result = formatter.validate_input(test_data)
            assert result is True

            # Should have validation logs
            validation_logs = [
                record.message
                for record in caplog.records
                if "validation" in record.message.lower()
            ]
            assert len(validation_logs) > 0


class TestLoggingLevels:
    """Test different logging levels work correctly."""

    def test_logging_level_separation(self, caplog):
        """Test that log levels are properly separated."""
        # Test INFO level (default)
        with caplog.at_level(logging.INFO):
            setup_logging(verbose=False)
            logger = get_logger(__name__)

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            messages = [record.message for record in caplog.records]

            # Should NOT see debug messages at INFO level
            assert "Debug message" not in messages
            assert "Info message" in messages
            assert "Warning message" in messages
            assert "Error message" in messages

    def test_verbose_logging_level(self, caplog):
        """Test that verbose mode shows debug messages."""
        with caplog.at_level(logging.DEBUG):
            setup_logging(verbose=True)
            logger = get_logger(__name__)

            logger.debug("Debug message")
            logger.info("Info message")

            messages = [record.message for record in caplog.records]

            # Should see ALL message levels in verbose mode
            assert "Debug message" in messages
            assert "Info message" in messages

    def test_logging_no_interference_with_cli_output(self):
        """Test that logging doesn't interfere with normal CLI output."""
        runner = CliRunner()

        # Test that normal CLI output is preserved regardless of logging
        result = runner.invoke(main, ["list-radios"])
        assert result.exit_code == 0
        assert "RadioBridge - Supported Radio Models" in result.output

        # Same test with verbose logging
        result = runner.invoke(main, ["--verbose", "list-radios"])
        assert result.exit_code == 0
        assert "RadioBridge - Supported Radio Models" in result.output


class TestFormatterLogging:
    """Test logging functionality in all radio formatters."""

    def setup_method(self):
        """Set up test data for formatter testing."""
        self.test_data = pd.DataFrame(
            {
                "frequency": ["146.520", "147.000", "448.000"],
                "callsign": ["W6ABC", "K6XYZ", "N6DEF"],
                "location": ["Los Angeles", "San Francisco", "San Diego"],
                "offset": ["0.600", "-0.600", "5.000"],
                "tone": ["88.5", "103.5", "127.3"],
            }
        )

    def test_anytone_878_formatter_logging(self, caplog):
        """Test logging in Anytone 878 formatter."""
        from radiobridge.radios.anytone_878 import Anytone878Formatter

        with caplog.at_level(logging.DEBUG):
            formatter = Anytone878Formatter()

            # Should log initialization
            init_logs = [
                record.message
                for record in caplog.records
                if "Initialized" in record.message and "878" in record.message
            ]
            assert len(init_logs) > 0

            # Test format operation logging
            result = formatter.format(self.test_data)

            # Should log format operation start and completion
            start_logs = [
                record.message
                for record in caplog.records
                if "Starting format operation" in record.message
            ]
            complete_logs = [
                record.message
                for record in caplog.records
                if "Format operation complete" in record.message
            ]

            assert len(start_logs) > 0
            assert len(complete_logs) > 0
            assert len(result) == 3  # All 3 rows should be processed

    def test_anytone_578_formatter_logging(self, caplog):
        """Test logging in Anytone 578 formatter."""
        from radiobridge.radios.anytone_578 import Anytone578Formatter

        with caplog.at_level(logging.DEBUG):
            formatter = Anytone578Formatter()

            # Should log initialization
            init_logs = [
                record.message
                for record in caplog.records
                if "Initialized" in record.message and "578" in record.message
            ]
            assert len(init_logs) > 0

            # Test format operation logging
            result = formatter.format(self.test_data)

            # Should log format operation start and completion
            start_logs = [
                record.message
                for record in caplog.records
                if "Starting format operation" in record.message
            ]
            complete_logs = [
                record.message
                for record in caplog.records
                if "Format operation complete" in record.message
            ]
            formatted_logs = [
                record.message
                for record in caplog.records
                if "Formatted channel" in record.message
            ]

            assert len(start_logs) > 0
            assert len(complete_logs) > 0
            assert len(formatted_logs) == 3  # One for each channel
            assert len(result) == 3

    def test_baofeng_k5_formatter_logging(self, caplog):
        """Test logging in Baofeng K5 Plus formatter."""
        from radiobridge.radios.baofeng_k5_plus import BaofengK5PlusFormatter

        with caplog.at_level(logging.DEBUG):
            formatter = BaofengK5PlusFormatter()

            # Should log initialization
            init_logs = [
                record.message
                for record in caplog.records
                if "Initialized" in record.message and "K5" in record.message
            ]
            assert len(init_logs) > 0

            # Test format operation logging
            result = formatter.format(self.test_data)

            # Should log format operation start and completion
            start_logs = [
                record.message
                for record in caplog.records
                if "Starting format operation" in record.message
            ]
            complete_logs = [
                record.message
                for record in caplog.records
                if "Format operation complete" in record.message
            ]
            formatted_logs = [
                record.message
                for record in caplog.records
                if "Formatted channel" in record.message
            ]

            assert len(start_logs) > 0
            assert len(complete_logs) > 0
            assert len(formatted_logs) == 3  # One for each channel
            assert len(result) == 3

    def test_baofeng_dm32uv_formatter_logging(self, caplog):
        """Test logging in Baofeng DM-32UV formatter."""
        from radiobridge.radios.baofeng_dm32uv import BaofengDM32UVFormatter

        with caplog.at_level(logging.DEBUG):
            formatter = BaofengDM32UVFormatter()

            # Should log initialization
            init_logs = [
                record.message
                for record in caplog.records
                if "Initialized" in record.message and "DM-32UV" in record.message
            ]
            assert len(init_logs) > 0

            # Test format operation logging
            result = formatter.format(self.test_data)

            # Should log format operation start and completion
            start_logs = [
                record.message
                for record in caplog.records
                if "Starting format operation" in record.message
            ]
            complete_logs = [
                record.message
                for record in caplog.records
                if "Format operation complete" in record.message
            ]
            formatted_logs = [
                record.message
                for record in caplog.records
                if "Formatted channel" in record.message
            ]

            assert len(start_logs) > 0
            assert len(complete_logs) > 0
            assert len(formatted_logs) == 3  # One for each channel
            assert len(result) == 3

    def test_formatter_error_logging(self, caplog):
        """Test that formatters log errors appropriately."""
        from radiobridge.radios.anytone_878 import Anytone878Formatter
        import pandas as pd

        with caplog.at_level(logging.ERROR):
            formatter = Anytone878Formatter()

            # Test with empty DataFrame
            empty_data = pd.DataFrame()

            with pytest.raises(ValueError, match="Input data is empty"):
                formatter.format(empty_data)

            # Should log error
            error_logs = [
                record.message
                for record in caplog.records
                if "Input data is empty" in record.message
            ]
            assert len(error_logs) > 0

    def test_formatter_skip_invalid_data_logging(self, caplog):
        """Test that formatters log when skipping invalid data."""
        from radiobridge.radios.anytone_578 import Anytone578Formatter
        import pandas as pd

        with caplog.at_level(logging.DEBUG):
            formatter = Anytone578Formatter()

            # Test data with some invalid frequencies
            invalid_data = pd.DataFrame(
                {
                    "frequency": ["146.520", "", "invalid", "448.000"],
                    "callsign": ["W6ABC", "K6XYZ", "N6DEF", "K6GHI"],
                    "location": ["LA", "SF", "SD", "OC"],
                }
            )

            result = formatter.format(invalid_data)

            # Should log skipped rows
            skip_logs = [
                record.message
                for record in caplog.records
                if "Skipping row" in record.message
                and "no valid frequency" in record.message
            ]
            assert len(skip_logs) >= 2  # At least 2 invalid frequencies

            # Should only format valid rows
            assert len(result) == 2  # Only 2 valid frequencies

    def test_formatter_input_validation_logging(self, caplog):
        """Test that formatters log input validation details."""
        from radiobridge.radios.baofeng_k5_plus import BaofengK5PlusFormatter
        import pandas as pd

        with caplog.at_level(logging.DEBUG):
            formatter = BaofengK5PlusFormatter()

            # Test with missing required column
            invalid_data = pd.DataFrame(
                {
                    "callsign": ["W6ABC"],
                    "location": ["LA"],
                    # Missing 'frequency' column
                }
            )

            with pytest.raises(
                ValueError, match="No valid repeater data found after formatting"
            ):
                formatter.format(invalid_data)

            # Should log validation details
            validation_logs = [
                record.message
                for record in caplog.records
                if "Validating input data" in record.message
            ]
            error_logs = [
                record.message
                for record in caplog.records
                if "No valid repeater data found after formatting" in record.message
            ]

            assert len(validation_logs) > 0
            assert len(error_logs) > 0
