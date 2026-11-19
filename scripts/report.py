import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
import json, sys
sys.path.insert(0,BASE)
import sim
def show(m, icps={'rork':'fnd'}, seed=7):
    r=sim.run(m, seed=seed)
    for qi,h in enumerate(r['hist']):
        tot=sum(v['mrr'] for v in h.values())
        print('Q',qi+1, 'total MRR', round(tot))
        for c,v in h.items():
            print(f"  {c:8s} users {v['users']:9,.0f} paid {v['paid']:8,.0f} mrr {v['mrr']:9,.0f} share {v['mrr']/tot*100:5.1f}% newpaid {v['new_paid']:7,.0f} spend {v['spend']:8,.0f} cac {v['cac'] or 0:6.0f} left {v['budget_left']:9,.0f}")
    f=sim.final_scores(r,icps)
    for k in f: print(k,{c:round(v,1) for c,v in f[k].items()})
    for c,l in r['logs'].items():
        if l: print(c,l)
    return r,f
if __name__=='__main__':
    show(json.load(open(sys.argv[1], encoding='utf-8')))
