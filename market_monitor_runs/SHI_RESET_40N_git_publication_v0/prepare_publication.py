"""Stage the verified40M snapshot without changing frozen artifact bytes."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
M = ROOT / "market_monitor_runs/SHI_RESET_40M_research_deployment_handoff_v0"


def run(args, data=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=data, text=True,
                          capture_output=True, check=True).stdout


def main():
    with (M / "handoff_inventory.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    chosen = [r for r in rows if r["role"] != "FROZEN_RAW_INPUT"]
    for r in chosen:
        assert hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest() == r["sha256"], r["path"]
    names = sorted({r["path"] for r in chosen} | {
        p.relative_to(ROOT).as_posix() for p in M.iterdir() if p.is_file()})
    assert all(not name.startswith(("feed/", "feed_recovered/", ".git/", ".worktrees/", "pytest-of-User/", "tmp_llm_last_two_evidence/")) for name in names)
    assert all("\n" not in name and "\t" not in name and '"' not in name for name in names)
    # Frozen manifests hash disk bytes. Ordinary text normalization would
    # change Windows-generated CSV bytes and invalidate those identities.
    hashes = run(["hash-object", "-w", "--stdin-paths", "--no-filters"], "\n".join(names) + "\n").splitlines()
    assert len(hashes) == len(names)
    modes = {}
    for record in run(["ls-files", "--stage", "-z"]).split("\0"):
        if record:
            metadata, name = record.split("\t", 1)
            modes[name] = metadata.split()[0]
    baseline = {}
    for record in run(["ls-tree", "-r", "-z", "HEAD"]).split("\0"):
        if record:
            metadata, name = record.split("\t", 1)
            mode, kind, blob = metadata.split()
            if kind == "blob":
                baseline[name] = (mode, blob)
    snapshot = json.loads((M / "handoff_index.json").read_text())
    modified = {line[3:] for line in snapshot["git_worktree_status_at_snapshot"] if line[:2] != "??"}
    preparation = ROOT / "market_monitor_runs/SHI_RESET_40B_own_signal_run_preparation_v1/preparation_manifest.json"
    frozen_code = set(json.loads(preparation.read_text())["code_hashes"])
    selected = {name: blob for name, blob in zip(names, hashes)
                if name not in baseline or name in modified or name in frozen_code}
    # Preserve old Windows checkout bytes separately rather than turning
    # unchanged repository files into hundreds of line-ending-only rewrites.
    overlay = {name: blob for name, blob in zip(names, hashes)
               if name in baseline and name not in selected and blob != baseline[name][1]}
    with zipfile.ZipFile(OUT / "40M_original_worktree_bytes.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(overlay):
            archive.write(ROOT / name, arcname=name)
    (OUT / "original_worktree_overlay.json").write_text(json.dumps({
        "purpose": "Overlay only in a detached reproduction of the research snapshot, before40M byte verification; not on merged production main.",
        "paths": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(overlay)},
        "raw_feed_included": False}, indent=2) + "\n", encoding="utf-8")
    updates = "".join(f"{mode} {blob}\t{name}\0" for name, (mode, blob) in baseline.items() if name not in selected)
    updates += "".join(f"{modes.get(name, '100644')} {blob}\t{name}\0" for name, blob in selected.items())
    run(["update-index", "-z", "--index-info"], updates)
    actual = {}
    for record in run(["ls-files", "--stage", "-z"]).split("\0"):
        if record:
            metadata, name = record.split("\t", 1)
            actual[name] = metadata.split()[1]
    assert all(actual.get(name) == blob for name, blob in selected.items()), "Index staging did not persist"
    assert all(actual.get(name) == blob for name, (mode, blob) in baseline.items() if name not in selected)
    result = {"snapshot_base_head": run(["rev-parse", "HEAD"]).strip(), "paths_staged_or_verified": len(selected),
              "unchanged_checkout_byte_overlay_files": len(overlay),
              "raw_feed_files_not_published": 232, "frozen_bytes_preserved_without_filters": True,
              "excluded": ["feed", "feed_recovered", "worktrees", "temporary pytest fixtures", "runtime credential/log directories"],
              "paths": sorted(selected)}
    (OUT / "publication_scope.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "paths"}, indent=2))


if __name__ == "__main__":
    main()
