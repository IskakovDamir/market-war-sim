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
| D9 | 3 | Sales has no cost in stud and dev (`None`, "не работает") by design. The invariant "lo < hi for all 5 segments" is tested as: every channel has all 5 segment keys, every range present has 0 < lo < hi, and `None` is allowed only in those two cells. | The literal rule would fail on a documented design choice, not a bug. |
| D10 | 3 | Budget policy for B6: cards are paid in the order written; a card that no longer fits is not played (log line); channels are scaled with what is left. The check moved before scoring so an unplayed card has no effect at all. | Matches the doc rule "траты на каналы урежутся пропорционально" and keeps the golden overspend numbers (88%, 80%) identical. |
| D11 | 3 | B17 fix is narrow: zero spend means efficiency 0. The broader tiny-spend outlier (G6) is reported, not fixed. | Changing how efficiency is normalized is a balance decision and would move the golden game. |
| D12 | 3 | M&A: the seller's card is consent only; a deal written again later is ignored; an owned company can neither buy nor be bought; anything the target owned moves to the buyer; the price must fit the buyer group's remaining budget. | One consistent ownership model, no double charge, no chains that `final_scores` cannot group. |
| D13 | 3 | Custom card `as` counts as that card wherever a card is checked by id without parameters (free_tier, decoy, upsell, overpromise, onboarding). | Before, it applied in conversion only. |
| D14 | 4 | The visual check renders through `live.py render` from a demo state: golden moves plus open answers for all five companies in `tools/fixtures/demo_public.json` (the samples only contain Rork's doc). | Exercises the real CLI with realistic text lengths; the demo text is marked as demo in the file. |
| D15 | 4 | Per-company blocks carry `data-company`, so the check counts company lists structurally (each list must show exactly the 5 ids). | Counting names in text cannot tell a sixth company from a repeated label. |
| D16 | 4 | Phone layout: a `max-width: 700px` media query (one column, smaller type, ranking and numbers tables stacked per company using the header words as labels) plus phone versions of both SVG charts. Desktop markup and charts are unchanged. | Projector view stays as it was; phones get readable charts instead of 3px text. |
| D17 | 4 | Visual thresholds: text boxes are compared after trimming 20% top and bottom (line box padding is not ink); chart marks except light grid lines must not cover text; on the phone text must be at least 12px (the brief sets only the 14px desktop rule). | Avoids false overlaps between stacked headline lines, catches the real B21 defect, keeps phone text legible. |
| D18 | 5 | Calibration adds a "minimal" probe ($5k once) next to the four requested strategies. | It exposes the remaining efficiency outlier (G6) with numbers. |
| D19 | 6 | `check_all.py` creates `.venv` and installs Chromium on first run (needs network once), requires at least 40 passed and 0 failed tests, and compares the golden game with tolerance 0.1. | A fresh clone must pass with one command. |

## Changes to public interface and UI text

Everything else (balance constants in spec.py, CLI commands and arguments, moves JSON format, markdown parsing labels, existing Russian UI strings) is unchanged.

| Change | Why |
| --- | --- |
| `live.py render wait` added; an unknown view name exits 1 with `!! неизвестный экран ...` and writes nothing; `sim1`/`final` without moves exit 1 with `!! нет ходов: ...` | B15: README listed a `wait` view, and any unknown name used to render the final view with revenue |
| `MARKET_WAR_LIVE` env var overrides the live folder (default `<repo>/live`) | D4: tests and parallel games |
| `sim.run` result has a new `warnings` list; snapshots have new `seg_paid`, `seg_arpu`, `arrivals` fields | B14 and tests; existing fields unchanged |
| New log lines: `неизвестный канал «X» пропущен`, `неизвестная карточка «X» пропущена`, `карточка «X» без нужных полей пропущена`, `не хватает бюджета на карточку «X», карточка не сыграна`, `рефералка урезана: бюджета хватает на N приглашений`, `сделка с X не засчитана: цена ... больше остатка бюджета ...`, `сделка с X не засчитана: одна из компаний уже куплена`; warning `неизвестная компания «X» пропущена` | B3, B4, B20, B6, B7, B10, B9, B14 |
| Empty CAC placeholder U+2013 (en dash) became `-` | B18, no em or en dashes in UI |
| `money()` parsing: thousands commas, units only right after the number | B1, B2 (labels untouched) |
| Golden final Lovable 85.489 -> 85.571 (prints 85.6), v0 74.450 -> 74.455 | B12, inside the 0.1 tolerance |
