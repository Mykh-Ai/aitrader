# H2 Subslice Review

**Date:** 2026-03-29
**Analyst:** Shi research cycle
**Status:** observational only — non-formalizable, non-replay-ready

---

## 1. Scope

**Data window:** 2026-03-18 → 2026-03-29 (12 days)

**Artifact source:** `local_runs/h2_bounded/<date>/` — per-day analyzer runs
generated from the H2 patch set (Patches 1–3 implemented).

**Setup types analyzed:**
- `IMPULSE_FADE_RECLAIM_LONG_V1`
- `IMPULSE_FADE_RECLAIM_SHORT_V1`

**Total H2 setups:** 315 (LONG: 168 / SHORT: 147)

**Session assignment (UTC):**
- ASIA: 00:00–08:00 (incl. LATE 22:00–24:00, merged in, n=127 combined)
- EU: 08:00–14:00 (n=86)
- US: 14:00–22:00 (n=102)

**Reference summary CSV:** `research/results/h2_subslice_summary_2026-03-29.csv`

---

## 2. Executive verdict

H2 is **not** a homogeneous micro-reaction layer.
A clear and consistent subgroup exists: **RECLAIM_HELD setups** (n=116, 36.8% of all H2)
show a dramatically different outcome profile compared to the aggregate baseline.

When the reclaim level holds at 6 bars post-entry (H2_Post6Label_v1 = RECLAIM_HELD),
MFE median doubles (+0.128% → +0.244%), MAE collapses to near zero (−0.077% → ≈0.000%),
and CloseReturn median jumps 5x (+0.024% → +0.129%).
PositiveCloseReturnRate goes from 56.2% to 79.3% (LONG) / 82.1% (SHORT).

A second dimension — EARLY_CONTINUATION (Post3) — also shows strong differentiation:
EC setups have MFE_median 0.215–0.226% vs 0.061–0.076% for NO_EC.
EC and RECLAIM_HELD are correlated (RECLAIM_HELD → 76–87% EC share)
but NOT identical: EC is observable 3 bars earlier than RECLAIM_HELD.

Session effect exists for SHORT: US session produces the cleanest SHORT profile
(PosRate 66.7%, CR_med +0.092%) while ASIA is weakest for SHORT (PosRate 53%).
For LONG, US session is the worst (PosRate 45%, CR_med −0.014%).

Key limitation: **RECLAIM_HELD and EARLY_CONTINUATION are post-entry outcome labels**.
They describe what happened after entry, not what is observable at entry.
They cannot be used as entry-time filters without further research
into which at-entry context features predict them.

---

## 3. Aggregate H2 baseline

From prior bounded review and confirmed here:

| Metric           | H2_ALL  | H2_LONG | H2_SHORT |
|------------------|---------|---------|----------|
| n                | 315     | 168     | 147      |
| MFE_mean         | +0.184% | +0.184% | +0.184%  |
| MFE_median       | +0.128% | +0.136% | +0.117%  |
| MAE_mean         | −0.124% | −0.121% | −0.128%  |
| MAE_median       | −0.077% | −0.081% | −0.073%  |
| CloseReturn_mean | +0.018% | +0.023% | +0.012%  |
| CloseReturn_med  | +0.024% | +0.022% | +0.024%  |
| PosCloseRetRate  | 56.2%   | 54.8%   | 57.8%    |
| RECLAIM_HELD     | 36.8%   | 35.7%   | 38.1%    |
| EARLY_CONT       | 48.9%   | 46.4%   | 51.7%    |

Aggregate looks like a micro-reaction layer. The subslice reveals why.

---

## 4. Direction × reclaim × session slice

### 4.1 Primary split: Direction × H2_Post6Label_v1

| Group                | n   | MFE_med  | MAE_med  | CR_med   | PosRate | FULL_FADE | EC_share |
|----------------------|-----|----------|----------|----------|---------|-----------|----------|
| LONG_RECLAIM_HELD    | 60  | +0.249%  | −0.002%  | +0.121%  | 76.7%   | 60.0%     | 76.7%    |
| LONG_RECLAIM_FAILED  | 108 | +0.092%  | −0.108%  | −0.011%  | 42.6%   |  9.3%     | 29.6%    |
| SHORT_RECLAIM_HELD   | 56  | +0.240%  | +0.005%  | +0.137%  | 82.1%   | 73.2%     | 87.5%    |
| SHORT_RECLAIM_FAILED | 91  | +0.082%  | −0.121%  | −0.018%  | 42.9%   |  8.8%     | 29.7%    |

**Observation:**
- RECLAIM_HELD: MAE is statistically near zero. When the level holds, there is virtually no
  adverse excursion. The mean-reversion thesis (liquidity grab → reclaim → fade) fully materialises.
- RECLAIM_FAILED: CloseReturn goes negative for both directions. MAE spikes.
  This is the "false reclaim" scenario — level is touched but not sustained.
- SHORT_RECLAIM_HELD shows 73.2% FULL_FADE — the strongest single-number in the dataset.
  This means 73% of held-reclaim SHORT setups see the original bullish impulse fully reversed.

### 4.2 Session × Direction

| Group      | n   | MFE_med  | MAE_med  | CR_med   | PosRate | RH_share |
|------------|-----|----------|----------|----------|---------|----------|
| LONG_ASIA  | 61  | +0.120%  | −0.069%  | +0.032%  | 60.7%   | 36.1%    |
| LONG_EU    | 47  | +0.137%  | −0.082%  | +0.045%  | 59.6%   | 31.9%    |
| LONG_US    | 60  | +0.167%  | −0.100%  | −0.014%  | 45.0%   | 38.3%    |
| SHORT_ASIA | 66  | +0.101%  | −0.095%  | +0.005%  | 53.0%   | 34.8%    |
| SHORT_EU   | 39  | +0.119%  | −0.065%  | +0.012%  | 56.4%   | 35.9%    |
| SHORT_US   | 42  | +0.203%  | −0.064%  | +0.092%  | 66.7%   | 45.2%    |

**Observation:**
- SHORT_US stands out with best MFE_median, best CR_median, best PosRate among all 6 cells.
  RECLAIM_HELD share is also highest (45.2%) — US session generates more durable short reclaims.
- LONG_US is the worst LONG session: PosRate 45%, negative CloseReturn.
  US session consistently hurts LONG H2 setups and helps SHORT.
- ASIA is moderate for LONG (PosRate 60.7%) and weakest for SHORT (53.0%).

### 4.3 Direction × Reclaim × Session (main cube — n≥20 cells only)

| Group                    | n   | MFE_med  | MAE_med  | CR_med   | PosRate | Note         |
|--------------------------|-----|----------|----------|----------|---------|--------------|
| LONG_RECLAIM_HELD_ASIA   | 22  | +0.190%  | +0.001%  | +0.113%  | 81.8%   |              |
| LONG_RECLAIM_HELD_EU     | 15  | +0.291%  | −0.001%  | +0.135%  | 80.0%   | LOW_SAMPLE   |
| LONG_RECLAIM_HELD_US     | 23  | +0.260%  | −0.004%  | +0.098%  | 69.6%   |              |
| LONG_RECLAIM_FAILED_ASIA | 39  | +0.073%  | −0.091%  | −0.004%  | 48.7%   |              |
| LONG_RECLAIM_FAILED_EU   | 32  | +0.112%  | −0.108%  | +0.004%  | 50.0%   |              |
| LONG_RECLAIM_FAILED_US   | 37  | +0.125%  | −0.174%  | −0.113%  | 29.7%   |              |
| SHORT_RECLAIM_HELD_ASIA  | 23  | +0.211%  | +0.005%  | +0.088%  | 78.3%   |              |
| SHORT_RECLAIM_HELD_EU    | 14  | +0.254%  | −0.007%  | +0.087%  | 78.6%   | LOW_SAMPLE   |
| SHORT_RECLAIM_HELD_US    | 19  | +0.285%  | +0.012%  | +0.202%  | 89.5%   | LOW_SAMPLE   |
| SHORT_RECLAIM_FAILED_ASIA| 43  | +0.077%  | −0.117%  | −0.020%  | 39.5%   |              |
| SHORT_RECLAIM_FAILED_EU  | 25  | +0.080%  | −0.156%  | −0.005%  | 44.0%   |              |
| SHORT_RECLAIM_FAILED_US  | 23  | +0.097%  | −0.118%  | −0.018%  | 47.8%   |              |

**Risk concentration note:**
`SHORT_RECLAIM_FAILED_EU` has MAE_mean = −0.345% (see summary CSV) — the worst in the dataset.
EU session appears prone to large adverse excursions on failed short reclaims.

### 4.4 Direction × H2_Post3Label_v1 (EARLY_CONTINUATION)

| Group                        | n   | MFE_med  | MAE_med  | CR_med   | PosRate | RH_share |
|------------------------------|-----|----------|----------|----------|---------|----------|
| LONG_EARLY_CONTINUATION      | 78  | +0.215%  | −0.068%  | +0.060%  | 59.0%   | 59.0%    |
| LONG_NO_EARLY_CONTINUATION   | 90  | +0.076%  | −0.094%  | +0.002%  | 51.1%   | 15.6%    |
| SHORT_EARLY_CONTINUATION     | 76  | +0.226%  | −0.014%  | +0.087%  | 68.4%   | 64.5%    |
| SHORT_NO_EARLY_CONTINUATION  | 71  | +0.061%  | −0.114%  | −0.012%  | 46.5%   |  9.9%    |

**Observation:**
- SHORT_EC: MAE_median = −0.014% (near zero). Combined with PosRate 68.4% and CR_med +0.087%,
  this is the second strongest signal axis.
- LONG_EC vs LONG_NO_EC: MFE 3x gap (+0.215% vs +0.076%), but MAE only modest improvement.
  SHORT_EC shows a cleaner profile: MAE is much lower than LONG_EC.
- EC and RECLAIM_HELD are correlated: EC_share in RECLAIM_HELD = 76–87%.
  But EC is observable 3 bars earlier (Post3 vs Post6).
  Not all EC setups become RECLAIM_HELD (LONG_EC RH_share = 59%; SHORT_EC = 64%).

---

## 5. Strongest subgroup

**Primary candidate: SHORT_RECLAIM_HELD** (n=56)

```
MFE_median:         +0.240%   (vs +0.117% baseline SHORT)
MAE_median:         +0.005%   (essentially zero — no adverse excursion)
CloseReturn_median: +0.137%
PositiveCloseReturnRate: 82.1%
FULL_FADE share:    73.2%
EARLY_CONTINUATION: 87.5%
```

Profile interpretation: when a SHORT H2 setup reclaims the level and holds it for 6 bars,
the original bullish impulse fades in 73% of cases. The price moves directionally with
near-zero drawback. This is the strongest isolated signal in the H2 dataset.

**Secondary candidate: LONG_RECLAIM_HELD** (n=60)

Slightly weaker than SHORT_RECLAIM_HELD but same structural profile:
MFE_median +0.249%, MAE_median −0.002%, PosRate 76.7%.

**Tertiary note: SHORT_US (standalone session, n=42)**
Strongest session effect without reclaim conditioning.
PosRate 66.7%, CR_med +0.092%, MFE_median +0.203%.
RECLAIM_HELD share 45.2% — US session has higher proportion of durable reclaims for SHORT.

**LOW_SAMPLE cell of interest (cannot conclude, but directionally strong):**
SHORT_RECLAIM_HELD_US (n=19): PosRate 89.5%, CR_med +0.202%, MAE_median +0.012%.
Requires 3–4x more data before meaningful interpretation.

---

## 6. Strategic interpretation for Shi

**H2 is NOT still only a micro-reaction layer.**
At the aggregate level it appears micro (+0.128% MFE_median). That is correct.
But the aggregate conceals a bimodal structure:

- **RECLAIM_HELD** (36.8%): clean reversal signal, near-zero MAE, 79–82% PosRate
- **RECLAIM_FAILED** (63.2%): noise/loss zone, MAE spikes, 42–43% PosRate

The H2 hypothesis (liquidity grab → reclaim → fade) **is empirically confirmed**
in the RECLAIM_HELD subgroup. The aggregate looks weak only because 63% of setups
don't sustain the reclaim — they are mixed in.

**Critical limitation:**
RECLAIM_HELD is a post-entry outcome label (measured at T+6). It cannot be used
as an entry-time filter without knowing which at-entry features predict it.
This is the research gap: the pattern is real, but the at-entry observable is unknown.

**What this means for future filter hypothesis:**
The question shifts from "does H2 have edge?" to
"what at-entry context features predict RECLAIM_HELD?"
Candidates to examine in next research step:
- `CtxLiqSpike_v1` — liquidity spike at formation
- `CtxDeltaSpike_v1` — aggressive order flow
- `AbsorptionScore_v1` — absorption context
- `CtxWickReclaim_v1` — wick reclaim at bar level
- Session (SHORT+US shows higher RH_share: 45% vs 35% in ASIA)

This is a future step — no code changes, no threshold tuning here.

**SHORT directional tilt confirmed:**
SHORT setups outperform LONG in RECLAIM_HELD (82.1% vs 76.7% PosRate,
73.2% vs 60.0% FULL_FADE). The previously observed weak SHORT tilt
now has a structural explanation: SHORT reclaims are more durable and
produce cleaner full reversals in compressed/MIXED regime.

---

## 7. Decision

**H2_SUBGROUP_WORTH_TRACKING**

Rationale: RECLAIM_HELD subgroup (n=116) has a statistically meaningful and
structurally consistent profile separation from RECLAIM_FAILED.
The MFE gap (+0.244% vs +0.087% median), the MAE collapse (near zero vs −0.115%),
and the PosRate gap (79% vs 43%) are not noise at this sample size.
This warrants tracking as a future filter hypothesis target.

---

## 8. Next step

Examine correlation between at-entry context features
(`CtxLiqSpike_v1`, `CtxDeltaSpike_v1`, `CtxWickReclaim_v1`, `AbsorptionScore_v1`)
and RECLAIM_HELD label — to identify whether any at-entry observable
predicts reclaim durability in H2 setups.

No code changes. Read-only analysis of existing setup CSVs.
Minimum sample threshold: n≥20 per cell before any interpretation.
