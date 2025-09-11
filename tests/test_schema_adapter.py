import pytest

from radiobridge.lightweight_data import LightDataFrame
from radiobridge.schema_adapter import normalize_for_formatting


def test_normalize_for_formatting_api_columns_mapping():
    # Sample API-style input
    df = LightDataFrame.from_records([
        {
            "frequency": "146.520",
            "input_freq": "147.120",
            "pl": "123.0",
            "nearest_city": "Concord",
            "county": "Contra Costa",
            "callsign": "W6ABC",
        },
        {
            "frequency": "444.100",
            "input_freq": "449.100",
            "tsq": "100.0",
            "county": "Contra Costa",
            "callsign": "N6XYZ",
        },
    ])

    meta = {"download_type": "api"}
    out = normalize_for_formatting(df, meta)

    # Columns created
    assert "Uplink" in out.columns
    assert "Offset" in out.columns
    assert "tone_up" in out.columns
    assert "tone_down" in out.columns
    assert "Location" in out.columns
    assert "city" in out.columns

    # Row 0
    assert out.iloc(0)["Uplink"] == "147.120"
    assert out.iloc(0)["Offset"] == "+0.600000"
    assert out.iloc(0)["tone_up"] == "123.0"
    assert out.iloc(0)["tone_down"] in (None, "")  # not duplicated
    assert out.iloc(0)["Location"] == "Concord"

    # Row 1
    assert out.iloc(1)["Uplink"] == "449.100"
    assert out.iloc(1)["Offset"] == "+5.000000"
    assert out.iloc(1)["tone_up"] in (None, "")
    assert out.iloc(1)["tone_down"] == "100.0"
    assert out.iloc(1)["Location"] == "Contra Costa"

