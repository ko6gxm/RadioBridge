"""Formatter for Baofeng DM-32UV handheld radio."""

from typing import List

import pandas as pd

from .base import BaseRadioFormatter


class BaofengDM32UVFormatter(BaseRadioFormatter):
    """Formatter for Baofeng DM-32UV handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng DM-32UV programming software or CHIRP.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng DM-32UV"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Dual-band DMR/analog handheld with digital and analog modes"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "DM-32UV"

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return ["frequency"]

    @property
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        return [
            "Channel",
            "Channel Name",
            "RX Frequency",
            "TX Frequency",
            "Channel Type",
            "TX Power",
            "Bandwidth",
            "RX CTCSS/DCS",
            "TX CTCSS/DCS",
            "Contact",
            "Contact Call Type",
            "Radio ID",
            "Busy Lock/TX Permit",
            "Squelch Mode",
            "Color Code",
            "Time Slot",
            "Scan List",
            "Group List",
        ]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format repeater data for Baofeng DM-32UV.

        Args:
            data: Input DataFrame with repeater information

        Returns:
            Formatted DataFrame ready for DM-32UV programming software
        """
        self.validate_input(data)

        formatted_data = []

        for idx, row in data.iterrows():
            channel = idx + 1

            rx_freq = self.clean_frequency(row.get("frequency"))
            if not rx_freq:
                continue

            # Calculate TX frequency from offset
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

            # Get tone information
            tone = self.clean_tone(row.get("tone"))

            # Generate channel name
            location = row.get("location", row.get("city", ""))
            callsign = row.get("callsign", "")

            if location and callsign:
                channel_name = (
                    f"{location[:8]} {callsign}"  # DM-32UV has limited display
                )
            elif location:
                channel_name = str(location)[:16]
            elif callsign:
                channel_name = str(callsign)
            else:
                channel_name = f"CH{channel:03d}"

            # Limit name for DM-32UV display
            channel_name = channel_name[:16]

            # Determine channel type - DM-32UV supports both analog and digital
            # Default to analog for repeater data, but could be enhanced to detect DMR
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF
                channel_type = "A-Analog"  # Could also be "D-Digital" for DMR
            elif 400.0 <= rx_float <= 520.0:  # UHF
                channel_type = "A-Analog"  # Could also be "D-Digital" for DMR
            else:
                channel_type = "A-Analog"

            formatted_row = {
                "Channel": channel,
                "Channel Name": channel_name,
                "RX Frequency": rx_freq,
                "TX Frequency": tx_freq,
                "Channel Type": channel_type,
                "TX Power": "High",  # DM-32UV: High (5W) or Low (1W)
                "Bandwidth": "25K",  # 25kHz for analog, 12.5kHz also supported
                "RX CTCSS/DCS": tone if tone else "Off",
                "TX CTCSS/DCS": tone if tone else "Off",
                "Contact": "None",  # For DMR contacts
                "Contact Call Type": "Group Call",
                "Radio ID": "None",  # DMR radio ID
                "Busy Lock/TX Permit": "Always",
                "Squelch Mode": "Carrier",
                "Color Code": "1",  # DMR color code (0-15)
                "Time Slot": "1",  # DMR time slot (1 or 2)
                "Scan List": "None",
                "Group List": "None",  # DMR group list
            }

            formatted_data.append(formatted_row)

        if not formatted_data:
            raise ValueError("No valid repeater data found after formatting")

        return pd.DataFrame(formatted_data)
