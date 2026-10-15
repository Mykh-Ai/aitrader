"""Official public USD-M archive acquisition/normalization; no trading API."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
import csv
import hashlib
import io
import json
import urllib.error
import urllib.request
import zipfile

import pandas as pd

OUT = Path(__file__).resolve().parent
BASE = "https://data.binance.vision/data/futures/um"
KLINE_COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def archive_url(date, cadence="monthly", source="klines"):
    pd.Timestamp(date + ("-01" if len(date) == 7 else ""))
    assert cadence in {"monthly", "daily"} and source in {"klines", "aggTrades"}
    interval = "/1m" if source == "klines" else ""
    name = f"BTCUSDT-{'1m' if source == 'klines' else 'aggTrades'}-{date}.zip"
    return f"{BASE}/{cadence}/{source}/BTCUSDT{interval}/{name}"


def quantize(value, places):
    return float(Decimal(str(value)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN))


def normalize_klines(frame):
    """Open-time+60s right-close labels, preserving original exchange clocks."""
    assert len(frame.columns) == 12, "Unexpected official USD-M kline schema"
    frame = frame.copy()
    if list(frame.columns) != KLINE_COLUMNS:
        frame.columns = KLINE_COLUMNS
    opening = pd.to_numeric(frame.open_time, errors="raise").astype("int64")
    closing = pd.to_numeric(frame.close_time, errors="raise").astype("int64")
    unit = "us" if opening.median() >= 100_000_000_000_000 else "ms"
    open_at = pd.to_datetime(opening, unit=unit, utc=True)
    close_at = pd.to_datetime(closing, unit=unit, utc=True)
    assert (open_at == open_at.dt.floor("min")).all()
    assert ((close_at - open_at) < pd.Timedelta(minutes=1)).all()
    assert ((close_at - open_at) >= pd.Timedelta(seconds=59)).all()
    assert open_at.is_monotonic_increasing and not open_at.duplicated().any()
    total = frame.volume.map(lambda x: quantize(x, 6))
    buy = frame.taker_buy_volume.map(lambda x: quantize(x, 6))
    sell = pd.Series([quantize(Decimal(str(v)) - Decimal(str(b)), 6) for v, b in zip(frame.volume, frame.taker_buy_volume)], index=frame.index)
    count = pd.to_numeric(frame["count"], errors="raise").astype("int64")
    assert (count >= 0).all() and (total >= 0).all() and (buy >= 0).all() and (sell >= 0).all()
    traded = count.gt(0) & total.gt(0)
    assert (count.gt(0) == total.gt(0)).all(), "Inconsistent traded/non-traded archive row"
    result = pd.DataFrame({"Timestamp": open_at + pd.Timedelta(minutes=1),
        "OpenPrice": frame.open.map(lambda x: quantize(x, 2)), "HiPrice": frame.high.map(lambda x: quantize(x, 2)),
        "LowPrice": frame.low.map(lambda x: quantize(x, 2)), "ClosePrice": frame.close.map(lambda x: quantize(x, 2)),
        "TotalQty": total, "BuyQty": buy, "SellQty": sell, "Trades": count,
        "Traded": traded, "IsSynthetic": (~traded).astype(int), "IsRecovered": False, "InvalidRow": False,
        "DataQuality": traded.map({True: "RAW", False: "SYNTHETIC"}),
        "OpenInterest": 0., "FundingRate": 0., "LiqBuyQty": 0., "LiqSellQty": 0., "LiquidationDataAvailable": False,
        "OIFundingLiquidationsAvailable": False, "CandleOpenTsUTC": open_at,
        "ExchangeOpenTimeRaw": opening, "ExchangeCloseTimeRaw": closing,
        "ExchangeOpenAt": open_at, "ExchangeCloseAt": close_at, "ExchangeTimestampUnit": unit})
    assert (result.HiPrice >= result[["OpenPrice", "ClosePrice", "LowPrice"]].max(axis=1)).all()
    assert (result.LowPrice <= result[["OpenPrice", "ClosePrice", "HiPrice"]].min(axis=1)).all()
    return result


def read_kline_zip(path):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(".csv")]
        assert len(names) == 1
        with archive.open(names[0]) as stream:
            data = pd.read_csv(stream, header=None, dtype=str)
    header = data.iloc[0, 0]
    if not str(header).isdigit():
        assert str(header).lower() == "open_time", f"Unexpected archive header: {header}"
        observed_header = data.iloc[0].tolist()
        assert observed_header == KLINE_COLUMNS, f"Unexpected official header: {observed_header}"
        data = data.iloc[1:].reset_index(drop=True)
    return normalize_klines(data)


def acquire(date, cadence="monthly", source="klines"):
    url = archive_url(date, cadence, source)
    folder = OUT / "official_archives" / source
    folder.mkdir(parents=True, exist_ok=True)
    filename = url.rsplit("/", 1)[1]
    record = {"url": url, "checksum_url": url + ".CHECKSUM", "symbol": "BTCUSDT", "market": "USD_M_PERPETUAL_FUTURES",
              "interval": "1m" if source == "klines" else "aggTrade", "date": date, "cadence": cadence,
              "filename": filename, "source_type": source}
    try:
        dest = folder / filename
        if not dest.exists():
            request = urllib.request.Request(url, headers={"User-Agent": "AiTrader-40O-research"})
            with urllib.request.urlopen(request, timeout=40) as response:
                body = response.read()
                record["http_status"] = response.status
            assert zipfile.is_zipfile(io.BytesIO(body)), "Not a ZIP archive"
            dest.write_bytes(body)
        checksum_path = folder / (filename + ".CHECKSUM")
        if not checksum_path.exists():
            with urllib.request.urlopen(url + ".CHECKSUM", timeout=40) as response:
                checksum_path.write_bytes(response.read())
        expected, named = checksum_path.read_text(encoding="utf-8").strip().split()[:2]
        assert named.lstrip("*") == filename
        actual = sha(dest)
        assert actual == expected, "OFFICIAL_CHECKSUM_MISMATCH"
        record.update({"status": "CHECKSUM_VERIFIED", "bytes": dest.stat().st_size, "binance_checksum_sha256": expected,
                       "local_sha256": actual, "archive_path": dest.relative_to(OUT).as_posix()})
        if source == "klines":
            normalized = read_kline_zip(dest)
            record.update({"row_count": len(normalized), "first_exchange_open": normalized.ExchangeOpenAt.min(),
                           "last_exchange_open": normalized.ExchangeOpenAt.max(), "first_normalized_timestamp": normalized.Timestamp.min(),
                           "last_normalized_timestamp": normalized.Timestamp.max(), "timestamp_unit": normalized.ExchangeTimestampUnit.iloc[0]})
        return record
    except Exception as exc:
        record.update({"status": "ACQUISITION_FAILED", "error_type": type(exc).__name__, "error": str(exc),
                       "http_status": getattr(exc, "code", record.get("http_status"))})
        return record


def probe():
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(acquire, ["2026-07", "2026-09"]))
    save("source_manifest.json", {"phase": "KNOWN_2026_SOURCE_VALIDATION_ONLY", "official_base": BASE,
         "official_schema": "https://github.com/binance/binance-public-data/blob/master/README.md#futures", "archives": records,
         "OOS_downloaded": False, "OOS_outcomes_read": False})
    pd.DataFrame(records).to_csv(OUT / "archive_inventory.csv", index=False)
    print(json.dumps(records, indent=2, default=str), flush=True)


if __name__ == "__main__":
    probe()
