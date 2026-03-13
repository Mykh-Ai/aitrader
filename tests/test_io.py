from pathlib import Path

import pandas as pd

from analyzer.io import save_dataframe


def test_save_dataframe_writes_utf8_csv_without_index(tmp_path):
    out = tmp_path / "out.csv"
    df = pd.DataFrame({"Name": ["тест", "café"], "Value": [1, 2]})

    save_dataframe(df, out)

    raw = out.read_bytes()
    assert "тест".encode("utf-8") in raw
    roundtrip = pd.read_csv(out, encoding="utf-8")
    assert roundtrip.columns.tolist() == ["Name", "Value"]
    assert "Unnamed: 0" not in roundtrip.columns
    assert roundtrip.to_dict(orient="list") == {"Name": ["тест", "café"], "Value": [1, 2]}
