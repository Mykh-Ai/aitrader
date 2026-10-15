"""40C run artifact: frozen engine, one instance, weekly progress only."""
from pathlib import Path
import json
import sys
import time

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT))

from research.own_signal_run.__main__ import code_hashes, save_json, verified_inputs
from research.own_signal_run.causal import CausalSignalEngine
from research.own_signal_run.contracts import contract_hash, validate_signal
from research.own_signal_run.feed import digest

started = time.monotonic()
feed, contract = verified_inputs(ROOT, OUT)
folder = OUT / "signals"
if folder.exists():
    raise ValueError("Preserve existing full-run outputs; use a new version")
engine = CausalSignalEngine(feed, contract)
cutoff = feed.Timestamp.iloc[0] + pd.Timedelta(days=7)
last = feed.Timestamp.max()
while True:
    current = min(cutoff, last)
    engine.advance_until(current)
    progress = {
        "processed_through": str(current),
        "h1_steps": len(engine.timeline),
        "candidate_decisions": len(engine.decisions),
        "accepted_candidates": sum(x["accepted"] for x in engine.decisions),
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "market_state_reset": False,
        "structure_levels_reset": False,
        "liquidity_zones_reset": False,
        "qualified_h1_state_reset": False,
        "setup_context_reset": False,
    }
    save_json(OUT / "signal_progress.json", progress)
    print(json.dumps(progress), flush=True)
    if current == last:
        break
    cutoff += pd.Timedelta(days=7)

decisions, timeline = engine.frames()
accepted = decisions.loc[decisions.accepted]
for decision in accepted.to_dict("records"):
    validate_signal(decision, contract)
folder.mkdir()
decisions.to_csv(folder / "candidate_decisions.csv", index=False)
timeline.to_csv(folder / "state_continuity.csv", index=False)
save_json(folder / "generation_manifest.json", {
    "contract_sha256": contract_hash(contract),
    "candidate_decisions_sha256": digest(folder / "candidate_decisions.csv"),
    "state_continuity_sha256": digest(folder / "state_continuity.csv"),
    "code_hashes": code_hashes(ROOT),
    "cutoff": last,
    "source": "Aitrader_feed_only",
    "financial_replay": False,
    "single_engine_instance": True,
    "technical_chunk_days": 7,
    "elapsed_seconds": round(time.monotonic() - started, 2),
    "accepted_by_family": accepted.family.value_counts().to_dict(),
    "run_artifact_sha256": digest(Path(__file__)),
})
print(json.dumps({"status": "CAUSAL_SIGNALS_COMPLETE", "accepted_by_family": accepted.family.value_counts().to_dict()}), flush=True)
