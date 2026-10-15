# SHI_RESET_40F1 — user-directed short protection after 2R

Date: 2026-10-14. During40F the user explicitly asked to try protection after2R. Run root: `market_monitor_runs/SHI_RESET_40F1_short_protection_2R_v0/`. The only new trading parameter is the trigger:2R instead of1R. Protective stop remains+0.25R. Full-position3,000 USD,5 USD round-trip fee,2-bps adverse slippage per fill, initial structural stops,6R/10R targets,168-hour deadline and the global book/cooldown are preserved.

## Study and evidence

Six paired portfolios were declared before evaluating new2R returns: original/short-space entry policy × no protection/1R/2R protection. The unchanged40F intervention engine is imported by hash. The original40D code, frozen sources, both baseline artifacts and40F selected artifacts are verified and preserved. `study_manifest.json` and execution revisions are retained; two preparation-only failures (all-NaT timezone comparison and rejection-list CSV serialization) were repaired without trading-rule changes or evaluation of2R returns. The active driver identity is frozen in `execution_manifest_v2.json`.

Protection observes a completed minute reaching2R and amends the stop at a real open no earlier than one minute later. Original protective orders remain active before amendment, stop-first same-bar priority is retained and favorable gaps do not invent target improvement. Entry screens are unchanged; each portfolio reruns chronological admission rather than summing overlapping independent trades.

| Protection trigger | Original full net USD | Short-space full net USD |
|---|---:|---:|
| None | 512.276015 | 671.050107 |
| 1R | 373.482955 | 542.325652 |
| 2R | 408.149170 | 671.050107 |

All six portfolios are completely observed with zero censored paths. Four no-protection/1R controls match40F exactly. Original2R has27 trades, nine positive/18 negative,17 original stops/one protective stop/four targets, closed-trade drawdown459.172245 USD. April–September net523.740946 USD. Filtered2R retains21 trades, eight positive/13 negative and224.013800 USD drawdown; April–September net839.785861 USD.

The entire original2R change is reconciled: March26 short expiry+58.774416 becomes a protective stop+9.925617; an earlier free book admits April1 long-55.278046. Net change-104.126845 USD. None of the original16 stops reaches2R, so this trigger rescues none of them. The two filtered short winners arm2R protection but continue to their original6R targets, leaving all21 exits/economics unchanged. This bounded result does not establish that protection is universally useless; it does not support adding this particular rule for a cash improvement on the tested cohort.

## Verification and implication

Two new focused tests passed in0.49s, extending the20 intervention/replay checks recorded in40F:1R cannot arm2R protection, and2R preserves a0.25R stop plus one-minute latency without retroactive same-minute fills. The driver verifies global book, trigger availability, latency, dollar arithmetic, all four controls and preserved source/code identities. `_verify_2r.py` independently checks first2R trigger and first terminal touch with the time-dependent stop on all48 observed paths of the two2R portfolios, including all five actual amendments. `run_verification.json`, `independent_verification.json`, complete journals and `all_2R_activations.csv` retain evidence. Final documentation check: `git diff --check`.

Keep40F short-space as the stronger historical research variant; no new successor is selected because2R improves neither the original no-protection baseline nor the filtered candidate. Continue genuinely subsequent fixed-rule confirmation and separately scoped long-entry research. Absolute positive-trade count improvement remains unachieved under the selected monetary variant; do not hide that tradeoff. Exposed-history selection, large-winner concentration, price-proxy reporting and unmodeled borrowing remain limitations. No source data, original engine, production Monitor/Executor policy, live/order behavior, Backtester gate, dependencies, network or remote state changed. Working-tree task; no commit.
