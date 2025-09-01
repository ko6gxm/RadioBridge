"""Formatter for Baofeng K5 Plus handheld radio."""

from typing import List

import pandas as pd

from .base import BaseRadioFormatter
from .metadata import RadioMetadata


class BaofengK5Formatter(BaseRadioFormatter):
    """Formatter for Baofeng K5 Plus handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng K5 programming software.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng K5 Plus"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Compact dual-band analog handheld radio"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "K5 Plus"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="K5 Plus",
                radio_version="v2.1",
                firmware_versions=["2.1.8", "2.1.7", "2.1.6"],
                cps_versions=["K5-CPS 2.1.8", "CHIRP-next 20240901-20250401"],
                formatter_key="baofeng-k5",
            ),
            RadioMetadata(
                manufacturer="Baofeng",
                model="K5 Plus",
                radio_version="v2.0",
                firmware_versions=["2.0.5", "2.0.4", "2.0.3"],
                cps_versions=["K5-CPS 2.0.5", "CHIRP-next 20240601-20241201"],
                formatter_key="baofeng-k5",
            ),
        ]

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return []  # Accept both basic and detailed downloader formats

    @property
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        return [
            "Channel",
            "Channel Name",
            "RX Frequency",
            "TX Frequency",
            "TX Power",
            "Bandwidth",
            "RX CTCSS/DCS",
            "TX CTCSS/DCS",
            "Busy Lock",
            "Scrambler",
            "Compander",
            "RX Only",
        ]

    def format(self, data: pd.DataFrame, start_channel: int = 1) -> pd.DataFrame:
        """Format repeater data for Baofeng K5 Plus.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)

        Returns:
            Formatted DataFrame ready for K5 Plus programming software
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        formatted_data = []
        channel_names = []  # Collect names for conflict resolution

        for idx, row in data.iterrows():
            channel = idx + start_channel

            # Get RX frequency (works with both basic and detailed downloader)
            rx_freq = self.clean_frequency(self.get_rx_frequency(row))
            if not rx_freq:
                self.logger.debug(f"Skipping row {idx}: no valid frequency found")
                continue

            # Get TX frequency - try detailed downloader first,
            # then calculate from offset
            tx_freq_raw = self.get_tx_frequency(row)
            if tx_freq_raw:
                tx_freq = self.clean_frequency(tx_freq_raw)
            else:
                # Calculate TX frequency from offset (basic downloader)
                offset = self.clean_offset(self.get_offset_value(row))
                if offset and offset != "0.000000":
                    try:
                        rx_float = float(rx_freq)
                        offset_float = float(offset)
                        tx_freq = f"{rx_float + offset_float:.6f}"
                    except (ValueError, TypeError):
                        tx_freq = rx_freq
                else:
                    tx_freq = rx_freq

            # Get tone information (supports both new tone_up/tone_down and
            # legacy tone columns)
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper (CallSign-Location format)
            # K5 has very limited display (12 chars max)
            channel_name = self.build_channel_name(row, max_length=12, location_slice=6)
            if not channel_name:
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Determine power based on frequency band
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF
                tx_power = "High"  # 5W on VHF
            elif 400.0 <= rx_float <= 520.0:  # UHF
                tx_power = "High"  # 4W on UHF
            else:
                tx_power = "Low"

            formatted_row = {
                "Channel": channel,
                "Channel Name": channel_name,
                "RX Frequency": rx_freq,
                "TX Frequency": tx_freq,
                "TX Power": tx_power,
                "Bandwidth": "Wide",  # K5 Plus defaults to wide (25kHz)
                "RX CTCSS/DCS": tone_down if tone_down else "Off",
                "TX CTCSS/DCS": tone_up if tone_up else "Off",
                "Busy Lock": "Off",
                "Scrambler": "Off",
                "Compander": "Off",
                "RX Only": "Off",
            }

            formatted_data.append(formatted_row)
            self.logger.debug(
                f"Formatted channel {channel}: {channel_name} @ {rx_freq}"
            )

        if not formatted_data:
            self.logger.error("No valid repeater data found after formatting")
            raise ValueError("No valid repeater data found after formatting")

        # Resolve channel name conflicts
        resolved_names = self.resolve_channel_name_conflicts(
            channel_names, max_length=12
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Channel Name"] = resolved_name

        result_df = pd.DataFrame(formatted_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
