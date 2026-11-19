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
| D7 | 3 | Each known bug gets a strict xfail test in the test commit; its fix commit removes the marker. A fix that accidentally repairs another bug shows up as XPASS and fails the run. | Proves every test failed before its fix, keeps every commit green. |
| D8 | 3 | Fixed B12 (cohort ARPU) although it moves the golden game: final Lovable 85.489 -> 85.571, v0 74.450 -> 74.455, everything else identical. Both stay inside the 0.1 tolerance of the brief, so the golden numbers in the brief still hold. Tests that compared printed, rounded output now compare with the same 0.1 tolerance. | Proven bug (`prev_price` tracked and never read; a decoy premium vanished with no price change). Leaving it would keep the decoy and upsell cards close to useless. |
