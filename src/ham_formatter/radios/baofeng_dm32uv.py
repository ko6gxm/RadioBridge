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
            "No.",
            "Channel Name",
            "Channel Type",
            "RX Frequency[MHz]",
            "TX Frequency[MHz]",
            "Power",
            "Band Width",
            "Scan List",
            "TX Admit",
            "Emergency System",
            "Squelch Level",
            "APRS Report Type",
            "Forbid TX",
            "APRS Receive",
            "Forbid Talkaround",
            "Auto Scan",
            "Lone Work",
            "Emergency Indicator",
            "Emergency ACK",
            "Analog APRS PTT Mode",
            "Digital APRS PTT Mode",
            "TX Contact",
            "RX Group List",
            "Color Code",
            "Time Slot",
            "Encryption",
            "Encryption ID",
            "APRS Report Channel",
            "Direct Dual Mode",
            "Private Confirm",
            "Short Data Confirm",
            "DMR ID",
            "CTC/DCS Decode",
            "CTC/DCS Encode",
            "Scramble",
            "RX Squelch Mode",
            "Signaling Type",
            "PTT ID",
            "VOX Function",
            "PTT ID Display",
        ]

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format repeater data for Baofeng DM-32UV.

        Args:
            data: Input DataFrame with repeater information

        Returns:
            Formatted DataFrame ready for DM-32UV programming software
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        formatted_data = []

        for idx, row in data.iterrows():
            channel = idx + 1

            rx_freq = self.clean_frequency(row.get("frequency"))
            if not rx_freq:
                self.logger.debug(
                    f"Skipping row {idx}: invalid frequency {row.get('frequency')}"
                )
                continue

            # Calculate TX frequency from offset
            offset = self.clean_offset(row.get("offset", 0))
            if offset and offset != "0.000000":
                try:
                    rx_float = float(rx_freq)
                    offset_float = float(offset)
                    tx_freq = f"{rx_float + offset_float:.5f}"
                except (ValueError, TypeError):
                    tx_freq = rx_freq
            else:
                tx_freq = rx_freq

            # Get tone information
            tone = self.clean_tone(row.get("tone"))

            # Generate channel name
            location = row.get("location", row.get("city", ""))
            callsign = row.get("callsign", row.get("call", ""))

            if location and callsign:
                # Keep it short for DM-32UV display
                channel_name = f"{location[:8]}-{callsign}"
            elif location:
                channel_name = str(location)[:16]
            elif callsign:
                channel_name = str(callsign)[:16]
            else:
                channel_name = f"CH{channel:03d}"

            # Limit name for DM-32UV display (16 chars max)
            channel_name = channel_name[:16]

            # Determine if this is a digital repeater (DMR)
            # Check for DMR indicators in the data
            is_dmr = False
            for field in ["mode", "type", "service"]:
                field_value = str(row.get(field, "")).lower()
                if any(
                    keyword in field_value
                    for keyword in ["dmr", "digital", "d-star", "fusion"]
                ):
                    is_dmr = True
                    break

            # Set channel type
            channel_type = "Digital" if is_dmr else "Analog"

            # Set bandwidth based on mode
            bandwidth = "12.5KHz" if is_dmr else "25KHz"

            # Set power level
            power = "High"  # Default to High (5W), could be "Low" (1W)

            # Format tone values for CTC/DCS fields
            if tone:
                ctc_decode = tone
                ctc_encode = tone
            else:
                ctc_decode = "None"
                ctc_encode = "None"

            formatted_row = {
                "No.": channel,
                "Channel Name": channel_name,
                "Channel Type": channel_type,
                "RX Frequency[MHz]": rx_freq,
                "TX Frequency[MHz]": tx_freq,
                "Power": power,
                "Band Width": bandwidth,
                "Scan List": "None",
                "TX Admit": "Allow TX",
                "Emergency System": "None",
                "Squelch Level": "3",
                "APRS Report Type": "Off",
                "Forbid TX": "0",
                "APRS Receive": "0",
                "Forbid Talkaround": "0",
                "Auto Scan": "0",
                "Lone Work": "0",
                "Emergency Indicator": "0",
                "Emergency ACK": "0",
                "Analog APRS PTT Mode": "0",
                "Digital APRS PTT Mode": "0",
                "TX Contact": "None" if not is_dmr else "None",
                "RX Group List": "None" if not is_dmr else "None",
                "Color Code": "1" if is_dmr else "0",
                "Time Slot": "Slot 1" if is_dmr else "Slot 1",
                "Encryption": "0",
                "Encryption ID": "None",
                "APRS Report Channel": "1",
                "Direct Dual Mode": "0",
                "Private Confirm": "0",
                "Short Data Confirm": "0",
                "DMR ID": callsign if callsign else "None",
                "CTC/DCS Decode": ctc_decode,
                "CTC/DCS Encode": ctc_encode,
                "Scramble": "None",
                "RX Squelch Mode": "Carrier/CTC",
                "Signaling Type": "None",
                "PTT ID": "OFF",
                "VOX Function": "0",
                "PTT ID Display": "0",
            }

            formatted_data.append(formatted_row)
            self.logger.debug(
                f"Formatted channel {channel}: {channel_name} @ {rx_freq} "
                f"({channel_type})"
            )

        if not formatted_data:
            self.logger.error("No valid repeater data found after formatting")
            raise ValueError("No valid repeater data found after formatting")

        result_df = pd.DataFrame(formatted_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
