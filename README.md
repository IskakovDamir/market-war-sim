# Market War: GTM simulation (nFactorial GTM / Growth bootcamp)

Python 3, stdlib only. Deterministic, seed 7.

- spec.py: segments, 5 companies, 12 channels, 14 action cards (single source of truth)
- sim.py: run(moves, seed=7, upto=None), final_scores(res, icps)
- extract.py: parses a team Google Doc exported as markdown for checkpoint 1, 2 or 3
- dashboard.py: HTML dashboards (wait, public, sim1, final)
- live.py: game-day CLI: reset | ingest <cp> <md...> | moves <cp> <moves.json> | render <public1|public2|public3|sim1|final> [out]
- report.py: prints a full test game from a moves file
- gen_doc.py: builds the team doc template (out/team_doc.html)

Quick check:
  python3 report.py samples/test_moves.json
  python3 live.py reset && python3 live.py ingest 1 samples/team_doc_filled_rork.md && python3 live.py moves 1 samples/moves_cp1.json && python3 live.py render public1 /tmp/p1.html
