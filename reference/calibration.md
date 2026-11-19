# Calibration report

Read only: nothing in the sim was changed for this report. Reproduce with:

```bash
python3 tools/calibrate.py
```

## Method

For each company, its three moves in the golden game (`samples/test_moves.json`, seed 7, Rork ICP `fnd`) are replaced by one strategy while the other four teams keep their golden moves. Code state: after fixes B1 to B21.

| Strategy | What changes for the tested company |
| --- | --- |
| golden | nothing |
| focused | each quarter's golden channel budget goes to the two channels that land the most ICP users per dollar inside the game (60/40); plans, scores, ICP and cards stay golden |
| spray | the same budget split evenly over all 12 channels (most slices fall under the min bid and work at 30%) |
| overpromise | golden moves plus the overpromise card in every quarter |
| zero | golden plans and scores, no spend and no cards |
| minimal | probe outside the brief: $5k on Telegram (its min bid) in Q1, nothing else |

"Best rival efficiency" is the highest efficiency score among the other four teams: 100 means the tested strategy did not distort anyone else's efficiency.

## Results

| Company | Strategy | Final | Goal | Efficiency | Best rival efficiency | Rank | MRR Q3 | Spent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lovable | golden | 85.6 | 100.0 | 51.9 | 100.0 | 2 | $428k | $895k |
| lovable | focused | 91.6 | 100.0 | 71.9 | 100.0 | 1 | $500k | $895k |
| lovable | spray | 79.9 | 100.0 | 33.0 | 100.0 | 3 | $369k | $895k |
| lovable | overpromise | 46.7 | 62.0 | 10.9 | 100.0 | 4 | $274k | $895k |
| lovable | zero | 0.0 | 0.0 | 0.0 | 100.0 | 5 | $70k | $0k |
| lovable | minimal | 0.0 | 0.0 | 0.0 | 100.0 | 5 | $71k | $5k |
| lovable | (focused channels Q1 / Q2 / Q3) | community+geo / community+geo / events+telegram | | | | | | |
| bolt | golden | 25.2 | 32.4 | 8.4 | 100.0 | 5 | $132k | $600k |
| bolt | focused | 60.4 | 77.3 | 21.0 | 100.0 | 5 | $177k | $600k |
| bolt | spray | 22.7 | 30.2 | 5.2 | 100.0 | 5 | $130k | $600k |
| bolt | overpromise | 0.0 | 0.0 | 0.0 | 100.0 | 5 | $77k | $600k |
| bolt | zero | 0.0 | 0.0 | 0.0 | 100.0 | 5 | $45k | $0k |
| bolt | minimal | 0.0 | 0.0 | 0.0 | 100.0 | 5 | $46k | $5k |
| bolt | (focused channels Q1 / Q2 / Q3) | geo+partners / geo+partners / events+telegram | | | | | | |
| v0 | golden | 74.5 | 100.0 | 14.9 | 100.0 | 4 | $100k | $365k |
| v0 | focused | 75.8 | 100.0 | 19.3 | 100.0 | 4 | $120k | $365k |
| v0 | spray | 70.0 | 100.0 | 0.0 | 100.0 | 4 | $59k | $365k |
| v0 | overpromise | 70.0 | 100.0 | 0.0 | 100.0 | 4 | $60k | $365k |
| v0 | zero | 67.5 | 96.4 | 0.0 | 100.0 | 4 | $27k | $0k |
| v0 | minimal | 68.5 | 97.8 | 0.0 | 100.0 | 4 | $27k | $5k |
| v0 | (focused channels Q1 / Q2 / Q3) | partners+seo / geo+partners / creators+events | | | | | | |
| base44 | golden | 90.7 | 100.0 | 69.1 | 100.0 | 1 | $218k | $400k |
| base44 | focused | 94.2 | 100.0 | 80.7 | 100.0 | 1 | $263k | $400k |
| base44 | spray | 77.2 | 100.0 | 24.0 | 100.0 | 3 | $113k | $400k |
| base44 | overpromise | 77.4 | 100.0 | 24.6 | 100.0 | 3 | $126k | $400k |
| base44 | zero | 70.0 | 100.0 | 0.0 | 100.0 | 4 | $37k | $0k |
| base44 | minimal | 70.0 | 100.0 | 0.0 | 100.0 | 4 | $38k | $5k |
| base44 | (focused channels Q1 / Q2 / Q3) | partners+seo / geo+partners / search+social | | | | | | |
| rork | golden | 78.1 | 68.7 | 100.0 | 69.1 | 3 | $75k | $120k |
| rork | focused | 92.0 | 88.5 | 100.0 | 68.0 | 1 | $92k | $120k |
| rork | spray | 72.2 | 60.3 | 100.0 | 92.2 | 4 | $65k | $120k |
| rork | overpromise | 29.9 | 23.0 | 45.9 | 100.0 | 4 | $27k | $120k |
| rork | zero | 28.0 | 40.1 | 0.0 | 100.0 | 4 | $42k | $0k |
| rork | minimal | 58.5 | 40.8 | 100.0 | 7.7 | 4 | $44k | $5k |
| rork | (focused channels Q1 / Q2 / Q3) | partners / geo / events+telegram | | | | | | |

Sanity: all expectations hold.

## Sanity expectations

| Expectation | Result |
| --- | --- |
| focused beats spray | holds for all 5 companies: Lovable 91.6 vs 79.9, Bolt 60.4 vs 22.7, v0 75.8 vs 70.0, Base44 94.2 vs 77.2, Rork 92.0 vs 72.2 |
| overpromise does not win | holds: it never beats golden or focused and never finishes first. It is the worst paid strategy for Lovable, Bolt and Rork and ties spray for v0 (70.0 vs 70.0) and Base44 (77.4 vs 77.2) |
| zero spend does not win | holds: it never beats golden or focused and never finishes first |

Before fix B17 the zero spend expectation failed in a worse way than "winning": with the original code, Rork at zero spend gained revenue from switching, got efficiency per $1 (110 475), and every other team's efficiency score fell to 0. Finals with the original code: Lovable 70.0, Bolt 14.9, v0 70.0, Base44 70.0, Rork 58.0 (golden: 85.5, 25.2, 74.5, 90.7, 78.1).

## Findings that need a balance decision (not fixed)

1. **A tiny spender still flattens everyone's efficiency (G6).** Rork spending only $5k in Q1 gets efficiency 25.3 revenue dollars per dollar against Base44's 1.94. Efficiency is normalized to the best team, so every rival's efficiency score drops to 7.7 or less. Finals move from golden 85.6 / 25.2 / 74.5 / 90.7 to 71.9 / 22.9 / 70.5 / 72.3 for Lovable, Bolt, v0 and Base44: a team that does almost nothing takes up to 18 points from the leaders. Suspected cause: `final_scores` divides revenue gain by spend with no floor and scales to the maximum. Options: floor the divisor (for example 25% of the company budget), score efficiency against a fixed target instead of the best team, or rank teams on efficiency. Each option changes the golden game, so it is the game designer's call.
2. **Niche goals are almost free.** v0 and Base44 keep goal 96 to 100 with zero spend, because they start first or close to first in their segment and nobody else invests there in the golden game. Doing nothing scores 67.5 (v0) and 70.0 (Base44), far above Bolt's best result. Raising the bar (for example "#1 with at least X% of segment revenue") or measuring growth in the segment would make the role play matter.
3. **Bolt cannot win.** Bolt finishes 5th under every strategy; even the focused plan reaches only goal 77.3 and final 60.4. Doubling MRR in 3 quarters on $600k is out of reach while Lovable spends $895k into the same ICP.
4. **Rork owns efficiency.** With the smallest budget, Rork has the top efficiency in every strategy where it spends, so its 30% efficiency share is close to guaranteed.
5. **The sample moves are far from optimal.** Focused beats golden for every company (by 1.3 to 35.2 points). The best channels per dollar are the slow ones (community, GEO, partners, SEO) in Q1 and Q2 and immediate ones (events, Telegram, search) in Q3. Teams that read the channel table well will beat these samples by a wide margin, which is the intended lesson.
6. **Overpromise compounds.** The refund (half of new payers) plus -1 score the next quarter also triggers switching (rivals become 1 point more attractive), so the trap costs more than the card text suggests: Bolt's MRR falls from $132k to $77k, Lovable's from $428k to $274k.
