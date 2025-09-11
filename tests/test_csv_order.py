import io
from radiobridge.lightweight_data import LightDataFrame
from radiobridge.csv_utils import write_csv


def test_write_csv_preserves_column_order(tmp_path):
    # Define a specific column order
    columns = [
        "No.",
        "Channel Name",
        "Receive Frequency",
        "Transmit Frequency",
        "Channel Type",
        "Transmit Power",
    ]

    # Build records in that order
    records = [
        {
            "No.": 1,
            "Channel Name": "W1ABC-CITY",
            "Receive Frequency": "146.520000",
            "Transmit Frequency": "146.520000",
            "Channel Type": "A-Analog",
            "Transmit Power": "Turbo",
        },
        {
            "No.": 2,
            "Channel Name": "K6XYZ-TOWN",
            "Receive Frequency": "147.000000",
            "Transmit Frequency": "147.600000",
            "Channel Type": "A-Analog",
            "Transmit Power": "Turbo",
        },
    ]

    df = LightDataFrame.from_records(records)

    out_file = tmp_path / "order_test.csv"
    write_csv(df, out_file)

    # Read back first line (header)
    header = out_file.read_text(encoding="utf-8").splitlines()[0]
    header_cols = header.split(",")

    assert header_cols == columns
