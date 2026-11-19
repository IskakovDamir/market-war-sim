# Game day runbook

All commands run from any directory. `MW` is the skill folder:

```bash
MW=~/.claude/skills/market-war
```

Live state is `$MW/live/state.json` and the default dashboard file is `$MW/live/index.html`. Both are gitignored. Set `MARKET_WAR_LIVE=/some/dir` to keep a second game apart.

## The day before

1. Run the full check. It must end with every row PASS:
   ```bash
   python3 $MW/tools/check_all.py
   ```
2. Build the team doc template, import `out/team_doc.html` into Google Docs, check the tables survived, share it as view only:
   ```bash
   python3 $MW/scripts/gen_doc.py
   ```
3. Decide which team plays which company: Lovable (leader), Bolt (challenger), v0 and Base44 (niche), Rork (newcomer).

## Before checkpoint 1

```bash
python3 $MW/scripts/live.py reset
python3 $MW/scripts/live.py render wait
```
Open `$MW/live/index.html` on the projector: the pre-game screen shows each company's budget, starting revenue and goal. Refresh the tab after each new render. A mistyped view name stops with `!! неизвестный экран` and writes nothing, so the final screen never shows by accident.

## Checkpoint 1

1. Each team sends its doc link with "[Компания], чекпоинт 1 готов".
2. Export each doc: File, Download, Markdown (.md). Save as `$MW/live/docs/cp1/<company>.md`. The company is read from "Наша компания:" and falls back to the file name.
3. Ingest:
   ```bash
   python3 $MW/scripts/live.py ingest 1 $MW/live/docs/cp1/*.md
   ```
   Each team prints `=== <company>` and the parsed fields. `!! не понял компанию` means neither the doc nor the file name names a company: rename the file and ingest it again.
4. Check spend and plans in the printout against the doc. Then write `$MW/live/moves_cp1.json` with references/scoring-rubric.md and references/moves-schema.md: `icp`, `scores`, `consistency: 1`, `actions`. Leave out `plans` and `spend` to take them from the doc.
5. Store the moves (this also fixes Rork's goal segment from its ICP):
   ```bash
   python3 $MW/scripts/live.py moves 1 $MW/live/moves_cp1.json
   ```
6. Show the open parts:
   ```bash
   python3 $MW/scripts/live.py render public1
   ```

## Checkpoint 2

1. Export to `$MW/live/docs/cp2/`, then `live.py ingest 2 ...`.
2. Write `moves_cp2.json`. Score consistency against checkpoint 1. Team deals and M&A count only when both docs say the same thing; check both.
3. `live.py moves 2 $MW/live/moves_cp2.json`, then `live.py render public2`.
4. Predictions: every team writes how many users each rival will have after two quarters. Store them (team id -> company id -> users):
   ```bash
   python3 - <<'EOF'
   import json, os
   p = os.path.expanduser('~/.claude/skills/market-war/live/state.json')
   s = json.load(open(p, encoding='utf-8'))
   s['predictions'] = {'bolt': {'lovable': 70000, 'v0': 20000, 'base44': 15000, 'rork': 9000}}
   json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
   EOF
   ```
5. Simulation 1 (users only, no revenue):
   ```bash
   python3 $MW/scripts/live.py render sim1
   ```
   The table marks the most accurate team with "+5 баллов". Write it into `s['bonus'] = {'<team>': 5}` with the same snippet; the final view adds it.

## Checkpoint 3

1. Export to `$MW/live/docs/cp3/`, `live.py ingest 3 ...`, write `moves_cp3.json`, `live.py moves 3 ...`.
2. Optional: `live.py render public3`.
3. Optional quotes for the final cards (company id -> list of short buyer quotes): `s['quotes'] = {'rork': ['...']}` with the snippet above.
4. Final:
   ```bash
   python3 $MW/scripts/live.py render final
   ```
   The terminal prints goals and final scores. The page names the winning team and, for every team, shows its role, the goal of that role with the number it is judged on (start, finish, what was needed), revenue, market share and users from start to finish, and the score. Below: the MRR chart, the numbers table and each company's events. Read it out from the role, not from the size: a newcomer that took 14% of its ICP can beat a leader with twice the revenue.

## When something goes wrong

| Situation | What to do |
| --- | --- |
| A team did not submit | leave it out of the moves file; it keeps its previous offer with zero spend and no cards |
| A team spent more than its budget | nothing; the sim scales its channels down and logs "перерасход" |
| Wrong number in a move | fix the JSON and run `live.py moves <cp> <file>` again; it overwrites that company's move for that checkpoint |
| Wrong doc ingested | ingest the right file again; it overwrites that company's entry |
| Start over | `live.py reset` deletes the state; docs and moves files stay |
| Need to see the numbers without showing them | `python3 $MW/scripts/report.py <full game file>` prints everything to the terminal only |
