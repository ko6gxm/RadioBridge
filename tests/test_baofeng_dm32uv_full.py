from radiobridge.lightweight_data import LightDataFrame
from radiobridge.radios.baofeng_dm32uv_full import BaofengDM32UVFullFormatter


def test_dm32uv_full_headers_and_defaults():
    f = BaofengDM32UVFullFormatter()
    expected = f.output_columns

    df = LightDataFrame.from_records([
        {
            "frequency": "146.520",
            "fm_analog": "1",
            "callsign": "W1ABC",
            "nearest_city": "Concord",
        }
    ])

    out = f.format(df, start_channel=5)

    assert out.columns == expected
    r0 = out.iloc(0)
    assert r0["No."] == 5
    assert r0["Channel Name"]
    assert r0["Channel Type"] == "Analog"
    assert r0["RX Frequency[MHz]"] == "146.520000"
    assert r0["TX Frequency[MHz]"] == "146.520000"
    assert r0["Power"] == "High"
    assert r0["Band Width"] == "25KHz"
    assert r0["Scan List"] == "None"
    assert r0["TX Admit"] == "Allow TX"
    assert r0["Squelch Level"] == "3"
    assert r0["CTC/DCS Decode"] == "None"
    assert r0["CTC/DCS Encode"] == "None"

