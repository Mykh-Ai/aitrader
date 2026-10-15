"""Verify/export40M bytes from the published research commit; no trading/network."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = "0862342"
M = "market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0/"
N = "market_monitor_runs/SHI_RESET_40N_git_publication_v0/"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, help="Optional NEW empty offline directory; never overwrite an existing checkout")
    parser.add_argument("--raw-source-root", type=Path, help="Optional external root containing unchanged feed/feed_recovered files")
    args = parser.parse_args()
    target = args.destination.resolve() if args.destination else None
    if target:
        assert target != ROOT and not ROOT.is_relative_to(target), "Do not export over/above the current checkout"
        assert not target.exists() or target.is_dir() and not any(target.iterdir()), "Destination must be new/empty"
    tree_output = subprocess.check_output(["git", "ls-tree", "-r", "-z", SNAPSHOT], cwd=ROOT)
    tree = {}
    for record in tree_output.split(b"\0"):
        if record:
            metadata, name = record.split(b"\t", 1)
            mode, kind, blob = metadata.decode().split()
            if kind == "blob":
                tree[name.decode("utf-8")] = blob
    process = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def blob(name):
        process.stdin.write(tree[name].encode() + b"\n")
        process.stdin.flush()
        head = process.stdout.readline().split()
        assert head[1] == b"blob"
        payload = process.stdout.read(int(head[2]))
        assert process.stdout.read(1) == b"\n"
        return payload

    def write(name, payload):
        if target:
            path = (target / name).resolve()
            assert path.is_relative_to(target)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

    rows = list(csv.DictReader(io.StringIO(blob(M + "handoff_inventory.csv").decode("utf-8"))))
    overlay = zipfile.ZipFile(io.BytesIO(blob(N + "40M_original_worktree_bytes.zip")))
    overlay_names = set(overlay.namelist())
    verified = raw = 0
    raw_names = []
    for row in rows:
        name = row["path"]
        if row["role"] == "FROZEN_RAW_INPUT":
            raw_names.append(name)
            if args.raw_source_root is None:
                continue
            source = (args.raw_source_root.resolve() / name).resolve()
            assert source.is_relative_to(args.raw_source_root.resolve())
            payload = source.read_bytes()
            raw += 1
        else:
            payload = overlay.read(name) if name in overlay_names else blob(name)
            verified += 1
        assert hashlib.sha256(payload).hexdigest() == row["sha256"], f"Snapshot byte mismatch: {name}"
        write(name, payload)
    for name in [M + "handoff_index.json", M + "handoff_inventory.csv", M + "verification.json", M + "handoff_package_hashes.json"]:
        write(name, blob(name))
    process.stdin.close()
    assert process.wait(timeout=10) == 0
    report = {"status": "PASS_FROZEN_RESEARCH_SNAPSHOT", "snapshot_commit": SNAPSHOT,
              "published_inventory_files_verified": verified, "original_checkout_byte_overlay_files": len(overlay_names),
              "external_frozen_raw_inputs_required": len(raw_names), "external_raw_inputs_verified": raw,
              "raw_feed_published_to_Git": False, "destination": str(target) if target else None,
              "historical_strategy_files_recovered_from_snapshot_not_current_merged_runtime": True}
    print(json.dumps(report, indent=2))
    if not target:
        (Path(__file__).resolve().parent / "snapshot_git_verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
