"""Read-only official BTCUSDC spot archive import; only this run root is written."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import shutil
import urllib.request
import zipfile

import pandas as pd

OUT = Path(__file__).resolve().parent
CACHE = Path("D:/Project_V/Executor/backtests/imbalance_045_075_through_2026-09-27_v1/source/execution_feed_btcusdc/raw")
RAW = OUT / "spot_BTCUSDC/raw"
FIELDS = ["open_time", "OpenPrice", "HiPrice", "LowPrice", "ClosePrice", "TotalQty", "close_time",
          "QuoteQty", "Trades", "BuyQty", "BuyQuoteQty", "ignore"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def urls():
    rows = []
    for month in pd.period_range("2026-03", "2026-08", freq="M"):
        name = f"BTCUSDC-1m-{month}.zip"
        rows.append((name, f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDC/1m/{name}"))
    for day in pd.date_range("2026-09-01", "2026-10-12"):
        name = f"BTCUSDC-1m-{day:%Y-%m-%d}.zip"
        rows.append((name, f"https://data.binance.vision/data/spot/daily/klines/BTCUSDC/1m/{name}"))
    return rows


def fetch(url, target):
    assert url.startswith("https://data.binance.vision/data/spot/")
    with urllib.request.urlopen(url, timeout=25) as response:
        if response.status != 200:
            raise ValueError(f"Unexpected HTTP status {response.status}")
        payload = response.read(20_000_001)
    if len(payload) > 20_000_000:
        raise ValueError("Archive exceeds bounded download size")
    target.write_bytes(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Fetch missing public official archives; never use credentials")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    provenance, missing, frames = [], [], []
    for name, url in urls():
        archive, checksum = RAW / name, RAW / (name + ".CHECKSUM")
        source = "EXISTING_RUN_CACHE"
        if not archive.exists() or not checksum.exists():
            if (CACHE / name).exists() and (CACHE / (name + ".CHECKSUM")).exists():
                shutil.copy2(CACHE / name, archive)
                shutil.copy2(CACHE / (name + ".CHECKSUM"), checksum)
                source = "READ_ONLY_EXECUTOR_OFFICIAL_ARCHIVE_CACHE"
            elif args.download:
                try:
                    fetch(url + ".CHECKSUM", checksum)
                    fetch(url, archive)
                    source = "PUBLIC_OFFICIAL_HTTPS_DOWNLOAD"
                except Exception as exc:
                    missing.append({"name": name, "url": url, "error": f"{type(exc).__name__}: {exc}"})
                    print(f"UNAVAILABLE {name}: {type(exc).__name__}", flush=True)
                    continue
            else:
                missing.append({"name": name, "url": url, "error": "PUBLIC_DOWNLOAD_REQUIRED"})
                continue
        expected = checksum.read_text().split()[0]
        actual = sha(archive)
        if expected != actual:
            raise ValueError(f"Official checksum mismatch: {name}")
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.namelist()
            assert len(members) == 1 and members[0] == name[:-4] + ".csv"
            payload = bundle.read(members[0])
        frame = pd.read_csv(io.BytesIO(payload), names=FIELDS)
        assert frame.open_time.mod(60_000_000).eq(0).all(), "Expected 2026 microsecond minute opens"
        assert (frame.close_time - frame.open_time).eq(59_999_999).all()
        frame["Timestamp"] = pd.to_datetime(frame.open_time, unit="us", utc=True) + pd.Timedelta(minutes=1)
        frame["SourceArchive"] = name
        frame["Market"] = "BINANCE_SPOT"
        frame["Symbol"] = "BTCUSDC"
        valid = frame.HiPrice.ge(frame[["OpenPrice", "ClosePrice"]].max(axis=1)) & frame.LowPrice.le(frame[["OpenPrice", "ClosePrice"]].min(axis=1))
        valid &= frame.LowPrice.gt(0) & frame.TotalQty.ge(0)
        assert valid.all(), f"Malformed OHLC: {name}"
        traded = frame.TotalQty.gt(0) & frame.Trades.gt(0)
        frame["DataQuality"] = traded.map({True: "RAW", False: "SPOT_NO_OBSERVED_TRADES"})
        frame["IsSynthetic"], frame["IsRecovered"], frame["InvalidRow"] = 0, False, False
        frame["SellQty"] = frame.TotalQty - frame.BuyQty
        frames.append(frame)
        provenance.append({"name": name, "url": url, "checksum_url": url + ".CHECKSUM", "source": source,
                           "sha256": actual, "checksum_sha256": sha(checksum), "bytes": archive.stat().st_size,
                           "rows": len(frame), "first_close": frame.Timestamp.iloc[0].isoformat(), "last_close": frame.Timestamp.iloc[-1].isoformat(),
                           "no_trade_minutes": int((~traded).sum())})
        print(f"VERIFIED {name} rows={len(frame)} source={source}", flush=True)
    report = {"market": "BINANCE_SPOT", "symbol": "BTCUSDC", "interval": "1m", "normalized_clock": "open_time_UTC_plus60s_right_close_label",
              "official_raw_clock": "microseconds", "archives": provenance, "missing_archives": missing,
              "protected_futures_feed_modified": False, "executor_data_modified": False,
              "official_documentation": "https://github.com/binance/binance-public-data/blob/master/README.md"}
    (OUT / "spot_BTCUSDC/source_manifest.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    combined = pd.concat(frames, ignore_index=True).sort_values("Timestamp").reset_index(drop=True)
    assert not combined.Timestamp.duplicated().any()
    columns = ["Timestamp", "OpenPrice", "HiPrice", "LowPrice", "ClosePrice", "TotalQty", "BuyQty", "SellQty", "Trades",
               "DataQuality", "IsSynthetic", "IsRecovered", "InvalidRow", "Market", "Symbol", "SourceArchive"]
    combined[columns].to_csv(OUT / "spot_BTCUSDC/spot_minutes.csv", index=False)
    quality = combined.groupby(combined.Timestamp.sub(pd.Timedelta(minutes=1)).dt.date).agg(rows=("Timestamp", "size"),
                    no_trade_minutes=("DataQuality", lambda s: int(s.ne("RAW").sum())), first_close=("Timestamp", "min"), last_close=("Timestamp", "max"))
    quality.to_csv(OUT / "spot_BTCUSDC/daily_quality.csv")
    print(json.dumps({"verified_archives": len(provenance), "missing_archives": len(missing), "rows": len(combined),
                      "first_close": str(combined.Timestamp.min()), "last_close": str(combined.Timestamp.max())}), flush=True)
    if missing:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
