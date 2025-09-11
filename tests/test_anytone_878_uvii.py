from radiobridge.lightweight_data import LightDataFrame
from radiobridge.radios.anytone_878_uvii import Anytone878UVIIFormatter

def test_anytone_878_uvii_headers_and_defaults():
    formatter = Anytone878UVIIFormatter()
    # Verify headers match exactly
    expected = formatter.output_columns

    # Minimal input row (analog)
    df = LightDataFrame.from_records([
        {
            "frequency": "146.520",
            "fm_analog": "1",
            "callsign": "W1ABC",
            "nearest_city": "Concord",
        }
    ])

    out = formatter.format(df, start_channel=10)

    # Headers
    assert out.columns == expected

    # Basic field checks
    r0 = out.iloc(0)
    assert r0["No."] == 10  # start_channel respected
    assert r0["Channel Name"]
    assert r0["Receive Frequency"] == "146.520000"
    assert r0["Transmit Frequency"] == "146.520000"  # simplex default
    assert r0["Channel Type"].startswith("A-")
    assert r0["Transmit Power"] == "Turbo"
    assert r0["Band Width"] == "25K"
    assert r0["CTCSS/DCS Decode"] in ("Off", None, "")
    assert r0["CTCSS/DCS Encode"] in ("Off", None, "")

    # Default long-tail
    assert r0["Contact"] == "Contact 1"
    assert r0["Contact Call Type"] == "Group Call"
    assert r0["Radio ID"]  # defaults to env or KO6GXM

