# Discovery: Market War as found

Snapshot of commit `890a721` (original sources, flat layout). File:line references point at that commit. From step 2 on the same files live in `scripts/`; every bug below also has a pytest test (named in the last column of the bug table) so it can be reproduced after the move.

Baseline measured before any change: `python3 report.py samples/test_moves.json` gives goals lovable 100, bolt 32.4, v0 100, base44 100, rork 68.7 and final lovable 85.5, bolt 25.2, v0 74.5, base44 90.7, rork 78.1. Exact values: final lovable 85.489, bolt 25.1761, v0 74.4504, base44 90.7245, rork 78.0567.

## 1. Data flow

```
team Google Doc (one per team, template built by gen_doc.py -> out/team_doc.html)
   | host: File -> Download -> Markdown
   v
live.py ingest <cp> <md...>
   extract.extract(md, cp)                 extract.py:32-58
   company id from "Наша компания:" or file name   live.py:15-19, 29
   state.raw[cp][cid]    = everything parsed (closed part: ICP, war, spend, cards, econ)
   state.public[cp][cid] = positioning, ad, h1, h2, cta, plans, announce   live.py:31-33
   v
host (Claude) reads raw, writes moves_cpN.json: scores 1-10 per segment, consistency, icp, actions
   v
live.py moves <cp> <moves.json>
   missing plans  -> taken from public[cp][cid].plans, else Pro at list price   live.py:41-42
   missing spend  -> taken from raw[cp][cid].spend                              live.py:43
   cp == 1        -> state.icps[cid] = icp (Rork goal segment)                  live.py:44
   state.quarters[cp-1][cid] = move                                             live.py:45
   v
live.py render public1|public2|public3 -> dashboard.view_public(state, cp)    public fields only
live.py render sim1  -> sim.run(quarters, seed, upto=2) -> dashboard.view_sim1   users only (+ predictions)
live.py render final -> sim.run(quarters, seed) -> sim.final_scores(res, icps) -> dashboard.view_final
   state file: <script dir>/live/state.json, default output <script dir>/live/index.html
```

`report.py <moves.json>` runs the same sim on a full game file and prints quarter tables, goals, efficiency and logs. `dashboard.view_wait()` (pre-game screen) exists but no CLI path reaches it.

State keys (live.py:13): `public, raw, quarters, seed (7), icps, predictions, bonus, quotes`. `predictions`, `bonus` and `quotes` are read by the dashboards but no CLI command writes them.

## 2. Rules found in code

### spec.py (balance constants)

| Rule | Where |
| --- | --- |
| 5 segments: size (people choosing a tool per quarter), WTP $/mo, base paid share. stud 120000/$8/0.06, fnd 40000/$40/0.30, des 25000/$30/0.22, dev 30000/$25/0.15, smb 25000/$60/0.25 | spec.py:2-9 |
| 5 companies: budget, list price, starting paid users per segment, free users. lovable $1M/$25/9000 paid/50000 free, bolt $600k/$25/4000/30000, v0 $400k/$20/3000/20000, base44 $400k/$30/2500/12000, rork $150k/$25/800/5000 | spec.py:12-33 |
| 12 channels: min bid (min_k thousand $), delay fractions, targeting share, cost per new user range (lo, hi) per segment, variance. None = channel does not work in that segment (only sales: stud, dev) | spec.py:36-73 |
| 14 action cards (text only, numbers live in sim.py) | spec.py:75-90 |
| AI cost per user per month: paid lovable 7, bolt 8, v0 6, base44 7, rork 8; free 1.5 (v0 1.0) | spec.py:92-93 |

### sim.py

| Rule | Where |
| --- | --- |
| Pool share 0.35 of segment size per quarter, paid churn 0.25, free churn 0.20, look share 0.10 | sim.py:22-25 |
| Card costs: decoy 10k, upsell 15k, referral 20k, viral 50k, onboarding 30k, copy 60k, attack 30k, exclusive 60k; custom max(20k, cost) | sim.py:26-27, 129 |
| Asset score: bolt +1 stud and dev, rork +1 fnd and smb | sim.py:28, 81 |
| Chosen price per segment: highest paid plan <= 1.3 x WTP, else cheapest paid plan, 0 if only free plans | sim.py:30-35 |
| Initial free users split across segments by the paid mix | sim.py:45 |
| Start MRR = sum(paid) x list price | sim.py:51 |
| Team that did not submit: previous move (or Pro at list price, icp fnd, scores 5) with spend {} and actions [], consistency 1 | sim.py:58-63 |
| M&A: both sides declare it, price >= 3 x 3 x paid x list price of the target (3 quarterly revenues), owner switches, price added to buyer spent | sim.py:65-76 |
| Score = AI score (default 5) + asset + events bonus; consistency 0 gives -1; Telegram > $60k gives -1; overpromise gives -1 next quarter; team deal +0.5 if both declare; copy +1 in the chosen segment, target asset bonus halved, second copy -0.5 everywhere; clamp 1..10 | sim.py:78-109 |
| Exclusive partner per segment (first claim wins) | sim.py:111-114 |
| Auction: social and search at >= min bid register the team on its ICP; +15% cost per other registered team in that segment | sim.py:116-120, 168-170 |
| Overspend: if channels + cards > budget left, channels scaled by (left - cards) / channels | sim.py:132-141 |
| Consistency cost penalty: 0 -> x1.25, 0.5 -> x1.10 | sim.py:144-145, 167 |
| Below min bid: 30% effect | sim.py:149-151 |
| Allocation: (1 - target) of spend by natural reach size / mid cost, target share to ICP; ICP not reachable by channel -> half of target share spread, half lost | sim.py:152-161 |
| Sales needs a plan >= $50, else money spent and nothing happens | sim.py:153-155 |
| Cost per user = hi - (hi - lo) x (score - 1) / 9 | sim.py:166 |
| GEO 20% cheaper per quarter, community x0.7 for Lovable, partners x0.6 for v0 in des/dev and Base44 in smb, exclusive x0.6 owner / x1.3 others | sim.py:171-178 |
| Variance: users x (1 + var x U(-1,1)), one draw per channel | sim.py:162, 179 |
| Delays: users land in pending[q + d] by the channel delay fractions | sim.py:180-183 |
| Community: churn bonus 0.2 this and next quarter; events: +0.5 ICP score next quarter | sim.py:185-188 |
| Viral: d6, 5-6 -> +15000 users, else +2000, spread like shorts | sim.py:190-196 |
| Referral: active users x 0.06 x avg score / 6, $10 each | sim.py:197-204 |
| Free tier: arrivals x1.4; no free plan: arrivals x0.6 | sim.py:207-208 |
| Pool cap: total arrivals (incl. sales) per segment <= 0.35 x size | sim.py:211-216 |
| Paid conversion = base_paid x clamp((WTP / price)^0.7, 0.3, 1.5) x (0.7 + 0.06 x score); free tier x0.75, onboarding x1.10, overpromise x1.30, no free plan x1.4, cap 0.9 | sim.py:228-239 |
| Sales arrivals: 60% paid, 40% free | sim.py:240, 248 |
| Cohort ARPU: new customers pay price x1.15 (decoy) x1.10 (upsell); existing keep their ARPU unless price < ARPU | sim.py:242-246 |
| Switching: 10% of paid look around; attack moves them to attacker if attacker score is higher, else attacker loses 5% of its paid; anyone switches to the most attractive rival when attractiveness gap >= 1, attractiveness = score - 0.5 x log2(price / WTP) | sim.py:253-274 |
| Churn: paid 25% x (1 - community bonus) x 0.7 with onboarding; free 20% | sim.py:276-283 |
| Overpromise refund: half of that quarter's new paid leave at quarter end | sim.py:284-289 |
| Metrics: users, paid, MRR, segment revenue, new paid, spend, CAC, AI cost (computed, unused), budget left | sim.py:291-301 |
| Goals: Lovable 100 - 6 per share point below 40; Bolt 100 x (MRR / start - 1) clamped; v0 des #1 -> 100 else ratio to best; Base44 same in smb; Rork 100 x share of ICP segment (from checkpoint 1) / 0.20 | sim.py:318-332 |
| Efficiency: (sum of quarterly revenue - start revenue x quarters) / max(1, spent), normalized to the best team; final = 0.7 goal + 0.3 efficiency; acquired company copies its owner score | sim.py:333-343 |

### extract.py, live.py, dashboard.py

| Rule | Where |
| --- | --- |
| money(): strip spaces and NBSP, comma becomes a dot, $ dropped, first number, units k/к/тыс and m/м/млн | extract.py:8-17 |
| Checkpoint section: `# **Чекпоинт N` up to the next `# **` heading | extract.py:29-31 |
| Field table (head Поле, Кто): question text matched against 16 labels, answer is the last cell | extract.py:40-46 |
| Plans table (head Тариф, Цена в месяц): "беспл", "free" or "$0" -> price 0, else money() | extract.py:47-48 |
| Channel table (head Канал): name matched to 12 channel names, amount from the last cell, only > 0 kept | extract.py:49-53 |
| Company id by substring of the company name or file name: lov, bolt, v0, base, rork | live.py:15-19 |
| "подзаголовок и текст кнопки" split on "Кнопка:" | live.py:20-22 |
| Public dashboard shows only positioning, ad, first screen, plans, announcement; marks a changed positioning | dashboard.py:69-88 |
| Sim 1 shows users only, red tick at start users, prediction error table with +5 for the best | dashboard.py:114-129 |
| Final: ranking with state.bonus added, MRR chart, table, logs and quotes | dashboard.py:159-188 |
| Logo read from out/nf_logo_b64.txt next to the script | dashboard.py:21 |

## 3. Suspected bugs

Every row was run before writing it here; "Got" is the measured output. Commands run from the repo root at commit `890a721`.

| ID | Where | Bug | Got | Expected | Test after step 3 |
| --- | --- | --- | --- | --- | --- |
| B1 | extract.py:9 | money() treats a thousands comma as a decimal point | `money('50,000')` = 50, `money('$1,200,000')` = 1 | 50000, 1200000 | test_extract.py::test_money_thousands_comma |
| B2 | extract.py:11, 16 | unit letters inside words count as units | `money('$29 со скидкой')` = 29000, `money('25 мес')` = 25000000 | 29, 25 | test_extract.py::test_money_unit_inside_word |
| B3 | sim.py:148 | unknown channel id crashes the run | KeyError: 'tiktok' | skipped, log line | test_robustness.py::test_unknown_channel_skipped |
| B4 | sim.py:128-131 | unknown action id ignored silently | logs [] | skipped with a log line | test_robustness.py::test_unknown_action_skipped |
| B5 | sim.py:68 | seller side M&A action (`buyer` key, no `target`) crashes | KeyError: 'target' | deal resolves | test_mna.py::test_seller_side_action_does_not_crash |
| B6 | sim.py:137-142 | card costs are charged even when the budget is gone | Rork spent 210000 of 150000 | <= 150000 | test_budget.py::test_cards_cannot_exceed_budget |
| B7 | sim.py:201 | referral $10 per invite is charged after the budget check | Bolt spent 618360 of 600000 | <= 600000 | test_budget.py::test_referral_cannot_exceed_budget |
| B8 | sim.py:135-136 | after M&A the buyer can spend the target's remaining budget while the target spends it too | group spent 1300000 of 1150000 | <= 1150000 | test_mna.py::test_group_budget_not_double_counted |
| B9 | sim.py:65-76 | the same M&A declared again next quarter is bought and paid again | Lovable spent 1000000, two "купили Rork" logs | one purchase | test_mna.py::test_repeat_declaration_charged_once |
| B10 | sim.py:72-73 | M&A price is not checked against the buyer budget | Lovable spent 5000000 of 1000000 | deal rejected | test_mna.py::test_price_above_budget_rejected |
| B11 | sim.py:114, 177-178 | exclusive partner works in the quarter it is bought; the start quarter `q0` is stored and never read. Card: "Партнёр включается только со следующего квартала" | Base44 Q2 users 13089 with card vs 11611 without | 11611 | test_actions.py::test_exclusive_starts_next_quarter |
| B12 | sim.py:245, 283 | cohort ARPU compares the list price with the cohort ARPU, not with the previous list price; any decoy or upsell premium of existing customers is wiped next quarter with no price change. `prev_price` is tracked and never read | Lovable ARPU Q1 25.456, Q2 25.000 | 25.456 both quarters | test_cohort.py::test_premium_survives_unchanged_price |
| B13 | sim.py:207, 222-224, 277 | custom card with `"as"` applies the mapped card only in conversion; churn (onboarding) and arrivals (free tier) ignore it | v0 paid 2227.5 with onboarding, 2025.0 with custom as onboarding | equal | test_actions.py::test_custom_as_onboarding_cuts_churn |
| B14 | sim.py:80 | unknown company id in a quarter crashes the run | KeyError: 'acme' | skipped with a warning | test_robustness.py::test_unknown_company_skipped |
| B15 | live.py:53-55 | any view name other than public*/sim1 runs the final view: a typo shows revenue to the room. README lists a `wait` view that does not exist | `render wait` writes "Итоги рынка" | pre-game view; unknown view -> error, exit 1 | test_live.py::test_render_wait_and_unknown_view |
| B16 | dashboard.py:70 | public view for a checkpoint nobody submitted crashes | `render public2` before ingest: KeyError: '2' | every card "ход не сдан" | test_live.py::test_public_view_before_ingest |
| B17 | sim.py:338 | efficiency divides by max(1, spent): a team that spends $0 but gains revenue (switching inflow) gets efficiency per $1 and zeroes every other team's efficiency | golden with Rork at zero spend: eff_score Rork 100, all others 0; Lovable final 85.5 -> 70.0 | zero spend -> efficiency 0, others unaffected | test_goals.py::test_zero_spend_does_not_zero_others |
| B18 | dashboard.py:178 | UI uses an en dash as the empty CAC placeholder (UI text rule: no em or en dashes) | U+2013 en dash | ASCII placeholder | test_dashboard.py::test_no_em_or_en_dash |
| B19 | dashboard.py CSS | fixed 3 column grid, 64px heading, 8 column tables and 1280-unit SVG charts at 390px phone width | measured in step 4 by tools/visual_check.py before the fix: 6/6 desktop pages pass, 6/6 phone pages fail; the page scrolls sideways (730 to 924px wide), the card grid is 673 to 868px wide inside 278px, chart text renders at 2.5 to 3.6px | no overflow, no overlap, chart text >= 12px | tools/visual_check.py |
| B20 | sim.py:258, 98, 114, 94 | found while writing tests in step 3: a known card with a missing field (attack or copy without `target`/`seg`, exclusive without `seg`, team_deal without `partner`, mna without `target`) crashes the run | KeyError: 'target' | skipped with a log line | test_robustness.py::test_card_with_missing_fields_skipped |
| B21 | dashboard.py:107 | found by eye in the step 4 screenshots: in the sim 1 users chart, a company with fewer users than at the start has its red start tick to the right of the bar, exactly where the value label starts, so the tick cuts through the number (golden game: v0, 21 803 users, -5%) | tick covers "21 803" | label after the tick | tools/visual_check.py (chart mark check) |

Reproduction commands (repo root, commit `890a721`):

```bash
python3 -c "import extract; print(extract.money('50,000'), extract.money('\$1,200,000'))"            # B1
python3 -c "import extract; print(extract.money('\$29 со скидкой'), extract.money('25 мес'))"        # B2
python3 -c "import sim; sim.run({'quarters':[{'rork':{'spend':{'tiktok':10000}}}]})"                 # B3
python3 -c "import sim; print(sim.run({'quarters':[{'rork':{'actions':[{'id':'bribe'}]}}]})['logs']['rork'])"   # B4
python3 -c "import sim; sim.run({'quarters':[{'lovable':{'actions':[{'id':'mna','target':'rork','price':2000000}]},'rork':{'actions':[{'id':'mna','buyer':'lovable'}]}}]})"   # B5
python3 -c "import sim; r=sim.run({'quarters':[{'rork':{'spend':{'creators':150000}}},{'rork':{'actions':[{'id':'copy','target':'v0','seg':'des'}]}}]}); print(r['hist'][-1]['rork']['spent_total'])"   # B6
python3 -c "import sim; r=sim.run({'quarters':[{'bolt':{'plans':[{'name':'Free','price':0},{'name':'Pro','price':25}],'spend':{'social':580000},'actions':[{'id':'referral'}]}}]}); print(round(r['hist'][-1]['bolt']['spent_total']))"   # B7
python3 -c "
import sim; A=lambda: [{'id':'mna','target':'rork','price':500000}]; S=lambda: [{'id':'mna','buyer':'lovable','target':'lovable'}]
r=sim.run({'quarters':[{'lovable':{'actions':A()},'rork':{'actions':S()}},{'lovable':{'spend':{'social':650000}},'rork':{'spend':{'creators':150000}}}]})
h=r['hist'][-1]; print(h['lovable']['spent_total']+h['rork']['spent_total'])"   # B8
python3 -c "
import sim; A=lambda: [{'id':'mna','target':'rork','price':500000}]; S=lambda: [{'id':'mna','buyer':'lovable','target':'lovable'}]
r=sim.run({'quarters':[{'lovable':{'actions':A()},'rork':{'actions':S()}}]*2}); print(r['hist'][-1]['lovable']['spent_total'], r['logs']['lovable'])"   # B9
python3 -c "
import sim; r=sim.run({'quarters':[{'lovable':{'actions':[{'id':'mna','target':'rork','price':5000000}]},'rork':{'actions':[{'id':'mna','buyer':'lovable','target':'lovable'}]}}]}); print(r['hist'][-1]['lovable']['spent_total'])"   # B10
python3 -c "
import sim
def users(acts): return round(sim.run({'quarters':[{'base44':{'plans':[{'name':'Pro','price':30}],'icp':'smb','spend':{'partners':100000},'actions':acts}},{}]})['hist'][1]['base44']['users'])
print(users([]), users([{'id':'exclusive','seg':'smb'}]))"   # B11
python3 -c "
import sim; P=[{'name':'Pro','price':25}]
r=sim.run({'quarters':[{'lovable':{'plans':P,'spend':{'social':200000},'actions':[{'id':'decoy'}]}},{'lovable':{'plans':P}}]})
print(['%.3f'%(h['lovable']['mrr']/h['lovable']['paid']) for h in r['hist']])"   # B12
python3 -c "
import sim; f=lambda a: sim.run({'quarters':[{'v0':{'actions':[a]}}]})['hist'][0]['v0']['paid']
print(f({'id':'onboarding'}), f({'id':'custom','cost':30000,'as':'onboarding'}))"   # B13
python3 -c "import sim; sim.run({'quarters':[{'acme':{}}]})"   # B14
python3 -c "import sim; sim.run({'quarters':[{'bolt':{'actions':[{'id':'attack','seg':'fnd'}]}}]})"   # B20
python3 live.py reset && for i in 1 2 3; do python3 live.py moves $i samples/moves_cp$i.json; done && python3 live.py render wait /tmp/w.html && grep -o '<title>[^<]*</title>' /tmp/w.html | head -1   # B15
python3 live.py reset && python3 live.py render public2 /tmp/p2.html   # B16
python3 -c "
import sim,json; G=json.load(open('samples/test_moves.json'))
for q in G['quarters']: q['rork']=dict(q['rork'],spend={},actions=[])
f=sim.final_scores(sim.run(G),{'rork':'fnd'}); print({c:round(v,1) for c,v in f['eff_score'].items()}, round(f['final']['lovable'],1))"   # B17
python3 -c "print([n for n,l in enumerate(open('dashboard.py',encoding='utf-8'),1) if chr(0x2013) in l])"   # B18
```

Golden impact measured before fixing: only B12 touches the golden game. With the fix, final Lovable moves from 85.489 to 85.571 and v0 from 74.450 to 74.455; all other goals and finals are unchanged, so the golden test (tolerance 0.1) still holds.

## 4. Design gaps (not fixed, reported)

| ID | Where | Note |
| --- | --- | --- |
| G1 | sim.py:297, spec.py:92-93 | AI cost per user is computed into every snapshot and never used: not in efficiency, not in budget. The free tier card promises a cost ("каждый бесплатный пользователь стоит AI-расходов") that the sim never charges. Using it would change the golden game. |
| G2 | dashboard.py:114-129, live.py | the +5 prediction bonus is shown in sim 1 but never written to `state.bonus`; predictions, bonus and quotes have no CLI command, the host edits state.json by hand. |
| G3 | sim.py:71 | M&A minimum uses the target's list price x current paid users, not its real ARPU. |
| G4 | sim.py:47-48 | pending, comm_bonus and event_bonus arrays have 5 slots: a 4th quarter with community or events spend raises IndexError. The game has 3 quarters. |
| G5 | extract.py:48 | a plan row with a name and an empty price is parsed as a free plan. |
| G6 | sim.py:338-340 | efficiency is normalized to the best team, so one outlier with tiny spend (not zero) still compresses everyone else. B17 fixes only the zero spend case. Measured in reference/calibration.md. |
| G7 | extract.py:3-4 | channel names and ids are duplicated from spec.py; a rename in spec.py silently breaks parsing. Guarded by a test from step 3. |
| G8 | dashboard.py:21, live.py:11, gen_doc.py:133 | all paths are relative to the script directory: state, output and the logo live next to the code. Fixed by the restructure in step 2. |

## 5. Fix status

Every bug had a failing test (strict xfail, or the visual check for B19 and B21) before its fix. Each fix commit removes the marker and keeps the whole suite green.

| ID | Fixed in | Golden game impact |
| --- | --- | --- |
| B1 | 597846c | none |
| B2 | 81c0b74 | none |
| B3 | 1304c80 | none |
| B4 | 1304c80 | none |
| B5 | a3dd6e6 | none |
| B6 | f33d968 | none (Bolt and Base44 Q3 overspend scaling unchanged: 88% and 80%) |
| B7 | 639f2a4 | none |
| B8 | 96346fd | none |
| B9 | 1e43266 | none |
| B10 | ce515be | none |
| B11 | b472c7f | none |
| B12 | 934311d | final Lovable 85.489 -> 85.571, v0 74.450 -> 74.455; inside the 0.1 tolerance |
| B13 | 3af74c1 | none |
| B14 | 9f5df18 | none |
| B15 | 0aa48b1 | none |
| B16 | 992e2fc | none |
| B17 | b071cd7 | none |
| B18 | a00666e | none |
| B19 | b8a26f7 | none (desktop rendering unchanged) |
| B20 | 1304c80 | none |
| B21 | 6fb5bda | none |

Open issues are G1 to G8 above plus the calibration findings in reference/calibration.md.
