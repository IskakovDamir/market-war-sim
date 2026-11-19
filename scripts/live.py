import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
"""Live game state manager.
python3 live.py ingest <cp> <md files...>      -> extracts docs, stores raw + public, prints compact summary
python3 live.py moves <cp> <moves.json>         -> stores sim moves for quarter cp (AI scores etc. from Claude)
python3 live.py render <view> [out]              -> view: wait|public1|public2|public3|sim1|final
python3 live.py sim1split [outdir]               -> simulation 1 as market.html (room) + <company>.html (one per team)
"""
import sys, json, os, re
sys.path.insert(0, BASE)
from extract import extract
import dashboard, sim
ROOT = os.path.dirname(BASE)
LIVE = os.environ.get('MARKET_WAR_LIVE') or os.path.join(ROOT, 'live')
ST = os.path.join(LIVE, 'state.json')
VIEWS = ('wait', 'public1', 'public2', 'public3', 'sim1', 'final')
def load():
    return json.load(open(ST, encoding='utf-8')) if os.path.exists(ST) else dict(public={}, raw={}, quarters=[], seed=7, icps={}, predictions={}, bonus={}, quotes={})
def save(s): os.makedirs(os.path.dirname(ST), exist_ok=True); json.dump(s, open(ST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
def cid_of(name):
    n = name.lower()
    for k, pat in [('lovable','lov'),('bolt','bolt'),('v0','v0'),('base44','base'),('rork','rork')]:
        if pat in n: return k
    return None
def split_h2(s):
    m = re.split(r'(?i)\.?\s*кнопк[аи]\s*:?\s*', s, maxsplit=1)
    return (m[0].strip(), m[1].strip()) if len(m) == 2 else (s, '')
def thousands(d):
    """Teams often write money in thousands ("50" for $50k): if every value is below 1000, scale them all by 1000."""
    return {k: v * 1000 for k, v in d.items()} if d and max(d.values()) < 1000 else d
def tidy(x):
    """Drop a leading field label, stray punctuation and one pair of wrapping quotes from a team answer."""
    x = re.sub(r'^\s*(Заголовок|Подзаголовок|CTA)\s*:\s*', '', (x or '').strip(), flags=re.I).strip()
    x = x.lstrip('.,; ').strip()
    if x.endswith('».') or x.endswith('".'): x = x[:-1]
    return x[1:-1].strip() if x[:1] in '«"' and x[-1:] in '»"' and x.count('«') <= 1 else x
def normalize(d, s, cp, cid):
    """Clean one team's extracted answers in place; an empty public field keeps the previous checkpoint's answer."""
    pr = thousands({cid_of(k): v for k, v in (d.get('predict') or {}).items() if cid_of(k)})
    if pr: s.setdefault('predictions', {})[cid] = pr
    if d.get('spend'): d['spend'] = thousands(d['spend'])
    for k in ('positioning', 'ad', 'h1', 'announce'): d[k] = tidy(d.get(k, ''))
    prev = s['public'].get(str(int(cp) - 1), {}).get(cid, {})
    if prev:
        for k in ('positioning', 'ad', 'h1'):
            if not d.get(k): d[k] = prev.get(k, '')
        if not d.get('h2cta'): d['h2cta'] = prev.get('h2', '') + ' Кнопка: ' + prev.get('cta', '')
        if not d.get('plans'): d['plans'] = prev.get('plans', [])
    h2, cta = split_h2(d.get('h2cta', ''))
    return tidy(re.sub(r'\s*CTA\s*$', '', tidy(h2))), tidy(cta)
if __name__ == '__main__':
    cmd = sys.argv[1]; s = load()
    if cmd == 'ingest':
        cp = sys.argv[2]
        for f in sys.argv[3:]:
            d = extract(open(f, encoding='utf-8').read(), int(cp))
            cid = cid_of(d.get('company', '')) or cid_of(os.path.basename(f))
            if not cid: print('!! не понял компанию', f, d.get('company')); continue
            s['raw'].setdefault(cp, {})[cid] = d   # raw keeps the normalized answers: d is cleaned in place
            h2, cta = normalize(d, s, cp, cid)
            s['public'].setdefault(cp, {})[cid] = dict(positioning=d.get('positioning',''), ad=d.get('ad',''), h1=d.get('h1',''), h2=h2, cta=cta, plans=d.get('plans', []), announce=d.get('announce',''))
            short = {k: v for k, v in d.items() if v and k not in ('company',)}
            print(f'=== {cid}'); print(json.dumps(short, ensure_ascii=False))
        save(s)
    elif cmd == 'moves':
        cp = int(sys.argv[2]); mv = json.load(open(sys.argv[3], encoding='utf-8'))
        while len(s['quarters']) < cp: s['quarters'].append({})
        for cid, m in mv.items():
            if 'plans' not in m:
                m['plans'] = [dict(name=p['name'], price=p['price']) for p in s['public'].get(str(cp), {}).get(cid, {}).get('plans', []) if p['price'] is not None] or [dict(name='Pro', price=sim.CO[cid]['price'])]   # "по запросу" plans stay off the sim
            if 'spend' not in m: m['spend'] = s['raw'].get(str(cp), {}).get(cid, {}).get('spend', {})
            if cp == 1 and m.get('icp'): s['icps'][cid] = m['icp']
            s['quarters'][cp-1][cid] = m
        save(s); print('ok', list(mv))
    elif cmd == 'render':
        view = sys.argv[2]; out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(LIVE, 'index.html')
        if view not in VIEWS:   # never fall through to the final view: it shows revenue to the room
            sys.exit(f"!! неизвестный экран {view}: {' | '.join(VIEWS)}")
        if view in ('sim1', 'final') and not s['quarters']:
            sys.exit('!! нет ходов: сначала live.py moves <cp> <moves.json>')
        if view == 'wait': h = dashboard.view_wait()
        elif view.startswith('public'): h = dashboard.view_public(s, int(view[-1]))
        elif view == 'sim1':
            r = sim.run({'quarters': s['quarters']}, seed=s['seed'], upto=2); h = dashboard.view_sim1(s, r)
            for c, v in r['hist'][-1].items(): print(c, round(v['users']))
        else:   # final
            r = sim.run({'quarters': s['quarters']}, seed=s['seed']); fs = sim.final_scores(r, s['icps']); h = dashboard.view_final(s, r, fs)
            print({k: {c: round(v, 1) for c, v in fs[k].items()} for k in ('goals', 'final')})
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(h); print('rendered', out)
    elif cmd == 'sim1split':
        if not s['quarters']: sys.exit('!! нет ходов: сначала live.py moves <cp> <moves.json>')
        outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'out', 'sim1')
        os.makedirs(outdir, exist_ok=True)
        r = sim.run({'quarters': s['quarters']}, seed=s['seed'], upto=2)
        open(os.path.join(outdir, 'market.html'), 'w', encoding='utf-8').write(dashboard.view_sim1_market(s, r))
        for c in dashboard.ORDER: open(os.path.join(outdir, f'{c}.html'), 'w', encoding='utf-8').write(dashboard.view_sim1_team(s, r, c))
        for c, v in r['hist'][-1].items(): print(c, round(v['users']))
        print('rendered', outdir)
    elif cmd == 'reset':
        if os.path.exists(ST): os.remove(ST)
        print('reset')
