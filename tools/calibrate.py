"""Calibration: does the sim reward sensible play? Read only, changes nothing.

python3 tools/calibrate.py            # prints a markdown table

For each company, replace its three moves in the golden game (samples/test_moves.json,
seed 7, Rork ICP fnd) with one strategy while the other four teams play their golden moves:

  golden     the golden moves as written
  focused    golden plans, scores, ICP and cards; each quarter's golden channel budget goes
             to the two channels that buy the most ICP users per dollar (60/40)
  spray      same budget and cards, split evenly over all 12 channels
  overpromise golden moves plus the overpromise card every quarter
  zero       golden plans and scores, no spend and no cards in any quarter
  minimal    probe, not a sanity check: $5k on Telegram (its min bid) in quarter 1, nothing else

Sanity expectations: focused beats spray; overpromise and zero spend do not beat the
golden moves or focused, and do not finish first.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import sim  # noqa: E402
from spec import CHANNELS, COMPANIES, SEGMENTS  # noqa: E402

CH = {c['id']: c for c in CHANNELS}
SEG = {s['id']: s for s in SEGMENTS}
CIDS = [c['id'] for c in COMPANIES]
ICPS = {'rork': 'fnd'}
STRATEGIES = ['golden', 'focused', 'spray', 'overpromise', 'zero', 'minimal']


def golden():
    return json.load(open(os.path.join(ROOT, 'samples', 'test_moves.json'), encoding='utf-8'))


def value(ch, cid, mv, q):
    """ICP users that land inside the game per dollar, sales weighted by its 60% paid share."""
    C, icp = CH[ch], mv['icp']
    if C['cpu'][icp] is None:
        return 0.0
    if ch == 'sales' and max([p['price'] for p in mv['plans']] + [0]) < 50:
        return 0.0
    lo, hi = C['cpu'][icp]
    sc = mv['scores'].get(icp, 5) + sim.ASSET_SCORE.get(cid, {}).get(icp, 0)
    cpu = hi - (hi - lo) * (sc - 1) / 9
    if ch == 'geo':
        cpu /= 1 + 0.2 * (q - 1)
    if ch == 'community' and cid == 'lovable':
        cpu *= 0.7
    if ch == 'partners' and ((cid == 'v0' and icp in ('des', 'dev')) or (cid == 'base44' and icp == 'smb')):
        cpu *= 0.6
    landed = sum(f for d, f in enumerate(C['delay']) if q + d <= 3)
    paid_weight = 0.6 / SEG[icp]['base_paid'] if ch == 'sales' else 1.0
    return C['target'] * landed / cpu * paid_weight


def focused(cid, mv, q):
    total = sum(mv['spend'].values())
    best = sorted(CH, key=lambda ch: -value(ch, cid, mv, q))[:2]
    a, b = best
    spend = {a: total * 0.6, b: total * 0.4}
    if spend[b] < CH[b]['min_k'] * 1000:   # second channel below its min bid: all in the best one
        spend = {a: total}
    for ch in list(spend):
        if ch == 'telegram' and spend[ch] > 60000:   # stay under the spam threshold
            other = b if ch == a else a
            spend[other] = spend.get(other, 0) + spend[ch] - 60000
            spend[ch] = 60000
    return spend


def play(cid, strategy):
    g = golden()
    for qi, quarter in enumerate(g['quarters']):
        mv = quarter[cid]
        q = qi + 1
        if strategy == 'focused':
            quarter[cid] = dict(mv, spend=focused(cid, mv, q))
        elif strategy == 'spray':
            total = sum(mv['spend'].values())
            quarter[cid] = dict(mv, spend={ch: total / len(CH) for ch in CH})
        elif strategy == 'overpromise':
            quarter[cid] = dict(mv, actions=mv['actions'] + [{'id': 'overpromise'}])
        elif strategy == 'zero':
            quarter[cid] = dict(mv, spend={}, actions=[])
        elif strategy == 'minimal':
            quarter[cid] = dict(mv, spend={'telegram': 5000} if q == 1 else {}, actions=[])
    res = sim.run(g)
    fs = sim.final_scores(res, ICPS)
    rank = sorted(CIDS, key=lambda c: -fs['final'][c]).index(cid) + 1
    last = res['hist'][-1][cid]
    others = max(fs['eff_score'][c] for c in CIDS if c != cid)
    return dict(final=fs['final'][cid], goal=fs['goals'][cid], eff=fs['eff_score'][cid], rank=rank, others=others,
                mrr=last['mrr'], spent=last['spent_total'], moves=g['quarters'])


def main():
    rows, issues = [], []
    for cid in CIDS:
        r = {s: play(cid, s) for s in STRATEGIES}
        for s in STRATEGIES:
            x = r[s]
            rows.append(f"| {cid} | {s} | {x['final']:.1f} | {x['goal']:.1f} | {x['eff']:.1f} | {x['others']:.1f} | {x['rank']} | "
                        f"${x['mrr'] / 1000:,.0f}k | ${x['spent'] / 1000:,.0f}k |")
        if not r['focused']['final'] > r['spray']['final']:
            issues.append(f"{cid}: focused {r['focused']['final']:.1f} does not beat spray {r['spray']['final']:.1f}")
        for s in ('overpromise', 'zero'):
            for ref in ('golden', 'focused'):
                if r[s]['final'] > r[ref]['final']:
                    issues.append(f"{cid}: {s} {r[s]['final']:.1f} beats {ref} {r[ref]['final']:.1f}")
            if r[s]['rank'] == 1:
                issues.append(f"{cid}: {s} finishes first")
        focus_q = [sorted(q[cid]['spend']) for q in r['focused']['moves']]
        rows.append(f"| {cid} | (focused channels Q1 / Q2 / Q3) | {' / '.join('+'.join(c) for c in focus_q)} | | | | | | |")
    print('| Company | Strategy | Final | Goal | Efficiency | Best rival efficiency | Rank | MRR Q3 | Spent |')
    print('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    print('\n'.join(rows))
    print()
    print('Sanity failures:' if issues else 'Sanity: all expectations hold.')
    for i in issues:
        print('-', i)


if __name__ == '__main__':
    main()
