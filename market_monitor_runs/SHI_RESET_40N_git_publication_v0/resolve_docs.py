"""Resolve documentation merge while preserving both research and continuity scope."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
pattern = re.compile(r"^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> origin/main\n?", re.MULTILINE | re.DOTALL)
for name in ["README.md", "AGENTS.md", "docs/ACTIVE_DOCS.md", "docs/FEED_CONTRACT_AND_SCHEMA_NOTES.md"]:
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    text, count = pattern.subn(lambda m: m[1] + ("\n" + m[2] if name.endswith("FEED_CONTRACT_AND_SCHEMA_NOTES.md") else ""), text)
    assert count > 0
    if name == "README.md":
        text = text.replace("# AiTrader\n", "# AiTrader\n\nPublication40N: the user explicitly requested publishing the research to`main`. Read [40N publication/reproduction notes](research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md) with the40M roadmap. The preserved research snapshot is commit`0862342`; current main also retains the existing [production-continuity ADR](docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md). Historical replay uses the frozen snapshot and raw inputs, not rehashed current runtime code.\n", 1)
    elif name == "AGENTS.md":
        text = text.replace("## Purpose\n", "## Purpose\n\nPublication40N records the user's explicit request to push this research to`main`. Read `research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md` for commit`0862342` offline reproduction and byte-preserving transfer. The existing production-continuity package/ADR is preserved on main. Publishing here does not alter the retired-main research-base policy or authorize live promotion; future work still follows the task's explicitly selected base and scope.\n", 1)
    else:
        text += "\n40N publication preserves both the40M research handoff and the existing production-continuity ADR`docs/MARKET_MONITOR_CONTINUOUS_CONTEXT_AND_GAP_POLICY_ADR.md`. Read `research/canonical/SHI_RESET_40N_GIT_PUBLICATION_AUDIT_2026_10_15.md` for exact snapshot reproduction after the merge; do not rewrite historical source/code hashes to match current runtime files.\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(name, count, "conflicts resolved")
