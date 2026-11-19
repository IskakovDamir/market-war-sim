# Decisions

Choices made without asking, in the order they were made.

| # | Step | Decision | Why |
| --- | --- | --- | --- |
| D1 | 0 | Work in `~/Projects/market-war`, created by copying `~/Downloads/market-war`. The Downloads folder is never written to. | The brief names `~/Projects/market-war`, which did not exist; the sources were in `~/Downloads/market-war`, and the brief forbids touching Downloads. Copying only reads it. |
| D2 | 1 | First commit is the original sources unchanged, so every later fix has a clean diff against the code as found. | Discovery cites file:line of that commit (`890a721`). |
| D3 | 2 | Two doc folders: `references/` holds what Claude reads while running a game (rules, schema, rubric, runbook); `reference/` holds the engineering record (discovery, decisions, calibration, proof screenshots). | The brief uses both names; keeping both literal paths means every path in the brief resolves. |
| D4 | 2 | Paths: each script keeps `BASE` (its own folder) and adds `ROOT` (repo root). Logo from `assets/`, live state in `ROOT/live`, team doc template in `ROOT/out`. `MARKET_WAR_LIVE` overrides the live folder. | Scripts run from any working directory; tests need a temp live folder without touching the real one. The env var is additive; the CLI is unchanged. |
| D5 | 2 | All file reads and writes in scripts pass `encoding='utf-8'`. | Russian text in state and HTML; the default encoding depends on the host locale. |
| D6 | 2 | `.venv` with pinned `pytest==9.2.0` and `playwright==1.65.2` (`requirements-dev.txt`). | Runtime stays stdlib; dev tools are isolated and reproducible. |
