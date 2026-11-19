---
name: market-war
description: Runs Market War, the nFactorial GTM / Growth bootcamp business game where 5 teams play AI app builders (Lovable, Bolt, v0, Base44, Rork) over 3 checkpoints. Use when hosting or preparing a Market War game, ingesting team Google Docs exported as markdown, scoring team moves (AI scores 1-10 per segment, consistency 0/0.5/1), writing a moves JSON for a checkpoint, running the deterministic market simulation, or rendering the public, simulation 1 or final dashboards. Also triggers on "рыночная война", "чекпоинт", "сделай ход за команду", "покажи дашборд", "посчитай симуляцию".
---

# Market War

A deterministic market simulation (Python 3 stdlib, seed 7) plus a live CLI for game day. Teams write moves in Google Docs, the host exports them as markdown, Claude turns each doc into a move with AI scores, the sim plays the quarter, the dashboards go on the projector.

`MW` below is this skill's folder (`~/.claude/skills/market-war`).

## Game-day CLI (public interface, do not change)

```bash
python3 $MW/scripts/live.py reset
python3 $MW/scripts/live.py ingest <cp> <doc.md ...>      # parse team docs for checkpoint 1, 2 or 3
python3 $MW/scripts/live.py moves <cp> <moves.json>       # store moves for that quarter
python3 $MW/scripts/live.py render <view> [out.html]      # public1 | public2 | public3 | sim1 | final
```

State lives in `$MW/live/state.json` (override with `MARKET_WAR_LIVE=<dir>`); the default page is `$MW/live/index.html`.

## What Claude does at each checkpoint

1. Ingest the exported docs and read the printed summary.
2. For every team, write one move into `moves_cp<N>.json`:
   - `icp`: segment id from the doc's ICP answer;
   - `scores`: 1..10 per segment by references/scoring-rubric.md (start at 5, four fits);
   - `consistency`: 1 / 0.5 / 0 against the previous checkpoint (checkpoint 1 is always 1);
   - `actions`: cards from the doc mapped to ids;
   - leave out `plans` and `spend` to take them from the doc.
   Exact format: references/moves-schema.md.
3. `live.py moves <N> <file>`, then render the view for that moment.
4. Never show revenue before the final: public views show open answers only, `sim1` shows users only.

Show the host the scores you gave, with one line of reasoning per team, before running `moves`. The host has the last word.

## Files

| Path | What |
| --- | --- |
| scripts/spec.py | market data: segments, companies, channels, cards, AI cost (balance constants) |
| scripts/sim.py | `run(moves, seed=7, upto=None)`, `final_scores(res, icps)` |
| scripts/extract.py | `extract(md, checkpoint)`, `money(text)` |
| scripts/dashboard.py | `view_wait`, `view_public`, `view_sim1`, `view_final` |
| scripts/live.py | game-day CLI |
| scripts/report.py | `report.py <full game moves.json>`: prints every quarter, goals and logs |
| scripts/gen_doc.py | builds the team doc template into `out/team_doc.html` |
| references/rules.md | every formula and constant |
| references/moves-schema.md | moves JSON schema and examples |
| references/scoring-rubric.md | how to score 1..10 per segment and consistency |
| references/game-day.md | step-by-step host runbook |
| samples/ | full test game, checkpoint moves, empty and filled team docs |

## Checks

```bash
python3 $MW/tools/check_all.py          # compile, pytest, visual check, golden game: all must PASS
python3 $MW/scripts/report.py $MW/samples/test_moves.json
```

The golden game (`samples/test_moves.json`, seed 7) must give goals lovable 100, bolt 32.4, v0 100, base44 100, rork 68.7 and final 85.5, 25.2, 74.5, 90.7, 78.1. If it does not, the sim changed: stop and find out why before game day.
