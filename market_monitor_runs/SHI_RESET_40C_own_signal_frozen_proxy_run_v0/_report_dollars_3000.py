"""Illustrative fixed-$3,000 notional reporting of existing frozen fills."""
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))
from research.own_signal_run.feed import digest

contract = json.loads((OUT / "frozen_contract.json").read_text())
path = OUT / "financial_proxy_replay/trade_ledger.csv"
ledger = pd.read_csv(path)
assert not ledger.censored.any(), "Do not turn unresolved trades into dollar returns"
money = ledger.copy()
money["fixed_raw_entry_notional_usd"] = 3000.0
money["illustrative_quantity_btc"] = 3000.0 / money.entry_price_raw
money["initial_stop_risk_usd"] = money.illustrative_quantity_btc * money.risk_price_distance
for field in ["gross_R", "fee_R", "slippage_R", "assumed_carry_R", "net_R"]:
    money[field.replace("_R", "_usd")] = money[field] * money.initial_stop_risk_usd
sign = np.where(money.direction.eq("LONG"), 1, -1)
np.testing.assert_allclose(money.gross_usd, sign * (money.exit_price_raw - money.entry_price_raw) * money.illustrative_quantity_btc)
np.testing.assert_allclose(money.net_usd, money.gross_usd - money.fee_usd - money.slippage_usd - money.assumed_carry_usd)
rows = []
for family in contract["families"]:
    for cost in contract["cost_scenarios"]:
        trades = money.loc[money.family.eq(family) & money.cost_scenario.eq(cost["id"])]
        rows.append({"family": family, "cost_scenario": cost["id"], "trades": len(trades), "fixed_raw_entry_notional_usd": 3000.0,
                     **{field: float(trades[field].sum()) for field in ["gross_usd", "fee_usd", "slippage_usd", "assumed_carry_usd", "net_usd"]}})
summary = pd.DataFrame(rows)
money.to_csv(OUT / "trade_ledger_3000_usd.csv", index=False)
summary.to_csv(OUT / "family_results_3000_usd.csv", index=False)
metadata = {"user_requested_position_notional_usd": 3000.0, "interpretation": "FIXED_RAW_ENTRY_NOTIONAL_PER_INDEPENDENT_TRADE",
            "source_ledger_sha256": digest(path), "source_contract_sha256": digest(OUT / "frozen_contract.json"),
            "report_script_sha256": digest(Path(__file__)), "fills_and_rules_changed": False, "capital_or_live_sizing_behavior_added": False,
            "usd_reporting_assumes_one_usdt_equals_one_usd": True, "actual_account_fees_verified": False,
            "quantity_formula": "3000 / raw_entry_price", "no_compounding": True,
            "output_hashes": {name: digest(OUT / name) for name in ["trade_ledger_3000_usd.csv", "family_results_3000_usd.csv"]}}
(OUT / "dollar_report_3000_manifest.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(summary.to_string(index=False))
