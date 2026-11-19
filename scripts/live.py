import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
"""Live game state manager.
python3 live.py ingest <cp> <md files...>      -> extracts docs, stores raw + public, prints compact summary
python3 live.py moves <cp> <moves.json>         -> stores sim moves for quarter cp (AI scores etc. from Claude)
python3 live.py render <view> [out]              -> view: wait|public1|public2|public3|sim1|final
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
if __name__ == '__main__':
    cmd = sys.argv[1]; s = load()
    if cmd == 'ingest':
        cp = sys.argv[2]
        for f in sys.argv[3:]:
            d = extract(open(f, encoding='utf-8').read(), int(cp))
            cid = cid_of(d.get('company', '')) or cid_of(os.path.basename(f))
            if not cid: print('!! не понял компанию', f, d.get('company')); continue
            s['raw'].setdefault(cp, {})[cid] = d
            h2, cta = split_h2(d.get('h2cta', ''))
            s['public'].setdefault(cp, {})[cid] = dict(positioning=d.get('positioning',''), ad=d.get('ad',''), h1=d.get('h1',''), h2=h2, cta=cta, plans=d.get('plans', []), announce=d.get('announce',''))
            short = {k: v for k, v in d.items() if v and k not in ('company',)}
            print(f'=== {cid}'); print(json.dumps(short, ensure_ascii=False))
        save(s)
    elif cmd == 'moves':
        cp = int(sys.argv[2]); mv = json.load(open(sys.argv[3], encoding='utf-8'))
        while len(s['quarters']) < cp: s['quarters'].append({})
        for cid, m in mv.items():
            if 'plans' not in m:
                m['plans'] = [dict(name=p['name'], price=p['price']) for p in s['public'].get(str(cp), {}).get(cid, {}).get('plans', [])] or [dict(name='Pro', price=sim.CO[cid]['price'])]
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
    elif cmd == 'reset':
        if os.path.exists(ST): os.remove(ST)
        print('reset')
