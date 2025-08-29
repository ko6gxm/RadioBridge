"""Formatter for Baofeng DN32UV handheld radio."""

from typing import List

import pandas as pd

from .base import BaseRadioFormatter


class BaofengDN32UVFormatter(BaseRadioFormatter):
    """Formatter for Baofeng DN32UV handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng programming software (CHIRP or similar).
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng DN32UV"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Dual-band analog handheld with programmable memories"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "DN32UV"

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return ["frequency"]

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

    def format(self, data: pd.DataFrame) -> pd.DataFrame:
        """Format repeater data for Baofeng DN32UV.

        Args:
            data: Input DataFrame with repeater information

        Returns:
            Formatted DataFrame ready for CHIRP or other programming software
        """
        self.validate_input(data)

        formatted_data = []

        for idx, row in data.iterrows():
            location = idx + 1  # Memory location/channel number

            frequency = self.clean_frequency(row.get("frequency"))
            if not frequency:
                continue

            # Determine duplex mode from offset
            offset_str = self.clean_offset(row.get("offset", 0))
            if offset_str and offset_str != "0.000000":
                try:
                    offset_float = float(offset_str)
                    if offset_float > 0:
                        duplex = "+"
                    elif offset_float < 0:
                        duplex = "-"
                        offset_str = str(abs(offset_float))  # Make positive for CHIRP
                    else:
                        duplex = ""
                        offset_str = ""
                except (ValueError, TypeError):
                    duplex = ""
                    offset_str = ""
            else:
                duplex = ""
                offset_str = ""

            # Get tone information
            tone = self.clean_tone(row.get("tone"))
            if tone:
                tone_mode = "Tone"
                rtone_freq = tone
                ctone_freq = tone
            else:
                tone_mode = ""
                rtone_freq = ""
                ctone_freq = ""

            # Generate name from available data
            location_name = row.get("location", row.get("city", ""))
            callsign = row.get("callsign", "")

            if location_name and callsign:
                name = (
                    f"{location_name[:8]} {callsign}"  # Baofeng has limited name length
                )
            elif location_name:
                name = str(location_name)[:16]
            elif callsign:
                name = str(callsign)
            else:
                name = f"MEM{location:03d}"

            # Limit name length for Baofeng
            name = name[:16]

            formatted_row = {
                "Location": location,
                "Name": name,
                "Frequency": frequency,
                "Duplex": duplex,
                "Offset": offset_str if offset_str else "",
                "Tone": tone_mode,
                "rToneFreq": rtone_freq,
                "cToneFreq": ctone_freq,
                "DtcsCode": "023",  # Default DTCS code
                "DtcsPolarity": "NN",
                "Mode": "FM",  # Baofeng radios are FM only
                "TStep": "5.00",  # Default step size
                "Skip": "",
                "Comment": row.get("use", ""),
                "URCALL": "",
                "RPT1CALL": "",
                "RPT2CALL": "",
                "DVCODE": "",
            }

            formatted_data.append(formatted_row)

        if not formatted_data:
            raise ValueError("No valid repeater data found after formatting")

        return pd.DataFrame(formatted_data)
