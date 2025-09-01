"""Formatter for Anytone AT-D878UV II (Plus) handheld radio."""

from typing import List

import pandas as pd

from .base import BaseRadioFormatter
from .metadata import RadioMetadata


class Anytone878Formatter(BaseRadioFormatter):
    """Formatter for Anytone AT-D878UV II (Plus) handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Anytone CPS (Customer Programming Software).
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Anytone AT-D878UV II (Plus)"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Dual-band DMR/Analog handheld with GPS and Bluetooth"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Anytone"

    @property
    def model(self) -> str:
        """Radio model."""
        return "AT-D878UV II"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II Plus",
                radio_version="Plus",
                firmware_versions=["1.24", "1.23", "1.22"],
                cps_versions=["1.24", "1.23"],
                formatter_key="anytone-878",
            ),
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II",
                radio_version="Standard",
                firmware_versions=["1.20", "1.19"],
                cps_versions=["1.20", "1.19"],
                formatter_key="anytone-878",
            ),
        ]

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return ["frequency"]  # Minimum required - frequency

    @property
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        return [
            "Channel Number",
            "Channel Name",
            "Receive Frequency",
            "Transmit Frequency",
            "Channel Type",
            "Power",
            "Band Width",
            "CTCSS/DCS Decode",
            "CTCSS/DCS Encode",
            "Contact",
            "Contact Call Type",
            "Radio ID",
            "Busy Lock/TX Permit",
            "Squelch Mode",
            "Optional Signal",
            "DTMF ID",
            "2Tone ID",
            "5Tone ID",
            "PTT ID",
            "Color Code",
            "Slot",
            "Scan List",
            "Group List",
            "GPS System",
        ]

    def format(self, data: pd.DataFrame, start_channel: int = 1) -> pd.DataFrame:
        """Format repeater data for Anytone 878.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)

        Returns:
            Formatted DataFrame ready for Anytone CPS import

        Raises:
            ValueError: If input data is invalid or missing required columns
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        # Create output DataFrame with required structure
        formatted_data = []
        channel_names = []  # Collect names for conflict resolution

        for idx, row in data.iterrows():
            channel_num = idx + start_channel

            # Extract and clean data
            rx_freq = self.clean_frequency(row.get("frequency"))
            if not rx_freq:
                self.logger.debug(
                    f"Skipping row {idx}: invalid frequency {row.get('frequency')}"
                )
                continue  # Skip rows without valid frequency

            # Calculate transmit frequency from offset if available
            offset = self.clean_offset(self.get_offset_value(row))
            if offset and offset != "0.000000":
                try:
                    rx_float = float(rx_freq)
                    offset_float = float(offset)
                    tx_freq = f"{rx_float + offset_float:.6f}"
                except (ValueError, TypeError):
                    tx_freq = rx_freq  # Simplex if offset calculation fails
            else:
                tx_freq = rx_freq  # Simplex

            # Get tone information (supports both new tone_up/tone_down and
            # legacy tone columns)
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper (CallSign-Location format)
            channel_name = self.build_channel_name(row, max_length=16, location_slice=8)
            if not channel_name:
                channel_name = f"CH{channel_num:03d}"

            channel_names.append(channel_name)

            # Determine channel type based on frequency
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF
                channel_type = "A-Analog"
            elif 400.0 <= rx_float <= 520.0:  # UHF
                channel_type = "A-Analog"
            else:
                channel_type = "A-Analog"  # Default to analog

            formatted_row = {
                "Channel Number": channel_num,
                "Channel Name": channel_name,
                "Receive Frequency": rx_freq,
                "Transmit Frequency": tx_freq,
                "Channel Type": channel_type,
                "Power": "High",  # Default to high power
                "Band Width": "25K",  # Default to 25kHz bandwidth
                "CTCSS/DCS Decode": tone_down if tone_down else "Off",
                "CTCSS/DCS Encode": tone_up if tone_up else "Off",
                "Contact": "None",
                "Contact Call Type": "Group Call",
                "Radio ID": "None",
                "Busy Lock/TX Permit": "Always",
                "Squelch Mode": "Carrier",
                "Optional Signal": "Off",
                "DTMF ID": "None",
                "2Tone ID": "None",
                "5Tone ID": "None",
                "PTT ID": "None",
                "Color Code": "1",
                "Slot": "1",
                "Scan List": "None",
                "Group List": "None",
                "GPS System": "GPS",
            }

            formatted_data.append(formatted_row)
            self.logger.debug(
                f"Formatted channel {channel_num}: {channel_name} @ {rx_freq}"
            )

        if not formatted_data:
            self.logger.error("No valid repeater data found after formatting")
            raise ValueError("No valid repeater data found after formatting")

        # Resolve channel name conflicts
        resolved_names = self.resolve_channel_name_conflicts(
            channel_names, max_length=16
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Channel Name"] = resolved_name

        result_df = pd.DataFrame(formatted_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
