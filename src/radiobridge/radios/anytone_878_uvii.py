"""Formatter for Anytone AT-D878UV II (UVII full field set)."""
from __future__ import annotations

import os
from typing import List, Optional, Any, Dict

from ..lightweight_data import LightDataFrame, LightSeries, is_null
from .base import BaseRadioFormatter
from .metadata import RadioMetadata


class Anytone878UVIIFormatter(BaseRadioFormatter):
    """Formatter for Anytone AT-D878UV II with full UVII column set.

    Outputs exactly the column headers and order provided by the user for
    CPS import, filling unspecified fields with sensible defaults.
    """

    @property
    def radio_name(self) -> str:
        return "Anytone AT-D878UV II (UVII Full)"

    @property
    def description(self) -> str:
        return "Dual-band DMR/Analog handheld (UVII) with full CPS field export"

    @property
    def manufacturer(self) -> str:
        return "Anytone"

    @property
    def model(self) -> str:
        return "AT-D878UV II"

    @property
    def metadata(self) -> List[RadioMetadata]:
        return [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II Plus",
                radio_version="Plus",
                firmware_versions=["3.08", "4.00"],
                cps_versions=["Anytone_CPS_3.00_4.00"],
                formatter_key="anytone-878-uvii",
            )
        ]

    @property
    def required_columns(self) -> List[str]:
        # Accept flexible input; schema_adapter already normalizes key fields
        return []

    @property
    def output_columns(self) -> List[str]:
        # Exact order as specified by the user
        return [
            "No.",
            "Channel Name",
            "Receive Frequency",
            "Transmit Frequency",
            "Channel Type",
            "Transmit Power",
            "Band Width",
            "CTCSS/DCS Decode",
            "CTCSS/DCS Encode",
            "Contact",
            "Contact Call Type",
            "Contact TG/DMR ID",
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
            "Receive Group List",
            "PTT Prohibit",
            "Reverse",
            "Simplex TDMA",
            "Slot Suit",
            "AES Digital Encryption",
            "Digital Encryption",
            "Call Confirmation",
            "Talk Around(Simplex)",
            "Work Alone",
            "Custom CTCSS",
            "2TONE Decode",
            "Ranging",
            "Through Mode",
            "APRS RX",
            "Analog APRS PTT Mode",
            "Digital APRS PTT Mode",
            "APRS Report Type",
            "Digital APRS Report Channel",
            "Correct Frequency[Hz]",
            "SMS Confirmation",
            "Exclude channel from roaming",
            "DMR MODE",
            "DataACK Disable",
            "R5toneBot",
            "R5ToneEot",
            "Auto Scan",
            "Ana Aprs Mute",
            "Send Talker Alias",
            "AnaAprsTxPath",
            "ARC4",
            "ex_emg_kind",
        ]

    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        # Assume input already normalized by schema_adapter in CLI
        self.validate_input(data)
        rows: List[Dict[str, Any]] = []
        # Prepare column-oriented output to preserve exact header order
        cols = self.output_columns
        out_cols: Dict[str, List[Any]] = {c: [] for c in cols}

        # Defaults provided by user
        DEFAULTS = {
            "Contact": "Contact 1",
            "Contact Call Type": "Group Call",
            "Radio ID": os.getenv("RADIOBRIDGE_USER_CALLSIGN", "KO6GXM"),
            "Busy Lock/TX Permit": "Off",
            "Squelch Mode": "Carrier",
            "Optional Signal": "Off",
            "DTMF ID": "1",
            "2Tone ID": "1",
            "5Tone ID": "1",
            "PTT ID": "Off",
            "Scan List": "None",
            "Receive Group List": "None",
            "PTT Prohibit": "Off",
            "Reverse": "Off",
            "Simplex TDMA": "Off",
            "Slot Suit": "Off",
            "AES Digital Encryption": "Normal Encryption",
            "Digital Encryption": "Off",
            "Call Confirmation": "Off",
            "Talk Around(Simplex)": "Off",
            "Work Alone": "Off",
            "Custom CTCSS": "251.1",
            "2TONE Decode": "1",
            "Ranging": "Off",
            "Through Mode": "On",
            "APRS RX": "Off",
            "Analog APRS PTT Mode": "Off",
            "Digital APRS PTT Mode": "Off",
            "APRS Report Type": "Off",
            "Digital APRS Report Channel": "1",
            "Correct Frequency[Hz]": "0",
            "SMS Confirmation": "Off",
            "Exclude channel from roaming": "0",
            "DMR MODE": "0",
            "DataACK Disable": "0",
            "R5toneBot": "0",
            "R5ToneEot": "0",
            "Auto Scan": "0",
            "Ana Aprs Mute": "0",
            "Send Talker Alias": "0",
            "AnaAprsTxPath": "0",
            "ARC4": "0",
            "ex_emg_kind": "0",
        }

        for idx in range(len(data)):
            row = data.iloc(idx)
            no_val = start_channel + idx  # Respect starting channel number

            rx = self.clean_frequency(self.get_rx_frequency(row))
            if not rx:
                continue

            # TX from canonical Uplink/Offset logic via get_tx_frequency fallback
            tx_raw = self.get_tx_frequency(row)
            if tx_raw:
                tx = self.clean_frequency(tx_raw)
            else:
                # Fallback: compute from offset if available
                offset = self.clean_offset(self.get_offset_value(row))
                if offset and offset != "0.000000":
                    try:
                        rx_float = float(rx)
                        off_float = float(offset)
                        tx = f"{rx_float + off_float:.6f}"
                    except (ValueError, TypeError):
                        tx = rx
                else:
                    tx = rx

            # Channel Name using helper; 16 chars is common for handheld CPS
            name = self.build_channel_name(row, max_length=16, location_slice=8)

            # Channel Type from API fm_analog if available, else infer from DMR flags
            ch_type = self._derive_channel_type(row)

            # Power defaults to Turbo per user
            power = "Turbo"

            # Band Width: analog 25K, digital 12.5K (typical). Can be adjusted
            bandwidth = "25K" if ch_type.startswith("A") else "12.5K"

            tone_up, tone_down = self.get_tone_values(row)
            ctc_decode = tone_down if tone_down else "Off"
            ctc_encode = tone_up if tone_up else "Off"

            color_code = self._derive_color_code(row)
            slot = self._derive_slot(row, ch_type)

            out_row: Dict[str, Any] = {
                "No.": no_val,
                "Channel Name": name,
                "Receive Frequency": rx,
                "Transmit Frequency": tx,
                "Channel Type": ch_type,
                "Transmit Power": power,
                "Band Width": bandwidth,
                "CTCSS/DCS Decode": ctc_decode,
                "CTCSS/DCS Encode": ctc_encode,
                "Contact": DEFAULTS["Contact"],
                "Contact Call Type": DEFAULTS["Contact Call Type"],
                "Contact TG/DMR ID": "",
                "Radio ID": DEFAULTS["Radio ID"],
                "Busy Lock/TX Permit": DEFAULTS["Busy Lock/TX Permit"],
                "Squelch Mode": DEFAULTS["Squelch Mode"],
                "Optional Signal": DEFAULTS["Optional Signal"],
                "DTMF ID": DEFAULTS["DTMF ID"],
                "2Tone ID": DEFAULTS["2Tone ID"],
                "5Tone ID": DEFAULTS["5Tone ID"],
                "PTT ID": DEFAULTS["PTT ID"],
                "Color Code": color_code,
                "Slot": slot,
                "Scan List": DEFAULTS["Scan List"],
                "Receive Group List": DEFAULTS["Receive Group List"],
                "PTT Prohibit": DEFAULTS["PTT Prohibit"],
                "Reverse": DEFAULTS["Reverse"],
                "Simplex TDMA": DEFAULTS["Simplex TDMA"],
                "Slot Suit": DEFAULTS["Slot Suit"],
                "AES Digital Encryption": DEFAULTS["AES Digital Encryption"],
                "Digital Encryption": DEFAULTS["Digital Encryption"],
                "Call Confirmation": DEFAULTS["Call Confirmation"],
                "Talk Around(Simplex)": DEFAULTS["Talk Around(Simplex)"],
                "Work Alone": DEFAULTS["Work Alone"],
                "Custom CTCSS": DEFAULTS["Custom CTCSS"],
                "2TONE Decode": DEFAULTS["2TONE Decode"],
                "Ranging": DEFAULTS["Ranging"],
                "Through Mode": DEFAULTS["Through Mode"],
                "APRS RX": DEFAULTS["APRS RX"],
                "Analog APRS PTT Mode": DEFAULTS["Analog APRS PTT Mode"],
                "Digital APRS PTT Mode": DEFAULTS["Digital APRS PTT Mode"],
                "APRS Report Type": DEFAULTS["APRS Report Type"],
                "Digital APRS Report Channel": DEFAULTS["Digital APRS Report Channel"],
                "Correct Frequency[Hz]": DEFAULTS["Correct Frequency[Hz]"],
                "SMS Confirmation": DEFAULTS["SMS Confirmation"],
                "Exclude channel from roaming": DEFAULTS["Exclude channel from roaming"],
                "DMR MODE": DEFAULTS["DMR MODE"],
                "DataACK Disable": DEFAULTS["DataACK Disable"],
                "R5toneBot": DEFAULTS["R5toneBot"],
                "R5ToneEot": DEFAULTS["R5ToneEot"],
                "Auto Scan": DEFAULTS["Auto Scan"],
                "Ana Aprs Mute": DEFAULTS["Ana Aprs Mute"],
                "Send Talker Alias": DEFAULTS["Send Talker Alias"],
                "AnaAprsTxPath": DEFAULTS["AnaAprsTxPath"],
                "ARC4": DEFAULTS["ARC4"],
                "ex_emg_kind": DEFAULTS["ex_emg_kind"],
            }

            # Append in exact column order
            for c in cols:
                out_cols[c].append(out_row.get(c))

        return self.create_output_dataframe(out_cols)

    # ----------------- helpers -----------------
    def _derive_channel_type(self, row: LightSeries) -> str:
        # Use fm_analog if present; otherwise infer
        fm_analog = None
        for key in ("fm_analog", "FM_Analog", "fmAnalog"):
            if key in row and not is_null(row[key]):
                fm_analog = str(row[key]).strip().lower()
                break
        if fm_analog is not None:
            if fm_analog in ("1", "true", "yes", "on"):  # Analog
                return "A-Analog"
            # Otherwise assume non-analog; prefer digital if flagged
        # Check DMR flag
        dmr = None
        for key in ("dmr", "DMR"):
            if key in row and not is_null(row[key]):
                dmr = str(row[key]).strip().lower()
                break
        if dmr in ("1", "true", "yes", "on"):
            return "D-Digital"
        # Fallback analog
        return "A-Analog"

    def _derive_color_code(self, row: LightSeries) -> str:
        # Try several columns
        for key in ("dmr_color_code", "Color Code", "color_code", "cc"):
            if key in row and not is_null(row[key]):
                val = str(row[key]).strip()
                if val.isdigit():
                    return val
        return "1"  # default

    def _derive_slot(self, row: LightSeries, ch_type: str) -> str:
        if not ch_type.startswith("D"):
            return ""  # analog has no slot
        # Try to find slot info
        for key in ("slot", "Time Slot", "time_slot", "ts"):
            if key in row and not is_null(row[key]):
                v = str(row[key]).strip()
                if v in ("1", "Slot 1", "slot 1"):
                    return "Slot 1"
                if v in ("2", "Slot 2", "slot 2"):
                    return "Slot 2"
        # Default
        return "Slot 1"
