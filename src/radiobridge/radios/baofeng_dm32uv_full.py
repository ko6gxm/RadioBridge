"""Full-field formatter for Baofeng DM-32UV with exact CPS columns and defaults."""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from ..lightweight_data import LightDataFrame, LightSeries, is_null
from .base import BaseRadioFormatter
from .metadata import RadioMetadata


class BaofengDM32UVFullFormatter(BaseRadioFormatter):
    """Formatter for DM-32UV that emits the exact CPS column set and order provided."""

    @property
    def radio_name(self) -> str:
        return "Baofeng DM-32UV (Full)"

    @property
    def description(self) -> str:
        return "DM-32UV dual-band DMR/analog handheld with full CPS export fields"

    @property
    def manufacturer(self) -> str:
        return "Baofeng"

    @property
    def model(self) -> str:
        return "DM-32UV"

    @property
    def metadata(self) -> List[RadioMetadata]:
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="DM-32UV",
                radio_version="Standard",
                firmware_versions=["v.046"],
                cps_versions=[
                    "DM_32UV_CPS_2.08_2.14",
                    "CHIRP_next_20240301_20250401",
                ],
                formatter_key="baofeng-dm32uv-full",
            )
        ]

    @property
    def required_columns(self) -> List[str]:
        return []

    @property
    def output_columns(self) -> List[str]:
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

    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        self.validate_input(data)
        cols = self.output_columns
        out: Dict[str, List[Any]] = {c: [] for c in cols}

        DEFAULTS = {
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
            "TX Contact": "Contacts 1",
            "RX Group List": "None",
            "Color Code": "0",
            "Time Slot": "Slot 1",
            "Encryption": "0",
            "Encryption ID": "None",
            "APRS Report Channel": "1",
            "Direct Dual Mode": "0",
            "Private Confirm": "0",
            "Short Data Confirm": "0",
            "DMR ID": "Radio 1",
            "Scramble": "None",
            "RX Squelch Mode": "Carrier/CTC",
            "Signaling Type": "None",
            "PTT ID": "OFF",
            "VOX Function": "0",
            "PTT ID Display": "0",
        }

        for i in range(len(data)):
            row = data.iloc(i)
            no_val = start_channel + i

            # Channel Name
            name = self.build_channel_name(row, max_length=16, location_slice=8)

            # Frequencies
            rx = self.clean_frequency(self.get_rx_frequency(row))
            if not rx:
                continue
            tx_raw = self.get_tx_frequency(row)
            if tx_raw:
                tx = self.clean_frequency(tx_raw)
            else:
                # Compute from offset if available
                off = self.clean_offset(self.get_offset_value(row))
                if off and off != "0.000000":
                    try:
                        tx = f"{float(rx) + float(off):.6f}"
                    except (ValueError, TypeError):
                        tx = rx
                else:
                    tx = rx

            # Channel Type: Analog if fm_analog truthy; else Digital if dmr truthy; else Analog
            ch_type = self._derive_channel_type(row)

            # Power (keep existing assumption: High)
            power = "High"

            # Bandwidth: Digital -> 12.5KHz, Analog -> 25KHz
            bandwidth = "12.5KHz" if ch_type.lower().startswith("digital") else "25KHz"

            # Tones: if not present, set to "None"
            tone_up, tone_down = self.get_tone_values(row)
            ctc_decode = tone_down if tone_down else "None"
            ctc_encode = tone_up if tone_up else "None"

            # Fill row
            values = {
                "No.": no_val,
                "Channel Name": name,
                "Channel Type": "Digital" if ch_type.lower().startswith("d") else "Analog",
                "RX Frequency[MHz]": rx,
                "TX Frequency[MHz]": tx,
                "Power": power,
                "Band Width": bandwidth,
                "Scan List": DEFAULTS["Scan List"],
                "TX Admit": DEFAULTS["TX Admit"],
                "Emergency System": DEFAULTS["Emergency System"],
                "Squelch Level": DEFAULTS["Squelch Level"],
                "APRS Report Type": DEFAULTS["APRS Report Type"],
                "Forbid TX": DEFAULTS["Forbid TX"],
                "APRS Receive": DEFAULTS["APRS Receive"],
                "Forbid Talkaround": DEFAULTS["Forbid Talkaround"],
                "Auto Scan": DEFAULTS["Auto Scan"],
                "Lone Work": DEFAULTS["Lone Work"],
                "Emergency Indicator": DEFAULTS["Emergency Indicator"],
                "Emergency ACK": DEFAULTS["Emergency ACK"],
                "Analog APRS PTT Mode": DEFAULTS["Analog APRS PTT Mode"],
                "Digital APRS PTT Mode": DEFAULTS["Digital APRS PTT Mode"],
                "TX Contact": DEFAULTS["TX Contact"],
                "RX Group List": DEFAULTS["RX Group List"],
                "Color Code": self._derive_color_code(row, DEFAULTS["Color Code"]),
                "Time Slot": self._derive_slot(row, DEFAULTS["Time Slot"], ch_type),
                "Encryption": DEFAULTS["Encryption"],
                "Encryption ID": DEFAULTS["Encryption ID"],
                "APRS Report Channel": DEFAULTS["APRS Report Channel"],
                "Direct Dual Mode": DEFAULTS["Direct Dual Mode"],
                "Private Confirm": DEFAULTS["Private Confirm"],
                "Short Data Confirm": DEFAULTS["Short Data Confirm"],
                "DMR ID": DEFAULTS["DMR ID"],
                "CTC/DCS Decode": ctc_decode,
                "CTC/DCS Encode": ctc_encode,
                "Scramble": DEFAULTS["Scramble"],
                "RX Squelch Mode": DEFAULTS["RX Squelch Mode"],
                "Signaling Type": DEFAULTS["Signaling Type"],
                "PTT ID": DEFAULTS["PTT ID"],
                "VOX Function": DEFAULTS["VOX Function"],
                "PTT ID Display": DEFAULTS["PTT ID Display"],
            }

            for c in cols:
                out[c].append(values.get(c))

        return self.create_output_dataframe(out)

    # ---------------- helpers -----------------
    def _derive_channel_type(self, row: LightSeries) -> str:
        # Prefer fm_analog when present
        fm = None
        for key in ("fm_analog", "FM_Analog", "fmAnalog"):
            if key in row and not is_null(row[key]):
                fm = str(row[key]).strip().lower()
                break
        if fm is not None:
            if fm in ("1", "true", "yes", "on"):
                return "Analog"
            else:
                return "Digital"
        # Fall back to DMR presence
        for key in ("dmr", "DMR"):
            if key in row and not is_null(row[key]):
                val = str(row[key]).strip().lower()
                if val in ("1", "true", "yes", "on"):
                    return "Digital"
        # Fallback analog
        return "Analog"

    def _derive_color_code(self, row: LightSeries, default_cc: str) -> str:
        for key in ("dmr_color_code", "color_code", "Color Code", "cc"):
            if key in row and not is_null(row[key]):
                v = str(row[key]).strip()
                if v.isdigit():
                    return v
        return default_cc

    def _derive_slot(self, row: LightSeries, default_slot: str, ch_type: str) -> str:
        if not ch_type.lower().startswith("digital"):
            return ""
        for key in ("slot", "Time Slot", "time_slot", "ts"):
            if key in row and not is_null(row[key]):
                v = str(row[key]).strip()
                if v in ("1", "Slot 1", "slot 1"):
                    return "Slot 1"
                if v in ("2", "Slot 2", "slot 2"):
                    return "Slot 2"
        return default_slot
