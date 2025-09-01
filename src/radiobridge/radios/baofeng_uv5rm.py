"""Formatter for Baofeng UV-5RM handheld radio."""

from typing import List, Optional

import pandas as pd

from .base import BaseRadioFormatter
from .metadata import RadioMetadata


class BaofengUV5RMFormatter(BaseRadioFormatter):
    """Formatter for Baofeng UV-5RM handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng UV-5RM programming software or CHIRP.

    The UV-5RM is an enhanced version of the UV-5R with additional memory channels
    and improved features, supporting VHF (136-174 MHz) and UHF (400-520 MHz) bands.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng UV-5RM"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Enhanced UV-5R with additional memory channels and improved features"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "UV-5RM"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="UV-5RM",
                radio_version="Standard",
                firmware_versions=[
                    "UV5RM-298",
                    "UV5RM-297",
                    "UV5RM-296",
                    "BFB298-RM",
                    "BFB297-RM",
                    "BFB296-RM",
                    "N5RM-298",
                    "N5RM-297",
                ],
                cps_versions=[
                    "CHIRP_next_20240301_20250401",
                    "RT_Systems_UV5RM_1.0_2.3",
                    "Baofeng_UV5RM_CPS_1.0_2.0",
                    "BaoFeng_CPS_5.5_6.8",
                ],
                formatter_key="baofeng-uv5rm",
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
            "Location",
            "Name",
            "Frequency",
            "Duplex",
            "Offset",
            "Tone",
            "rToneFreq",
            "cToneFreq",
            "DtcsCode",
            "DtcsPolarity",
            "Mode",
            "TStep",
            "Skip",
            "Comment",
            "URCALL",
            "RPT1CALL",
            "RPT2CALL",
            "DVCODE",
        ]

    def format(
        self,
        data: pd.DataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> pd.DataFrame:
        """Format repeater data for Baofeng UV-5RM.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)
            cps_version: CPS version to optimize output for (optional)

        Returns:
            Formatted DataFrame ready for UV-5RM programming software
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        if cps_version:
            self.logger.info(f"Optimizing output for CPS version: {cps_version}")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        # CPS-specific optimizations
        use_chirp_format = cps_version and "chirp" in cps_version.lower()
        if use_chirp_format:
            self.logger.debug("Using CHIRP-optimized formatting")

        use_rt_systems = cps_version and "rt_systems" in cps_version.lower()
        if use_rt_systems:
            self.logger.debug("Using RT Systems-optimized formatting")

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
            offset_mhz = "0.000000"
            duplex = ""

            if tx_freq_raw:
                tx_freq = self.clean_frequency(tx_freq_raw)
                # Calculate offset and duplex
                try:
                    rx_float = float(rx_freq)
                    tx_float = float(tx_freq)
                    offset_val = tx_float - rx_float

                    if abs(offset_val) < 0.001:  # Simplex
                        duplex = ""
                        offset_mhz = "0.000000"
                    elif offset_val > 0:  # Positive offset
                        duplex = "+"
                        offset_mhz = f"{offset_val:.6f}"
                    else:  # Negative offset
                        duplex = "-"
                        offset_mhz = f"{abs(offset_val):.6f}"

                except (ValueError, TypeError):
                    duplex = ""
                    offset_mhz = "0.000000"
            else:
                # Calculate TX frequency from offset (basic downloader)
                offset = self.clean_offset(self.get_offset_value(row))
                if offset and offset != "0.000000":
                    try:
                        offset_float = float(offset)
                        if abs(offset_float) >= 0.001:
                            if offset_float > 0:
                                duplex = "+"
                            else:
                                duplex = "-"
                            offset_mhz = f"{abs(offset_float):.6f}"
                        else:
                            duplex = ""
                            offset_mhz = "0.000000"
                    except (ValueError, TypeError):
                        duplex = ""
                        offset_mhz = "0.000000"
                else:
                    duplex = ""
                    offset_mhz = "0.000000"

            # Get tone information (supports both new tone_up/tone_down and
            # legacy tone columns)
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper
            # UV-5RM has similar display to UV-5R (8 chars max)
            channel_name = self.build_channel_name(row, max_length=8, location_slice=4)
            if not channel_name:
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Format tone values for UV-5RM format
            tone_mode = "None"
            rtone_freq = "88.5"
            ctone_freq = "88.5"
            dtcs_code = "023"
            dtcs_pol = "NN"

            if tone_down or tone_up:
                if tone_down and tone_down.replace(".", "").isdigit():
                    # CTCSS tone
                    tone_mode = "Tone"
                    rtone_freq = tone_down
                    if tone_up and tone_up.replace(".", "").isdigit():
                        ctone_freq = tone_up
                    else:
                        ctone_freq = tone_down
                elif tone_down and tone_down.startswith("D"):
                    # DCS tone
                    tone_mode = "DTCS"
                    dtcs_code = tone_down[1:] if len(tone_down) > 1 else "023"

            # Determine frequency step based on frequency
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF
                tstep = "5.00"
            elif 400.0 <= rx_float <= 520.0:  # UHF
                tstep = "12.50"
            else:
                tstep = "5.00"

            formatted_row = {
                "Location": channel,
                "Name": channel_name,
                "Frequency": rx_freq,
                "Duplex": duplex,
                "Offset": offset_mhz,
                "Tone": tone_mode,
                "rToneFreq": rtone_freq,
                "cToneFreq": ctone_freq,
                "DtcsCode": dtcs_code,
                "DtcsPolarity": dtcs_pol,
                "Mode": "FM",  # UV-5RM only supports FM
                "TStep": tstep,
                "Skip": "",
                "Comment": "",
                "URCALL": "",
                "RPT1CALL": "",
                "RPT2CALL": "",
                "DVCODE": "",
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
            channel_names, max_length=8
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Name"] = resolved_name

        result_df = pd.DataFrame(formatted_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
