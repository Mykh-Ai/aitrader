# analyzer/

Status: LEGACY / FAILED AS STRATEGY ANALYZER / READ-ONLY.

Do not run `analyzer.pipeline` as active research.

Do not import `failed_breaks`, `setups`, `outcomes`, `rankings`, `shortlists`, or `research_summary` into `market_monitor`.

Potentially reusable only after audit/refactor:

- feed_contract;
- schema reference;
- loader reference;
- base metrics;
- VWAP;
- volume/delta;
- context/session labels;
- swing primitives.

Forbidden:

- failed-break/reclaim setup logic;
- shallow sweep detector as liquidity model;
- arbitrary 12-bar outcomes;
- setup candidate logic;
- rankings/selections/shortlists;
- research replay bridge;
- `FormalizationEligible` logic.
