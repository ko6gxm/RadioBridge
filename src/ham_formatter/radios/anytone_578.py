"""Formatter for Anytone AT-D578UV III (Plus) mobile radio."""

from typing import List

import pandas as pd

from .base import BaseRadioFormatter


class Anytone578Formatter(BaseRadioFormatter):
    """Formatter for Anytone AT-D578UV III (Plus) mobile radio.

    This formatter converts repeater data into the CSV format expected by
    the Anytone CPS (Customer Programming Software) for the mobile radio.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Anytone AT-D578UV III (Plus)"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Dual-band DMR/Analog mobile radio with GPS and APRS"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Anytone"

    @property
    def model(self) -> str:
        """Radio model."""
        return "AT-D578UV III"

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return ["frequency"]

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
            "Roaming",
        ]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format repeater data for Anytone 578.

        Args:
            data: Input DataFrame with repeater information

        Returns:
            Formatted DataFrame ready for Anytone CPS import
        """
        self.validate_input(data)

        formatted_data = []

        for idx, row in data.iterrows():
            channel_num = idx + 1

            rx_freq = self.clean_frequency(row.get("frequency"))
            if not rx_freq:
                continue

            # Calculate TX frequency
            offset = self.clean_offset(row.get("offset", 0))
            if offset and offset != "0.000000":
                try:
                    rx_float = float(rx_freq)
                    offset_float = float(offset)
                    tx_freq = f"{rx_float + offset_float:.6f}"
                except (ValueError, TypeError):
                    tx_freq = rx_freq
            else:
                tx_freq = rx_freq

            tone = self.clean_tone(row.get("tone"))

            # Generate channel name (mobile radios can handle longer names)
            location = row.get("location", row.get("city", row.get("callsign", "")))
            callsign = row.get("callsign", "")

            if location and callsign:
                channel_name = f"{location} ({callsign})"
            elif location:
                channel_name = str(location)
            elif callsign:
                channel_name = str(callsign)
            else:
                channel_name = f"CH{channel_num:03d}"

            # Limit to 20 characters for mobile radio
            channel_name = channel_name[:20]

            formatted_row = {
                "Channel Number": channel_num,
                "Channel Name": channel_name,
                "Receive Frequency": rx_freq,
                "Transmit Frequency": tx_freq,
                "Channel Type": "A-Analog",
                "Power": "High",  # Mobile radios typically high power
                "Band Width": "25K",
                "CTCSS/DCS Decode": tone if tone else "Off",
                "CTCSS/DCS Encode": tone if tone else "Off",
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
                "Roaming": "Off",
            }

            formatted_data.append(formatted_row)

        if not formatted_data:
            raise ValueError("No valid repeater data found after formatting")

        return pd.DataFrame(formatted_data)
