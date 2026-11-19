# Market War: GTM simulation (nFactorial GTM / Growth bootcamp)

A Claude Code skill. Five teams play real AI app builders (Lovable, Bolt, v0, Base44, Rork) for three checkpoints. Teams fill a Google Doc, the host exports it as markdown, Claude scores the moves, a deterministic simulation (seed 7) plays the market, and HTML dashboards go on the projector.

Runtime: Python 3, standard library only. Dev tools (pytest, Playwright) live in `.venv`.

## Layout

```
SKILL.md                skill entry point (name: market-war)
scripts/                spec.py, sim.py, extract.py, dashboard.py, live.py, report.py, gen_doc.py
assets/                 nf_logo_b64.txt (inlined into dashboards), nf_logo_160.png
samples/                test_moves.json (full game), moves_cp1-3.json, team doc template and a filled doc
references/             rules.md, moves-schema.md, scoring-rubric.md, game-day.md (read by Claude during a game)
reference/              discovery.md, decisions.md, calibration.md, proof/ screenshots (engineering record)
tests/                  pytest suite
tools/                  check_all.py, visual_check.py, calibrate.py
live/                   game state and rendered pages (gitignored)
out/                    generated team doc template (gitignored)
```

## Quick start

```bash
python3 scripts/report.py samples/test_moves.json
python3 scripts/live.py reset
python3 scripts/live.py ingest 1 samples/team_doc_filled_rork.md
python3 scripts/live.py moves 1 samples/moves_cp1.json
python3 scripts/live.py render public1
```

Every script works from any working directory. Game day steps: references/game-day.md.

## Development

```bash
python3 tools/check_all.py
```

It creates `.venv` with `requirements-dev.txt` and Playwright Chromium on first run, then compiles everything, runs pytest, renders and checks all dashboards at 1440x900 and 390x844, replays the golden game and prints a PASS/FAIL table. Exit code 0 only when every row passes.

Install as a skill:

```bash
ln -s "$(pwd)" ~/.claude/skills/market-war
```
