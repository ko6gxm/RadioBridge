"""Formatter for Baofeng DM-32UV handheld radio."""

from typing import Dict, List, Optional

import pandas as pd

from .base import BaseRadioFormatter
from .metadata import RadioMetadata


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
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="DM-32UV",
                radio_version="v2",
                firmware_versions=["2.14", "2.13"],
                cps_versions=["2.14", "CHIRP 20241201"],
                formatter_key="baofeng-dm32uv",
            ),
            RadioMetadata(
                manufacturer="Baofeng",
                model="DM-32UV",
                radio_version="v1",
                firmware_versions=["2.10", "2.09"],
                cps_versions=["2.10", "CHIRP 20240901"],
                formatter_key="baofeng-dm32uv",
            ),
        ]

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        # Accept both basic downloader format (frequency) and detailed format (Downlink)
        # The formatter will handle both formats
        return []

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

    def format(self, data: pd.DataFrame, start_channel: int = 1) -> pd.DataFrame:
        """Format repeater data for Baofeng DM-32UV.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)

        Returns:
            Formatted DataFrame ready for DM-32UV programming software
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        formatted_data = []
        channel_names = []  # Collect names for conflict resolution

        # First pass: collect all data and generate initial channel names
        for idx, row in data.iterrows():
            channel = idx + start_channel

            # Map download data fields to radio fields
            # Detailed downloader: Downlink -> RX Frequency[MHz]
            # Basic downloader: frequency -> RX Frequency[MHz]
            rx_freq = self._get_rx_frequency(row)
            if not rx_freq:
                self.logger.debug(f"Skipping row {idx}: no valid RX frequency found")
                continue

            # Map download data fields to radio fields
            # Detailed downloader: Uplink -> TX Frequency[MHz]
            # Basic downloader: calculated from frequency + offset
            tx_freq = self._get_tx_frequency(row, rx_freq)

            # Map tone fields: Uplink Tone -> encode, Downlink Tone -> decode
            tone_up, tone_down = self._get_tone_values(row)

            # Generate channel name using base class helper
            channel_name = self.build_channel_name(row, max_length=16, location_slice=8)
            if not channel_name:
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Map DMR field: detailed downloader provides DMR column directly
            is_dmr = self._is_dmr_repeater(row)

            # Set channel type
            channel_type = "Digital" if is_dmr else "Analog"

            # Set bandwidth based on mode
            bandwidth = "12.5KHz" if is_dmr else "25KHz"

            # Set power level
            power = "High"  # Default to High (5W), could be "Low" (1W)

            # Format tone values for CTC/DCS fields
            # Use tone_down for decode (receive) and tone_up for encode (transmit)
            ctc_decode = tone_down if tone_down else "None"
            ctc_encode = tone_up if tone_up else "None"

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
                "Color Code": self._get_color_code(row, is_dmr),
                "Time Slot": "Slot 1" if is_dmr else "Slot 1",
                "Encryption": "0",
                "Encryption ID": "None",
                "APRS Report Channel": "1",
                "Direct Dual Mode": "0",
                "Private Confirm": "0",
                "Short Data Confirm": "0",
                "DMR ID": self._get_dmr_id(row),
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

    def format_zones(
        self,
        formatted_data: pd.DataFrame,
        csv_metadata: Optional[Dict[str, str]] = None,
        zone_strategy: str = "location",
        max_zones: int = 250,
        max_channels_per_zone: int = 64,
    ) -> pd.DataFrame:
        """Format zone data for Baofeng DM-32UV.

        Creates zones in the format: No., Zone Name, Channel Members
        where Channel Members are pipe-separated channel names.

        Args:
            formatted_data: DataFrame with formatted channel information
            csv_metadata: Metadata from CSV comments (contains county, state, city, etc.)
            zone_strategy: Strategy for creating zones ('location', 'band', 'service')
            max_zones: Maximum number of zones to create
            max_channels_per_zone: Maximum channels per zone

        Returns:
            Formatted DataFrame with zone information
        """
        self.logger.info(f"Creating zones using strategy: {zone_strategy}")

        zones_data = []
        zone_num = 1  # Start at 1 as expected by radio

        if zone_strategy == "location":
            # Get zone name from CSV metadata
            zone_name = self._get_zone_name_from_metadata(
                csv_metadata, zone_strategy, max_length=16
            )

            # Collect all channel names
            channel_names = []
            for _, row in formatted_data.iterrows():
                channel_name = row.get("Channel Name", f"CH{row.get('No.', 0)}")
                channel_names.append(str(channel_name))

            # Split into groups if too many channels
            if len(channel_names) <= max_channels_per_zone:
                # Single zone
                channel_members = "|".join(channel_names)
                zones_data.append(
                    {
                        "No.": zone_num,
                        "Zone Name": zone_name,
                        "Channel Members": channel_members,
                    }
                )
            else:
                # Multiple zones
                for i in range(0, len(channel_names), max_channels_per_zone):
                    if zone_num > max_zones:
                        break

                    group_channels = channel_names[i : i + max_channels_per_zone]
                    group_name = f"{zone_name}{zone_num}"  # e.g., "Riverside CA1", "Riverside CA2"
                    channel_members = "|".join(group_channels)

                    zones_data.append(
                        {
                            "No.": zone_num,
                            "Zone Name": group_name[:16],  # Truncate to 16 chars
                            "Channel Members": channel_members,
                        }
                    )
                    zone_num += 1

        elif zone_strategy == "band":
            # Group by frequency band
            vhf_channels = []
            uhf_channels = []

            for _, row in formatted_data.iterrows():
                channel_name = row.get("Channel Name", f"CH{row.get('No.', 0)}")
                rx_freq_str = row.get("RX Frequency[MHz]", "0")

                try:
                    freq = float(rx_freq_str)
                    if 136.0 <= freq <= 174.0:  # VHF
                        vhf_channels.append(str(channel_name))
                    elif 400.0 <= freq <= 520.0:  # UHF
                        uhf_channels.append(str(channel_name))
                except (ValueError, TypeError):
                    pass

            # Create VHF zone
            if vhf_channels and zone_num <= max_zones:
                channel_members = "|".join(vhf_channels[:max_channels_per_zone])
                zones_data.append(
                    {
                        "No.": zone_num,
                        "Zone Name": "VHF",
                        "Channel Members": channel_members,
                    }
                )
                zone_num += 1

            # Create UHF zone
            if uhf_channels and zone_num <= max_zones:
                channel_members = "|".join(uhf_channels[:max_channels_per_zone])
                zones_data.append(
                    {
                        "No.": zone_num,
                        "Zone Name": "UHF",
                        "Channel Members": channel_members,
                    }
                )
                zone_num += 1

        else:
            # Default: create single zone with all channels
            zone_name = self._get_zone_name_from_metadata(
                csv_metadata, "location", max_length=16
            )
            # Don't use "All Channels" - keep the location-based name
            if zone_name == "Unknown":
                zone_name = "Mixed"

            channel_names = []
            for _, row in formatted_data.iterrows():
                channel_name = row.get("Channel Name", f"CH{row.get('No.', 0)}")
                channel_names.append(str(channel_name))

            channel_members = "|".join(channel_names[:max_channels_per_zone])
            zones_data.append(
                {
                    "No.": zone_num,
                    "Zone Name": zone_name[:16],
                    "Channel Members": channel_members,
                }
            )

        if not zones_data:
            # Fallback: create default zone
            zones_data.append({"No.": 1, "Zone Name": "Default", "Channel Members": ""})

        result_df = pd.DataFrame(zones_data)
        self.logger.info(
            f"Created {len(result_df)} zones using {zone_strategy} strategy"
        )
        return result_df

    def _get_rx_frequency(self, row: pd.Series) -> Optional[str]:
        """Get RX frequency from row data, handling both basic and detailed formats.

        Args:
            row: Row data from DataFrame

        Returns:
            Cleaned RX frequency string or None if invalid
        """
        # Try detailed downloader format first: Downlink -> RX Frequency[MHz]
        if (
            "Downlink" in row
            and pd.notna(row["Downlink"])
            and str(row["Downlink"]).strip()
        ):
            return self.clean_frequency(row["Downlink"])

        # Try basic downloader format: frequency -> RX Frequency[MHz]
        if (
            "frequency" in row
            and pd.notna(row["frequency"])
            and str(row["frequency"]).strip()
        ):
            return self.clean_frequency(row["frequency"])

        # Try alternative column names
        for col in ["rx_freq", "receive_frequency", "downlink_freq"]:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                return self.clean_frequency(row[col])

        return None

    def _get_tx_frequency(self, row: pd.Series, rx_freq: str) -> str:
        """Get TX frequency from row data, handling both basic and detailed formats.

        Args:
            row: Row data from DataFrame
            rx_freq: RX frequency for fallback calculation

        Returns:
            TX frequency string
        """
        # Try detailed downloader format first: Uplink -> TX Frequency[MHz]
        if "Uplink" in row and pd.notna(row["Uplink"]) and str(row["Uplink"]).strip():
            tx_freq = self.clean_frequency(row["Uplink"])
            if tx_freq:
                return tx_freq

        # Try direct TX frequency fields
        for col in ["tx_freq", "transmit_frequency", "uplink_freq"]:
            if col in row and pd.notna(row[col]) and str(row[col]).strip():
                tx_freq = self.clean_frequency(row[col])
                if tx_freq:
                    return tx_freq

        # Calculate from offset (basic downloader format or detailed format with Offset)
        offset = None
        if "Offset" in row and pd.notna(row["Offset"]) and str(row["Offset"]).strip():
            offset = self.clean_offset(row["Offset"])
        elif "offset" in row and pd.notna(row["offset"]) and str(row["offset"]).strip():
            offset = self.clean_offset(row["offset"])

        if offset and offset != "0.000000":
            try:
                rx_float = float(rx_freq)
                offset_float = float(offset)
                return f"{rx_float + offset_float:.5f}"
            except (ValueError, TypeError):
                pass

        # Fallback: same as RX frequency (simplex)
        return rx_freq

    def _get_tone_values(self, row: pd.Series) -> tuple[Optional[str], Optional[str]]:
        """Get tone values from row data, handling both basic and detailed formats.

        Args:
            row: Row data from DataFrame

        Returns:
            Tuple of (tone_up/encode, tone_down/decode)
        """
        # Try detailed downloader format first
        tone_up = None
        tone_down = None

        # Uplink Tone -> encode (TX tone)
        if (
            "Uplink Tone" in row
            and pd.notna(row["Uplink Tone"])
            and str(row["Uplink Tone"]).strip()
        ):
            tone_up = self.clean_tone(row["Uplink Tone"])
        elif (
            "tone_up" in row
            and pd.notna(row["tone_up"])
            and str(row["tone_up"]).strip()
        ):
            tone_up = self.clean_tone(row["tone_up"])

        # Downlink Tone -> decode (RX tone)
        if (
            "Downlink Tone" in row
            and pd.notna(row["Downlink Tone"])
            and str(row["Downlink Tone"]).strip()
        ):
            tone_down = self.clean_tone(row["Downlink Tone"])
        elif (
            "tone_down" in row
            and pd.notna(row["tone_down"])
            and str(row["tone_down"]).strip()
        ):
            tone_down = self.clean_tone(row["tone_down"])

        # Fallback to legacy single tone field (use for both encode and decode)
        if not tone_up and not tone_down:
            if "tone" in row and pd.notna(row["tone"]) and str(row["tone"]).strip():
                legacy_tone = self.clean_tone(row["tone"])
                if legacy_tone:
                    tone_up = tone_down = legacy_tone

        return tone_up, tone_down

    def _is_dmr_repeater(self, row: pd.Series) -> bool:
        """Determine if this is a DMR repeater from row data.

        Args:
            row: Row data from DataFrame

        Returns:
            True if this appears to be a DMR repeater
        """
        # Check detailed downloader DMR field first
        if "DMR" in row and pd.notna(row["DMR"]):
            dmr_value = str(row["DMR"]).lower().strip()
            return dmr_value in ["true", "1", "yes", "on"]

        # Check for Color Code (DMR indicator)
        if "Color Code" in row and pd.notna(row["Color Code"]):
            try:
                color_code = int(str(row["Color Code"]).strip())
                return 0 <= color_code <= 15
            except (ValueError, TypeError):
                pass

        # Check for DMR ID
        if "DMR ID" in row and pd.notna(row["DMR ID"]):
            dmr_id = str(row["DMR ID"]).strip()
            return dmr_id.isdigit() and len(dmr_id) >= 3

        # Check legacy fields for DMR indicators
        for field in ["mode", "type", "service"]:
            if field in row and pd.notna(row[field]):
                field_value = str(row[field]).lower()
                if any(
                    keyword in field_value for keyword in ["dmr", "digital", "mototrbo"]
                ):
                    return True

        return False

    def _get_color_code(self, row: pd.Series, is_dmr: bool) -> str:
        """Get DMR color code from row data.

        Args:
            row: Row data from DataFrame
            is_dmr: Whether this is a DMR repeater

        Returns:
            Color code string
        """
        if not is_dmr:
            return "0"

        # Try detailed downloader Color Code field
        if "Color Code" in row and pd.notna(row["Color Code"]):
            try:
                color_code = int(str(row["Color Code"]).strip())
                if 0 <= color_code <= 15:
                    return str(color_code)
            except (ValueError, TypeError):
                pass

        # Try alternative field names
        for col in ["color_code", "cc", "dmr_color_code"]:
            if col in row and pd.notna(row[col]):
                try:
                    color_code = int(str(row[col]).strip())
                    if 0 <= color_code <= 15:
                        return str(color_code)
                except (ValueError, TypeError):
                    pass

        # Default color code for DMR
        return "1"

    def _get_dmr_id(self, row: pd.Series) -> str:
        """Get DMR ID from row data.

        Args:
            row: Row data from DataFrame

        Returns:
            DMR ID string or 'None'
        """
        # Try detailed downloader DMR ID field
        if "DMR ID" in row and pd.notna(row["DMR ID"]):
            dmr_id = str(row["DMR ID"]).strip()
            if dmr_id.isdigit() and len(dmr_id) >= 3:
                return dmr_id

        # Try alternative field names
        for col in ["dmr_id", "radio_id", "id"]:
            if col in row and pd.notna(row[col]):
                dmr_id = str(row[col]).strip()
                if dmr_id.isdigit() and len(dmr_id) >= 3:
                    return dmr_id

        # Try to use callsign as fallback (not ideal but sometimes used)
        callsign = self.get_callsign(row)
        if callsign and callsign != "None":
            return callsign

        return "None"
