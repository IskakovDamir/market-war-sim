import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
"""GTM war game simulator. Deterministic given inputs + seed.
Input: moves.json = {"quarters":[{company_id: move}, x3 or fewer], "seed": int}
move = {
  "plans": [{"name":"Free","price":0},{"name":"Pro","price":25}],
  "icp": "fnd",
  "scores": {"stud":5,...}        # AI: fit of positioning+ad+landing+pricing per segment, 1-10
  "consistency": 1 | 0.5 | 0,     # AI: positioning vs previous checkpoint
  "spend": {"social": 50000, ...},
  "actions": [{"id":"decoy"}, {"id":"attack","target":"lovable","seg":"fnd"}, {"id":"viral"},
              {"id":"copy","target":"v0","seg":"des"}, {"id":"exclusive","seg":"smb"},
              {"id":"team_deal","partner":"rork","seg":"fnd"}, {"id":"mna","target":"rork","price":60000},
              {"id":"custom","cost":20000,"as":"onboarding"}]
}
"""
import json, math, random, sys, copy
sys.path.insert(0, BASE)
from spec import SEGMENTS, SEG_IDS, COMPANIES, CHANNELS, ACTIONS, PAID_COST, FREE_COST
SEG = {s['id']: s for s in SEGMENTS}
CH = {c['id']: c for c in CHANNELS}
CO = {c['id']: c for c in COMPANIES}
POOL_SHARE = 0.35      # share of a segment choosing a tool each quarter
BASE_CHURN = 0.25      # paid churn per quarter
FREE_CHURN = 0.20
LOOK = 0.10            # share of paid users looking at alternatives each quarter
ACTION_COST = dict(decoy=10000, upsell=15000, referral=20000, viral=50000, onboarding=30000,
                   copy=60000, attack=30000, exclusive=60000)
ASSET_SCORE = dict(bolt=dict(stud=1, dev=1), rork=dict(fnd=1, smb=1))

def chosen_price(plans, seg):
    paid = sorted([p['price'] for p in plans if p['price'] > 0])
    if not paid: return 0
    wtp = SEG[seg]['wtp']
    ok = [p for p in paid if p <= wtp * 1.3]
    return ok[-1] if ok else paid[0]

def has_free(plans): return any(p['price'] == 0 for p in plans)

CARDS = {a['id'] for a in ACTIONS}
CARD_FIELDS = dict(attack=('target', 'seg'), copy=('target', 'seg'), exclusive=('seg',), team_deal=('partner',))

def card_ok(a):
    """A known card with every field it needs, pointing at real companies and segments."""
    if 'seg' in a and a['seg'] not in SEG: return False
    if a['id'] == 'mna':
        return (a.get('target') in CO and 'price' in a) or a.get('buyer') in CO
    return all(a.get(f) in (SEG if f == 'seg' else CO) for f in CARD_FIELDS.get(a['id'], ()))

def clean_move(mv, log, q):
    """Drop unknown channels, unknown cards and cards with missing fields, with a log line each."""
    spend, actions = {}, []
    for ch, amt in mv.get('spend', {}).items():
        if ch in CH: spend[ch] = amt
        else: log.append(f"Q{q}: неизвестный канал «{ch}» пропущен")
    for a in mv.get('actions', []):
        aid = a.get('id')
        if aid not in CARDS: log.append(f"Q{q}: неизвестная карточка «{aid}» пропущена")
        elif not card_ok(a): log.append(f"Q{q}: карточка «{aid}» без нужных полей пропущена")
        else: actions.append(a)
    return dict(mv, spend=spend, actions=actions)

def group_left(st, owner):
    """Budget left for everything one owner controls: its own budget plus every company it bought."""
    return sum(CO[t]['budget'] - st[t]['spent'] for t in st if st[t]['owner'] == owner)

def run(moves, seed=7, upto=None):
    rnd = random.Random(seed)
    Q = moves['quarters'][:upto] if upto else moves['quarters']
    st = {}
    for c in COMPANIES:
        st[c['id']] = dict(paid={s: float(c['paid'][s]) for s in SEG_IDS},
                           free={s: c['free'] * c['paid'][s] / max(1, sum(c['paid'].values())) for s in SEG_IDS},
                           spent=0.0, owner=c['id'], prev_price={s: c['price'] for s in SEG_IDS},
                           pending=[{s: 0.0 for s in SEG_IDS} for _ in range(5)],
                           comm_bonus=[0.0]*5, event_bonus=[{s:0.0 for s in SEG_IDS} for _ in range(5)],
                           exclusive={}, copy_count=0, decoy=False, upsell=False, log=[],
                           arpu={s: float(c['price']) for s in SEG_IDS})
    start_mrr = {c['id']: sum(c['paid'].values()) * c['price'] for c in COMPANIES}
    hist = []
    warnings = []
    excl_by_seg = {}  # seg -> owner for exclusive partner
    prev_moves = {}
    for qi, qmoves in enumerate(Q):
        q = qi + 1
        qmoves = dict(qmoves)
        for cid in [c for c in qmoves if c not in CO]:   # unknown company id: skip, do not crash
            warnings.append(f"Q{q}: неизвестная компания «{cid}» пропущена")
            del qmoves[cid]
        for cid in qmoves: qmoves[cid] = clean_move(qmoves[cid], st[cid]['log'], q)
        for c in COMPANIES:   # a team that did not submit keeps its offer and spends nothing
            cid = c['id']
            if cid not in qmoves:
                base = prev_moves.get(cid, dict(plans=[{'name': 'Pro', 'price': c['price']}], icp='fnd', scores={}, consistency=1))
                qmoves[cid] = dict(base, spend={}, actions=[], consistency=1)
        prev_moves = qmoves
        # ---------- resolve deals (M&A) ----------
        for cid, mv in qmoves.items():
            for a in mv.get('actions', []):
                if a['id'] == 'mna' and 'buyer' not in a:   # the seller's card only marks consent
                    t = a['target']
                    if st[t]['owner'] == cid: continue   # already ours: the same deal written again costs nothing
                    if t == cid or st[t]['owner'] != t or st[cid]['owner'] != cid:
                        st[cid]['log'].append(f"Q{q}: сделка с {CO[t]['name']} не засчитана: одна из компаний уже куплена")
                        continue
                    tm = qmoves.get(t, {})
                    agreed = any(x['id'] == 'mna' and x.get('buyer') == cid for x in tm.get('actions', []))
                    min_price = 3 * 3 * sum(st[t]['paid'][s] for s in SEG_IDS) * CO[t]['price']
                    left = group_left(st, cid)
                    if agreed and min_price * 0.999 <= a['price'] <= left:
                        for x in st:   # the target and anything it owned now belong to the buyer
                            if st[x]['owner'] == t: st[x]['owner'] = cid
                        st[cid]['spent'] += a['price']
                        st[cid]['log'].append(f"Q{q}: купили {CO[t]['name']} за ${a['price']:,.0f}")
                    elif agreed and a['price'] > left:
                        st[cid]['log'].append(f"Q{q}: сделка с {CO[t]['name']} не засчитана: цена ${a['price']:,.0f} больше остатка бюджета ${left:,.0f}")
                    else:
                        st[cid]['log'].append(f"Q{q}: сделка с {CO[t]['name']} не засчитана (нет согласия или цена ниже ${min_price:,.0f})")
        # ---------- effective scores ----------
        score = {}
        for cid, mv in qmoves.items():
            sc = {s: float(mv.get('scores', {}).get(s, 5)) for s in SEG_IDS}
            for s, b in ASSET_SCORE.get(cid, {}).items(): sc[s] += b
            for s in SEG_IDS: sc[s] += st[cid]['event_bonus'][q][s]
            cons = mv.get('consistency', 1)
            if cons == 0:
                for s in SEG_IDS: sc[s] -= 1
            if mv.get('spend', {}).get('telegram', 0) > 60000:
                for s in SEG_IDS: sc[s] -= 1
                st[cid]['log'].append(f"Q{q}: перебор с Telegram, −1 к оценке")
            if st[cid].get('overpromise_hit_q') == q:
                for s in SEG_IDS: sc[s] -= 1
            for a in mv.get('actions', []):
                if a['id'] == 'team_deal':
                    p = a.get('partner'); pm = qmoves.get(p, {})
                    if any(x['id'] == 'team_deal' and x.get('partner') == cid for x in pm.get('actions', [])):
                        sc[a.get('seg', mv.get('icp'))] += 0.5
                if a['id'] == 'copy':
                    st[cid]['copy_count'] += 1
                    sc[a['seg']] += 1
            score[cid] = sc
        # copy effect on targets (asset halved)
        for cid, mv in qmoves.items():
            for a in mv.get('actions', []):
                if a['id'] == 'copy' and a['target'] in score:
                    b = ASSET_SCORE.get(a['target'], {}).get(a['seg'], 0)
                    score[a['target']][a['seg']] -= b * 0.5
                if a['id'] == 'copy' and st[cid]['copy_count'] >= 2:
                    for s in SEG_IDS: score[cid][s] -= 0.5
        for cid in score:
            for s in SEG_IDS: score[cid][s] = max(1.0, min(10.0, score[cid][s]))
        # exclusive partners
        for cid, mv in qmoves.items():
            for a in mv.get('actions', []):
                if a['id'] == 'exclusive':
                    excl_by_seg.setdefault(a['seg'], (cid, q))
        # ---------- auction pressure ----------
        targeting = {}
        for cid, mv in qmoves.items():
            for ch, amt in mv.get('spend', {}).items():
                if ch in ('social', 'search') and amt >= CH[ch]['min_k'] * 1000:
                    targeting.setdefault((ch, mv.get('icp')), set()).add(cid)
        # ---------- acquisition ----------
        arrivals = {cid: {s: 0.0 for s in SEG_IDS} for cid in st}
        sales_arr = {cid: {s: 0.0 for s in SEG_IDS} for cid in st}
        q_spend = {}
        for cid, mv in qmoves.items():
            spend = dict(mv.get('spend', {}))
            act_cost = 0
            for a in mv.get('actions', []):
                if a['id'] == 'custom': act_cost += max(20000, a.get('cost', 20000))
                elif a['id'] == 'decoy' and st[cid]['decoy']: pass
                else: act_cost += ACTION_COST.get(a['id'], 0)
            total = sum(spend.values()) + act_cost
            budget_left = group_left(st, st[cid]['owner'])   # buyer and bought companies share one pool
            if total > budget_left and total > 0:
                k = max(0.0, (budget_left - act_cost) / max(1, sum(spend.values())))
                spend = {ch: v * k for ch, v in spend.items()}
                st[cid]['log'].append(f"Q{q}: перерасход, траты на каналы урезаны до {k:.0%}")
                total = sum(spend.values()) + act_cost
            st[cid]['spent'] += total; q_spend[cid] = total
            icp = mv.get('icp', 'fnd')
            cons = mv.get('consistency', 1)
            pen = 1.25 if cons == 0 else (1.10 if cons == 0.5 else 1.0)
            for ch, amt in spend.items():
                if amt <= 0: continue
                C = CH[ch]
                eff_amt = amt if amt >= C['min_k'] * 1000 else amt * 0.3
                if amt < C['min_k'] * 1000:
                    st[cid]['log'].append(f"Q{q}: {C['name']}: ставка ниже минимальной, эффект 30%")
                valid = [s for s in SEG_IDS if C['cpu'][s] is not None]
                if ch == 'sales' and max([p['price'] for p in mv.get('plans', [])] + [0]) < 50:
                    st[cid]['log'].append(f"Q{q}: Продажи без тарифа от $50: канал не сработал")
                    continue
                nat = {s: SEG[s]['size'] / ((C['cpu'][s][0] + C['cpu'][s][1]) / 2) for s in valid}
                tot = sum(nat.values())
                alloc = {s: eff_amt * (1 - C['target']) * nat[s] / tot for s in valid}
                if icp in valid: alloc[icp] += eff_amt * C['target']
                else:
                    for s in valid: alloc[s] += eff_amt * C['target'] * 0.5 * nat[s] / tot
                u = rnd.uniform(-1, 1)
                for s, a_amt in alloc.items():
                    lo, hi = C['cpu'][s]
                    sc = score[cid][s]
                    cpu = hi - (hi - lo) * (sc - 1) / 9
                    cpu *= pen
                    if ch in ('social', 'search'):
                        n = len(targeting.get((ch, s), set()) - {cid})
                        cpu *= (1 + 0.15 * n)
                    if ch == 'geo': cpu /= (1 + 0.2 * (q - 1))
                    if ch == 'community' and cid == 'lovable': cpu *= 0.7
                    if ch == 'partners':
                        if cid == 'v0' and s in ('des', 'dev'): cpu *= 0.6
                        if cid == 'base44' and s == 'smb': cpu *= 0.6
                        if s in excl_by_seg:
                            owner, q0 = excl_by_seg[s]
                            cpu *= 0.6 if owner == cid else 1.3
                    n_users = a_amt / cpu * (1 + C['var'] * u)
                    for d, frac in enumerate(C['delay']):
                        if ch == 'sales':
                            st[cid]['pending'][q + d - 1][s] += 0  # handled below
                        st[cid]['pending'][q + d - 1][s] += n_users * frac if ch != 'sales' else 0
                    if ch == 'sales': sales_arr[cid][s] += n_users
                if ch == 'community':
                    st[cid]['comm_bonus'][q] = 0.2; st[cid]['comm_bonus'][q + 1] = 0.2
                if ch == 'events':
                    st[cid]['event_bonus'][q + 1][icp] += 0.5
            # viral
            for a in mv.get('actions', []):
                if a['id'] == 'viral':
                    roll = rnd.randint(1, 6)
                    extra = 15000 if roll >= 5 else 2000
                    st[cid]['log'].append(f"Q{q}: вирусная акция, кубик {roll}: +{extra:,} пользователей")
                    C = CH['shorts']; nat = {s: SEG[s]['size'] / sum(C['cpu'][s]) for s in SEG_IDS}; tot = sum(nat.values())
                    for s in SEG_IDS: st[cid]['pending'][q - 1][s] += extra * nat[s] / tot
                if a['id'] == 'referral':
                    active = sum(st[cid]['paid'].values()) + sum(st[cid]['free'].values())
                    avg_sc = sum(score[cid].values()) / 5
                    ref = active * 0.06 * (avg_sc / 6)
                    st[cid]['spent'] += ref * 10; q_spend[cid] += ref * 10
                    mix = {s: st[cid]['paid'][s] + st[cid]['free'][s] for s in SEG_IDS}; mt = sum(mix.values()) or 1
                    for s in SEG_IDS: st[cid]['pending'][q - 1][s] += ref * mix[s] / mt
                    st[cid]['log'].append(f"Q{q}: рефералка привела {ref:,.0f} пользователей")
            for s in SEG_IDS:
                arrivals[cid][s] = st[cid]['pending'][q - 1][s]
                if any(a['id'] == 'free_tier' for a in mv.get('actions', [])): arrivals[cid][s] *= 1.4
                if not has_free(mv.get('plans', [])): arrivals[cid][s] *= 0.6
        # companies without moves (should not happen) keep state
        # ---------- pool cap ----------
        for s in SEG_IDS:
            pool = SEG[s]['size'] * POOL_SHARE
            tot = sum(arrivals[c][s] + sales_arr[c][s] for c in arrivals)
            if tot > pool:
                k = pool / tot
                for c in arrivals: arrivals[c][s] *= k; sales_arr[c][s] *= k
        # ---------- conversion ----------
        new_paid = {}; arpu = {}
        for cid, mv in qmoves.items():
            plans = mv.get('plans', [{'name': 'Pro', 'price': CO[cid]['price']}])
            acts = {a['id'] for a in mv.get('actions', [])}
            if 'custom' in acts:
                for a in mv['actions']:
                    if a['id'] == 'custom' and a.get('as'): acts.add(a['as'])
            if 'decoy' in acts: st[cid]['decoy'] = True
            if 'upsell' in acts: st[cid]['upsell'] = True
            new_paid[cid] = {}; arpu[cid] = {}
            for s in SEG_IDS:
                price = chosen_price(plans, s)
                if price == 0:
                    rate = 0
                else:
                    pf = max(0.3, min(1.5, (SEG[s]['wtp'] / price) ** 0.7))
                    rate = SEG[s]['base_paid'] * pf * (0.7 + 0.06 * score[cid][s])
                    if 'free_tier' in acts: rate *= 0.75
                    if 'onboarding' in acts: rate *= 1.10
                    if 'overpromise' in acts: rate *= 1.30
                    if not has_free(plans): rate *= 1.4
                    rate = min(rate, 0.9)
                np_ = arrivals[cid][s] * rate + (sales_arr[cid][s] * 0.6 if price > 0 else 0)
                new_paid[cid][s] = np_
                if price > 0:
                    pnew = price * (1.15 if st[cid]['decoy'] else 1) * (1.10 if st[cid]['upsell'] else 1)
                    old = st[cid]['paid'][s]; a_old = st[cid]['arpu'][s]
                    if price < a_old: a_old = price   # price cut reaches existing customers
                    st[cid]['arpu'][s] = (old * a_old + np_ * pnew) / max(1e-9, old + np_)
                st[cid]['paid'][s] += np_
                st[cid]['free'][s] += arrivals[cid][s] * (1 - rate) + sales_arr[cid][s] * 0.4
                if 'overpromise' in acts:
                    st[cid]['over_paid'] = st[cid].get('over_paid', 0) + np_
            if 'overpromise' in acts: st[cid]['overpromise_hit_q'] = q + 1
        # ---------- switching ----------
        moves_sw = {c: {s: 0.0 for s in SEG_IDS} for c in st}
        for s in SEG_IDS:
            for cid in qmoves:
                look = st[cid]['paid'][s] * LOOK
                attackers = [a_c for a_c, mv in qmoves.items() for a in mv.get('actions', [])
                             if a['id'] == 'attack' and a['target'] == cid and a['seg'] == s]
                for a_c in attackers:
                    if score[a_c][s] > score[cid][s]:
                        moves_sw[cid][s] -= look; moves_sw[a_c][s] += look
                        st[a_c]['log'].append(f"Q{q}: атака на {CO[cid]['name']} сработала: +{look:,.0f} платящих")
                    else:
                        loss = st[a_c]['paid'][s] * 0.05
                        moves_sw[a_c][s] -= loss; moves_sw[cid][s] += loss
                        st[a_c]['log'].append(f"Q{q}: атака на {CO[cid]['name']} ударила по вам: −{loss:,.0f} платящих")
                def attr(c):
                    p = chosen_price(qmoves[c].get('plans', []), s) or 999
                    return score[c][s] - 0.5 * math.log(max(1, p) / max(1, SEG[s]['wtp']), 2)
                best = max((c for c in qmoves if c != cid), key=attr)
                if attr(best) - attr(cid) >= 1.0:
                    moves_sw[cid][s] -= look; moves_sw[best][s] += look
        for c in moves_sw:
            for s in SEG_IDS: st[c]['paid'][s] = max(0, st[c]['paid'][s] + moves_sw[c][s])
        # ---------- churn ----------
        for cid, mv in qmoves.items():
            acts = {a['id'] for a in mv.get('actions', [])}
            ch = BASE_CHURN * (1 - st[cid]['comm_bonus'][q])
            if 'onboarding' in acts: ch *= 0.7
            for s in SEG_IDS:
                st[cid]['paid'][s] *= (1 - ch)
                st[cid]['free'][s] *= (1 - FREE_CHURN)
                st[cid]['prev_price'][s] = chosen_price(mv.get('plans', []), s) or st[cid]['prev_price'][s]
            if st[cid].get('over_paid') and st[cid].get('overpromise_hit_q') == q + 1:
                tot_p = sum(st[cid]['paid'].values()) or 1
                lose = st[cid]['over_paid'] * 0.5
                for s in SEG_IDS: st[cid]['paid'][s] -= lose * st[cid]['paid'][s] / tot_p
                st[cid]['log'].append(f"Q{q}: возвраты после обещания сверх продукта: −{lose:,.0f} платящих")
                st[cid]['over_paid'] = 0
        # ---------- metrics ----------
        snap = {}
        for cid, mv in qmoves.items():
            mrr = sum(st[cid]['paid'][s] * st[cid]['arpu'][s] for s in SEG_IDS)
            seg_rev = {s: st[cid]['paid'][s] * st[cid]['arpu'][s] for s in SEG_IDS}
            paid = sum(st[cid]['paid'].values()); free = sum(st[cid]['free'].values())
            npaid = sum(new_paid[cid].values())
            ai_cost = 3 * (paid * PAID_COST[cid] + free * FREE_COST[cid])
            snap[cid] = dict(users=paid + free, paid=paid, mrr=mrr, seg_rev=seg_rev, new_paid=npaid,
                             spend=q_spend[cid], cac=q_spend[cid] / npaid if npaid > 1 else None,
                             ai_cost=ai_cost, score=dict(score[cid]), spent_total=st[cid]['spent'],
                             budget_left=CO[cid]['budget'] - st[cid]['spent'],
                             seg_paid=dict(st[cid]['paid']), seg_arpu=dict(st[cid]['arpu']),
                             arrivals={s: arrivals[cid][s] + sales_arr[cid][s] for s in SEG_IDS})
        hist.append(snap)
    return dict(hist=hist, start_mrr=start_mrr, logs={c: st[c]['log'] for c in st},
                owners={c: st[c]['owner'] for c in st}, warnings=warnings)

def final_scores(res, icps):
    """icps: company -> chosen ICP seg at checkpoint 1 (for the newcomer)"""
    last = res['hist'][-1]; start = res['start_mrr']
    owners = res['owners']
    grp = {}
    for c in last: grp.setdefault(owners[c], []).append(c)
    def g_mrr(o): return sum(last[c]['mrr'] for c in grp.get(o, []))
    def g_seg(o, s): return sum(last[c]['seg_rev'][s] for c in grp.get(o, []))
    tot = sum(last[c]['mrr'] for c in last)
    tot0 = sum(start.values())
    seg_tot = {s: sum(last[c]['seg_rev'][s] for c in last) for s in SEG_IDS}
    goals = {}
    for o in grp:
        share = g_mrr(o) / tot * 100
        if o == 'lovable':
            goals[o] = max(0, 100 - 6 * max(0, 40 - share))
        elif o == 'bolt':
            mult = g_mrr(o) / sum(start[c] for c in grp[o])
            goals[o] = max(0, min(100, 100 * (mult - 1) / 1.0))
        elif o in ('v0', 'base44'):
            s = 'des' if o == 'v0' else 'smb'
            mine = g_seg(o, s); best = max(g_seg(x, s) for x in grp)
            goals[o] = 100 if mine >= best else 100 * mine / best
        else:
            s = icps.get(o, 'fnd')
            sh = g_seg(o, s) / max(1, seg_tot[s])
            goals[o] = min(100, 100 * sh / 0.20)
    eff = {}
    for o in grp:
        rev3 = sum(sum(h[c]['mrr'] for c in grp[o]) for h in res['hist']) * 3
        base3 = sum(start[c] for c in grp[o]) * 3 * len(res['hist'])
        spent = sum(res['hist'][-1][c]['spent_total'] for c in grp[o])
        eff[o] = (rev3 - base3) / max(1, spent)
    mx = max(eff.values())
    effs = {o: max(0, 100 * eff[o] / mx) if mx > 0 else 0 for o in eff}
    final = {o: 0.7 * goals[o] + 0.3 * effs[o] for o in grp}
    for c in last:
        if owners[c] != c: final[c] = final[owners[c]]; goals[c] = goals[owners[c]]; effs[c] = effs[owners[c]]; eff[c] = eff[owners[c]]
    return dict(goals=goals, eff=eff, eff_score=effs, final=final)
