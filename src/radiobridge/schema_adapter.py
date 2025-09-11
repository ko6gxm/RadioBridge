"""Schema adapter for formatting: normalize disparate source columns to canonical fields.

This module transforms downloaded repeater data (from scraping, CSV export, or
the RepeaterBook JSON API) into a canonical schema that all radio formatters
can consume reliably without mutating or removing the original columns.

Key canonical fields created (if missing):
- Uplink: TX frequency in MHz (string), derived from API input_freq
- Offset: Signed MHz offset string like "+0.600000" or "-5.000000"
- tone_up: TX/encode tone (CTCSS) from API 'pl'. Only set when provided
- tone_down: RX/decode tone (CTCSS) from API 'tsq'. Only set when provided
- Location: Derived from nearest_city, then county as fallback
- city: Mirrored from nearest_city if absent

Notes on tones (per user guidance):
- If only a single uplink or downlink tone is supplied, do NOT duplicate it
  into both tone_up and tone_down. Preserve only what is provided.

The adapter returns a new LightDataFrame instance that includes the original
columns plus any canonical columns added.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .lightweight_data import LightDataFrame, is_null


def _as_float(val: Any) -> Optional[float]:
    if is_null(val):
        return None
    try:
        s = str(val).strip()
        if not s:
            return None
        # Remove common suffixes
        s = s.replace(" MHz", "").replace("MHz", "")
        return float(s)
    except Exception:
        return None


def _format_offset(diff_mhz: Optional[float]) -> Optional[str]:
    if diff_mhz is None:
        return None
    # Include sign for non-zero
    if diff_mhz == 0.0:
        return f"{0.0:.6f}"
    return f"{diff_mhz:+.6f}"


def normalize_for_formatting(
    data: LightDataFrame, csv_metadata: Optional[Dict[str, str]] = None
) -> LightDataFrame:
    """Return a new LightDataFrame with canonical fields added.

    Args:
        data: Source LightDataFrame from rb download
        csv_metadata: Parsed comments from CSV (may include download_type)

    Returns:
        LightDataFrame with original columns plus canonical fields.
    """
    if data.empty:
        return data

    # Copy existing data to avoid mutating original in-place
    new_data: Dict[str, List[Any]] = {k: v[:] for k, v in data._data.items()}
    columns = list(data.columns)

    # Heuristics for API-style input
    is_api = False
    if csv_metadata and str(csv_metadata.get("download_type", "")).lower() == "api":
        is_api = True
    else:
        # Detect by presence of API-specific fields
        for key in ("rptr_id", "input_freq", "pl", "tsq", "nearest_city"):
            if key in data._data:
                is_api = True
                break

    # Prepare per-row derived columns
    need_uplink = "Uplink" not in new_data
    need_offset = "Offset" not in new_data and "offset" not in new_data
    need_tone_up = "tone_up" not in new_data
    need_tone_down = "tone_down" not in new_data
    need_location = "Location" not in new_data and "location" not in new_data
    need_city = "city" not in new_data

    uplink_vals: List[Optional[str]] = [] if need_uplink else None
    offset_vals: List[Optional[str]] = [] if need_offset else None
    tone_up_vals: List[Optional[str]] = [] if need_tone_up else None
    tone_down_vals: List[Optional[str]] = [] if need_tone_down else None
    location_vals: List[Optional[str]] = [] if need_location else None
    city_vals: List[Optional[str]] = [] if need_city else None

    # Gather row-wise values
    for i in range(len(data)):
        # Accessors
        def get(col: str) -> Any:
            return data._data.get(col, [None] * len(data))[i]

        freq = get("frequency")
        in_freq = get("input_freq") if is_api else None
        if in_freq is None:
            # Tolerate alternative cased names
            in_freq = get("Input_Freq")
        # Derive Uplink
        if uplink_vals is not None:
            uplink_val = None
            if not is_null(in_freq):
                uplink_val = str(in_freq).strip()
            elif not is_null(get("tx_frequency")):
                uplink_val = str(get("tx_frequency")).strip()
            elif not is_null(get("tx_freq")):
                uplink_val = str(get("tx_freq")).strip()
            # Save value (may be None)
            uplink_vals.append(uplink_val)

        # Derive Offset (signed)
        if offset_vals is not None:
            rx_f = _as_float(freq)
            tx_f = _as_float(in_freq)
            if tx_f is None:
                tx_f = _as_float(get("tx_frequency")) or _as_float(get("tx_freq"))
            diff = None
            if rx_f is not None and tx_f is not None:
                diff = tx_f - rx_f
            offset_vals.append(_format_offset(diff) if diff is not None else None)

        # Derive tone_up and tone_down per user rule (do not duplicate single tones)
        if tone_up_vals is not None:
            pl_val = get("pl")
            if is_null(pl_val):
                # Tolerate alternative cases/names
                pl_val = get("PL")
            tone_up_vals.append(None if is_null(pl_val) else str(pl_val).strip())
        if tone_down_vals is not None:
            tsq_val = get("tsq")
            if is_null(tsq_val):
                tsq_val = get("TSQL") or get("tsql")
            tone_down_vals.append(None if is_null(tsq_val) else str(tsq_val).strip())

        # Location and city fields
        if location_vals is not None or city_vals is not None:
            nearest_city = get("nearest_city")
            county = get("county")
            loc = None
            if not is_null(nearest_city):
                loc = str(nearest_city).strip()
            elif not is_null(county):
                loc = str(county).strip()
            if location_vals is not None:
                location_vals.append(loc)
            if city_vals is not None:
                if not is_null(nearest_city):
                    city_vals.append(str(nearest_city).strip())
                else:
                    city_vals.append(None)

    # Attach derived columns if needed
    if uplink_vals is not None:
        new_data["Uplink"] = uplink_vals
        if "Uplink" not in columns:
            columns.append("Uplink")
    if offset_vals is not None:
        new_data["Offset"] = offset_vals
        if "Offset" not in columns:
            columns.append("Offset")
    if tone_up_vals is not None:
        new_data["tone_up"] = tone_up_vals
        if "tone_up" not in columns:
            columns.append("tone_up")
    if tone_down_vals is not None:
        new_data["tone_down"] = tone_down_vals
        if "tone_down" not in columns:
            columns.append("tone_down")
    if location_vals is not None:
        new_data["Location"] = location_vals
        if "Location" not in columns:
            columns.append("Location")
    if city_vals is not None:
        new_data["city"] = city_vals
        if "city" not in columns:
            columns.append("city")

    return LightDataFrame(new_data, columns)
