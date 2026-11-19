import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
"""Render live game screens as one self-contained HTML page.
views: public(cp) | sim1 | final
"""
import json, sys, html, math
sys.path.insert(0, BASE)
import sim
from spec import COMPANIES, SEGMENTS
CO = {c['id']: c for c in COMPANIES}
SEGN = {s['id']: s['name'] for s in SEGMENTS}
ORDER = ['lovable', 'bolt', 'v0', 'base44', 'rork']
INIT = dict(lovable='L', bolt='B', v0='v0', base44='44', rork='R')
SER = dict(lovable='#2a78d6', bolt='#eb6834', v0='#1baf7a', base44='#eda100', rork='#e87ba4')
E = html.escape
def fmt(n): return f"{n:,.0f}".replace(',', ' ')
import re as _re
def nice(mx, n=5):
    raw = mx / n; mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw: step = m * mag; break
    return step, step * math.ceil(mx / step)
ROOT = _os.path.dirname(BASE)
LOGO = open(_os.path.join(ROOT, 'assets', 'nf_logo_b64.txt'), encoding='utf-8').read().strip()
def money(n):
    return f"${n/1e6:.2f}M" if n >= 1e6 else f"${n/1e3:.0f}k"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#F5F7FB;color:#04131B;font-family:Manrope,'Segoe UI',system-ui,-apple-system,sans-serif;padding:40px 56px 64px}
.top{display:flex;align-items:center;gap:14px;margin-bottom:28px}
table.t th.n{text-align:right}
.brand{font-weight:600;font-size:20px;letter-spacing:-.02em}
.when{margin-left:auto;color:#5B6675;font-size:18px}
h1{font-weight:500;font-size:64px;letter-spacing:-.04em;line-height:1.04}
h1 span{color:#F5000D;display:block}
.sub{color:#5B6675;font-size:22px;margin:14px 0 32px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.card{background:#fff;border-radius:18px;padding:26px 28px}
.head{display:flex;align-items:center;gap:14px;margin-bottom:18px}
.ini{width:52px;height:52px;border-radius:13px;border:2px solid #E6ECF5;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:19px;flex:none}
.name{font-size:26px;font-weight:600;letter-spacing:-.02em}
.pos{font-size:17px;font-weight:600;color:#F5000D}
.lbl{font-size:16px;font-weight:600;color:#5B6675;margin:16px 0 6px}
.pv{font-size:22px;font-weight:500;line-height:1.3}
.ad{font-size:19px;line-height:1.4}
.fs b{display:block;font-size:20px}.fs i{font-style:normal;color:#5B6675;font-size:17px;display:block;margin:4px 0}.fs u{text-decoration:none;color:#F5000D;font-weight:600;font-size:17px}
.plans{width:100%;border-collapse:collapse;font-size:18px}.plans td{padding:6px 0;border-top:1px solid #E6ECF5}.plans td:last-child{text-align:right;font-weight:600}
.chg{color:#F5000D;font-size:15px;font-weight:600;margin-left:auto}
.wide{background:#fff;border-radius:18px;padding:30px 34px;margin-bottom:22px}
table.t{width:100%;border-collapse:collapse;font-size:19px}
table.t th{text-align:left;color:#5B6675;font-weight:600;font-size:16px;padding:8px 10px;border-bottom:2px solid #E6ECF5}
table.t td{padding:12px 10px;border-bottom:1px solid #E6ECF5;vertical-align:middle}
table.t td.n{text-align:right;font-variant-numeric:tabular-nums}
.rk{font-size:30px;font-weight:500;color:#5B6675}
.bar{height:14px;border-radius:4px;background:#E6ECF5;position:relative;min-width:220px}.bar>i{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:#F5000D}
.small{color:#5B6675;font-size:16px}
.log{font-size:16px;color:#5B6675;line-height:1.5}
.q{font-size:18px;line-height:1.45;margin-top:8px}
.legend{display:flex;gap:22px;flex-wrap:wrap;font-size:17px;margin:6px 0 10px}.legend span{display:flex;align-items:center;gap:8px}.legend i{width:22px;height:4px;border-radius:2px;display:inline-block}
svg text{font-family:inherit}
.tm{display:grid;grid-template-columns:44px 250px minmax(0,1.25fr) minmax(0,1fr) 190px;grid-template-areas:"rk co gl sf sc" "rk co gl sf sb";grid-template-rows:auto 1fr;column-gap:24px;padding:24px 0;border-top:1px solid #E6ECF5}
.tm:first-child{border-top:0;padding-top:6px}
.tm>.rk{grid-area:rk;line-height:52px}.tm.win>.rk{color:#F5000D}
.tm>.co{grid-area:co}.tm>.gl{grid-area:gl}.tm>.sf{grid-area:sf}.tm>.sc{grid-area:sc}.tm>.sb{grid-area:sb}
.tm .lbl{margin-top:0}
.war{font-size:16px;color:#5B6675;margin-top:10px}
.gt{font-size:17px;line-height:1.4}
.gm{font-size:18px;line-height:1.45;margin-top:10px}.gm b{font-variant-numeric:tabular-nums}
.gm i{font-style:normal;display:block;color:#5B6675;font-size:16px}
.sf{font-size:17px;line-height:1.8;font-variant-numeric:tabular-nums}.sf span{color:#5B6675}
.sc{text-align:right;font-size:44px;font-weight:600;line-height:1}
.sb .bar{min-width:0;margin:14px 0 10px}.sb .small{text-align:right;font-size:15px;line-height:1.45}
.mob{display:none}
@media (max-width:700px){
body{padding:20px 16px 40px}
.top{flex-wrap:wrap;gap:10px;margin-bottom:20px}.top img{width:32px;height:32px}
.brand{font-size:16px}.when{flex-basis:100%;margin-left:0;font-size:14px}
h1{font-size:38px;line-height:1.08}
.sub{font-size:17px;margin:10px 0 22px}
.grid{grid-template-columns:1fr;gap:14px}
.card{padding:20px 18px}.wide{padding:20px 16px;margin-bottom:14px}
.name{font-size:22px}.pv{font-size:19px}.ad{font-size:17px}.fs b{font-size:18px}.plans{font-size:16px}.chg{font-size:13px}
.desk{display:none}.mob{display:block}
table.t{font-size:16px}
.tm{grid-template-columns:28px 1fr auto;grid-template-areas:"rk co sc" "sb sb sb" "gl gl gl" "sf sf sf";grid-template-rows:auto;row-gap:12px;column-gap:10px;padding:20px 0}
.sc{font-size:34px;line-height:52px}.sb .bar{margin:0 0 8px}.sb .small{text-align:left;font-size:14px;display:flex;flex-wrap:wrap;column-gap:14px}
.gm{font-size:17px}.sf{font-size:16px;line-height:1.7}
table.rank tr:first-child,table.nums tr:first-child{display:none}
table.rank tr{display:grid;grid-template-columns:28px 1fr auto;grid-template-areas:"rk co sc" "bar bar bar" "det det det";align-items:center;column-gap:10px;padding:12px 0;border-bottom:1px solid #E6ECF5}
table.rank td{display:block;padding:0;border:0}
table.rank td.rk{grid-area:rk;font-size:24px}table.rank td:nth-child(2){grid-area:co}
table.rank td:nth-child(3){grid-area:bar;padding:10px 0 6px}table.rank td:nth-child(4){grid-area:sc}table.rank td:nth-child(5){grid-area:det}
.bar{min-width:0}
table.nums tr{display:grid;grid-template-columns:1fr 1fr;column-gap:16px;padding:12px 0;border-bottom:1px solid #E6ECF5}
table.nums td{display:flex;justify-content:space-between;gap:8px;padding:3px 0;border:0}
table.nums td:first-child{grid-column:1/-1;font-weight:600;font-size:18px}table.nums td:last-child{grid-column:1/-1;padding-top:6px}
table.nums td.n::before{content:attr(data-label);color:#5B6675;font-size:14px;text-align:left}
}
"""
def page(title, body, when):
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><div class="top"><img src="data:image/png;base64,{LOGO}" width="40" height="40" alt="nFactorial"><div class="brand">nFactorial · рыночная война</div><div class="when">{E(when)}</div></div>{body}</body></html>"""

def head(cid):
    c = CO[cid]
    return f'<div class="head" data-company="{cid}"><div class="ini">{INIT[cid]}</div><div><div class="name">{E(c["name"])}</div><div class="pos">{E(c["pos"].lower())}</div></div>'

def view_public(state, cp):
    pub = state.get('public', {}).get(str(cp), {})   # nobody submitted yet: every card says so
    prev = state.get('public', {}).get(str(cp - 1), {})
    cards = []
    for cid in ORDER:
        p = pub.get(cid)
        if not p:
            cards.append(f'<div class="card">{head(cid)}</div><div class="small">ход не сдан</div></div>'); continue
        chg = ''
        if prev.get(cid) and prev[cid].get('positioning') != p.get('positioning'):
            chg = '<div class="chg">позиционирование изменилось</div>'
        plans = ''.join(f'<tr><td>{E(x["name"])}</td><td>{"бесплатно" if x["price"]==0 else "$"+str(x["price"])+" в месяц"}</td></tr>' for x in p.get('plans', []))
        extra = f'<div class="lbl">заявление</div><div class="ad">{E(p["announce"])}</div>' if p.get('announce') else ''
        cards.append(f'''<div class="card">{head(cid)}{chg}</div>
<div class="lbl">позиционирование</div><div class="pv">{E(p.get("positioning",""))}</div>
<div class="lbl">реклама</div><div class="ad">«{E(p.get("ad",""))}»</div>
<div class="lbl">первый экран</div><div class="fs"><b>{E(p.get("h1",""))}</b><i>{E(p.get("h2",""))}</i><u>{E(p.get("cta",""))}</u></div>
<div class="lbl">тарифы</div><table class="plans">{plans}</table>{extra}</div>''')
    body = f'<h1>дашборд рынка<span>после чекпоинта {cp}</span></h1><div class="sub">Открытые части ходов всех компаний. ICP, бюджеты и карточки видит только ментор</div><div class="grid">{"".join(cards)}</div>'
    return page(f'Дашборд рынка · чекпоинт {cp}', body, f'чекпоинт {cp}')

def users_svg(hist, start_users):
    last = hist[-1]
    rows = sorted(ORDER, key=lambda c: -last[c]['users'])
    step, mx = nice(max(max(last[c]['users'] for c in ORDER), max(start_users.values())) * 1.05)
    W, L, RH = 1280, 190, 74
    H = RH * len(rows) + 40
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Пользователи по компаниям">']
    for k in range(0, int(round(mx / step)) + 1):
        v = step * k; x = L + (W - L - 160) * v / mx
        out.append(f'<line x1="{x:.0f}" y1="0" x2="{x:.0f}" y2="{H-30}" stroke="#E6ECF5" stroke-width="1"/><text x="{x:.0f}" y="{H-6}" font-size="15" fill="#5B6675" text-anchor="middle">{v/1000:g}k</text>')
    for i, c in enumerate(rows):
        y = i * RH + 14; u = last[c]['users']; s0 = start_users[c]
        w = (W - L - 160) * u / mx; x0 = L + (W - L - 160) * s0 / mx
        d = (u - s0) / s0 * 100
        out.append(f'<g data-company="{c}"><text x="0" y="{y+30}" font-size="22" font-weight="600" fill="#04131B">{E(CO[c]["name"])}</text>')
        out.append(f'<rect x="{L}" y="{y+8}" width="{max(4,w):.0f}" height="34" rx="4" fill="#04131B"><title>{E(CO[c]["name"])}: {fmt(u)} пользователей, на старте {fmt(s0)}</title></rect>')
        out.append(f'<line x1="{x0:.0f}" y1="{y+2}" x2="{x0:.0f}" y2="{y+48}" stroke="#F5000D" stroke-width="3"/>')
        tx = max(L + max(4, w), x0 + 2) + 12   # after the bar and after the start tick when users fell below the start
        out.append(f'<text x="{tx:.0f}" y="{y+32}" font-size="20" font-weight="600" fill="#04131B">{fmt(u)}</text><text x="{tx+len(fmt(u))*12+16:.0f}" y="{y+32}" font-size="18" fill="#5B6675">{d:+.0f}% к старту</text></g>')
    out.append('</svg>')
    return ''.join(out)

def users_svg_mobile(hist, start_users):
    last = hist[-1]
    rows = sorted(ORDER, key=lambda c: -last[c]['users'])
    mx = max(max(last[c]['users'] for c in ORDER), max(start_users.values())) * 1.05
    W, RH = 330, 66
    out = [f'<svg viewBox="0 0 {W} {RH * len(rows)}" width="100%" role="img" aria-label="Пользователи по компаниям">']
    for i, c in enumerate(rows):
        y = i * RH; u = last[c]['users']; s0 = start_users[c]; d = (u - s0) / s0 * 100
        out.append(f'<g data-company="{c}"><text x="0" y="{y+18}" font-size="16" font-weight="600" fill="#04131B">{E(CO[c]["name"])}</text>')
        out.append(f'<text x="{W}" y="{y+18}" text-anchor="end" font-size="15" fill="#04131B"><tspan font-weight="600">{fmt(u)}</tspan><tspan font-size="14" fill="#5B6675"> {d:+.0f}% к старту</tspan></text>')
        out.append(f'<rect x="0" y="{y+28}" width="{max(4, W * u / mx):.0f}" height="20" rx="4" fill="#04131B"><title>{E(CO[c]["name"])}: {fmt(u)} пользователей, на старте {fmt(s0)}</title></rect>')
        out.append(f'<line x1="{W * s0 / mx:.0f}" y1="{y+24}" x2="{W * s0 / mx:.0f}" y2="{y+52}" stroke="#F5000D" stroke-width="3"/></g>')
    out.append('</svg>')
    return ''.join(out)

def start_users():
    return {c['id']: sum(c['paid'].values()) + c['free'] for c in COMPANIES}

def view_sim1(state, res):
    su = start_users()
    pred = state.get('predictions') or {}
    ptab = ''
    if pred:
        last = res['hist'][-1]; errs = {}
        for team, guess in pred.items():
            e = [abs(guess[c] - last[c]['users']) / last[c]['users'] for c in guess if c in last]
            if e: errs[team] = sum(e) / len(e) * 100
        best = min(errs, key=errs.get) if errs else None
        rows = ''.join(f'<tr><td>{E(CO[t]["name"])}</td><td class="n">{errs[t]:.0f}%</td><td>{"+5 баллов" if t==best else ""}</td></tr>' for t in sorted(errs, key=errs.get))
        ptab = f'<div class="wide"><div class="lbl" style="margin-top:0">прогнозы: средняя ошибка</div><table class="t"><tr><th>команда</th><th class="n">ошибка</th><th></th></tr>{rows}</table></div>'
    body = f'''<h1>симуляция 1<span>пользователи после двух кварталов</span></h1>
<div class="sub">Пользователи: бесплатные и платящие вместе. Красная черта: сколько было на старте. Выручку покажем только в финале</div>
<div class="wide"><div class="desk">{users_svg(res["hist"], su)}</div><div class="mob">{users_svg_mobile(res["hist"], su)}</div></div>{ptab}'''
    return page('Симуляция 1', body, 'после чекпоинта 2')

def mrr_svg(res):
    pts = {c: [res['start_mrr'][c]] + [h[c]['mrr'] for h in res['hist']] for c in ORDER}
    step, mx = nice(max(max(v) for v in pts.values()) * 1.05)
    W, H, L, B, Rm = 1280, 460, 80, 50, 170
    X = lambda i: L + (W - L - Rm) * i / 3
    Y = lambda v: (H - B) - (H - B - 20) * v / mx
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Выручка в месяц по кварталам">']
    for k in range(0, int(round(mx / step)) + 1):
        v = step * k
        out.append(f'<line x1="{L}" y1="{Y(v):.0f}" x2="{W-Rm}" y2="{Y(v):.0f}" stroke="#E6ECF5"/><text x="{L-12}" y="{Y(v)+5:.0f}" font-size="15" fill="#5B6675" text-anchor="end">{money(v)}</text>')
    for i, q in enumerate(['старт', 'квартал 1', 'квартал 2', 'квартал 3']):
        out.append(f'<text x="{X(i):.0f}" y="{H-14}" font-size="16" fill="#5B6675" text-anchor="middle">{q}</text>')
    ends = []
    for c in ORDER:
        p = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(pts[c]))
        out.append(f'<g data-company="{c}">')
        out.append(f'<polyline points="{p}" fill="none" stroke="{SER[c]}" stroke-width="2.5" stroke-linejoin="round"/>')
        for i, v in enumerate(pts[c]):
            out.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="5" fill="{SER[c]}" stroke="#fff" stroke-width="2"><title>{E(CO[c]["name"])}, {["старт","квартал 1","квартал 2","квартал 3"][i]}: {money(v)} в месяц</title></circle>')
        out.append('</g>')
        ends.append([Y(pts[c][-1]), c, pts[c][-1]])
    ends.sort()
    last_y = -99
    for y, c, v in ends:
        y = max(y, last_y + 22); last_y = y
        out.append(f'<text data-company="{c}" x="{W-Rm+14}" y="{y+5:.0f}" font-size="16" font-weight="600" fill="#04131B">{E(CO[c]["name"])} {money(v)}</text>')
    out.append('</svg>')
    leg = ''.join(f'<span data-company="{c}"><i style="background:{SER[c]}"></i>{E(CO[c]["name"])}</span>' for c in ORDER)
    return f'<div class="legend">{leg}</div><div class="desk">' + ''.join(out) + f'</div><div class="mob">{mrr_svg_mobile(pts, step, mx)}</div>'

def mrr_svg_mobile(pts, step, mx):
    W, H, L, B, R = 330, 280, 46, 34, 36
    X = lambda i: L + (W - L - R) * i / 3
    Y = lambda v: (H - B) - (H - B - 12) * v / mx
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Выручка в месяц по кварталам">']
    for k in range(0, int(round(mx / step)) + 1):
        v = step * k
        out.append(f'<line x1="{L}" y1="{Y(v):.0f}" x2="{W-R+30}" y2="{Y(v):.0f}" stroke="#E6ECF5"/><text x="{L-8}" y="{Y(v)+5:.0f}" font-size="13" fill="#5B6675" text-anchor="end">{money(v)}</text>')
    for i, q in enumerate(['старт', 'квартал 1', 'квартал 2', 'квартал 3']):
        out.append(f'<text x="{X(i):.0f}" y="{H-8}" font-size="13" fill="#5B6675" text-anchor="middle">{q}</text>')
    for c in ORDER:
        p = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, v in enumerate(pts[c]))
        out.append(f'<g data-company="{c}"><polyline points="{p}" fill="none" stroke="{SER[c]}" stroke-width="2.5" stroke-linejoin="round"/>')
        out.append(''.join(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4" fill="{SER[c]}" stroke="#fff" stroke-width="2"/>' for i, v in enumerate(pts[c])) + '</g>')
    out.append('</svg>')
    return ''.join(out)

def seg_rank(rev, cid, seg):
    """1-based place of a company by revenue in one segment."""
    return 1 + sum(1 for c in ORDER if c != cid and rev[c][seg] > rev[cid][seg])

def goal_line(cid, start, last, tot0, tot, icps):
    """The number the role is judged on: where the team started, where it finished, what the role needed."""
    seg0 = {c: {s: CO[c]['paid'][s] * CO[c]['price'] for s in SEGN} for c in ORDER}
    seg1 = {c: last[c]['seg_rev'] for c in ORDER}
    if cid == 'lovable':
        return 'доля выручки рынка', f'{start[cid]/tot0*100:.0f}%', f'{last[cid]["mrr"]/tot*100:.0f}%', 'нужно не ниже 40%'
    if cid == 'bolt':
        return 'выручка в месяц', money(start[cid]), money(last[cid]['mrr']), f'нужно {money(2*start[cid])}'
    if cid in ('v0', 'base44'):
        s = 'des' if cid == 'v0' else 'smb'
        return f'место по выручке в сегменте «{SEGN[s]}»', f'№{seg_rank(seg0, cid, s)}', f'№{seg_rank(seg1, cid, s)}', 'нужно №1'
    s = icps.get(cid, 'fnd')
    sh0 = seg0[cid][s] / sum(seg0[c][s] for c in ORDER) * 100
    sh1 = seg1[cid][s] / max(1, sum(seg1[c][s] for c in ORDER)) * 100
    return f'доля выручки в сегменте «{SEGN[s]}»', f'{sh0:.0f}%', f'{sh1:.0f}%', 'нужно 20%'

def view_final(state, res, fs):
    last = res['hist'][-1]; tot = sum(last[c]['mrr'] for c in ORDER)
    start = res['start_mrr']; tot0 = sum(start[c] for c in ORDER); su = start_users()
    bonus = state.get('bonus', {})
    total = {c: fs['final'][c] + bonus.get(c, 0) for c in ORDER}
    rank = sorted(ORDER, key=lambda c: -total[c])
    rows = []
    for i, c in enumerate(rank):
        own = res['owners'][c]
        parts = [f'цель {fs["goals"][c]:.0f}%', f'эффективность {fs["eff_score"][c]:.0f}']
        parts += [f'бонус +{bonus[c]}'] if bonus.get(c) else []
        parts += [f'куплена {E(CO[own]["name"])}'] if own != c else []
        hh = head(c).replace('<div class="head" ', '<div class="head" style="margin:0" ', 1)
        what, a, z, need = goal_line(c, start, last, tot0, tot, state.get('icps', {}))
        sf = (f'<div><span>выручка в месяц</span> {money(start[c])} → {money(last[c]["mrr"])}</div>'
              f'<div><span>доля рынка</span> {start[c]/tot0*100:.0f}% → {last[c]["mrr"]/tot*100:.0f}%</div>'
              f'<div><span>пользователи</span> {fmt(su[c])} → {fmt(last[c]["users"])}</div>'
              f'<div><span>потрачено</span> {money(last[c]["spent_total"])} из {money(CO[c]["budget"])}</div>')
        rows.append(f'<div class="tm{" win" if i == 0 else ""}"><div class="rk">{i+1}</div>'
                    f'<div class="co">{hh}</div><div class="war">{E(CO[c]["war"].lower())}</div></div>'
                    f'<div class="gl"><div class="lbl">цель роли</div><div class="gt">{E(CO[c]["goal"])}</div>'
                    f'<div class="gm">{E(what)}: <b>{a} → {z}</b><i>{need} · выполнено на {fs["goals"][c]:.0f}%</i></div></div>'
                    f'<div class="sf"><div class="lbl">старт → финиш</div>{sf}</div>'
                    f'<div class="sc">{total[c]:.0f}</div>'
                    f'<div class="sb"><div class="bar"><i style="width:{min(100,total[c]):.0f}%"></i></div>'
                    f'<div class="small">{"".join(f"<div>{x}</div>" for x in parts)}</div></div></div>')
    ranking = f'<div class="wide"><div class="lbl" style="margin-top:0">кто лучше сыграл свою роль: 70% цель роли, 30% эффективность денег</div><div class="teams">{"".join(rows)}</div></div>'
    det = []
    for c in ORDER:
        h = last[c]
        spent = h['spent_total']; cac = [x[c]['cac'] for x in res['hist'] if x[c]['cac']]
        det.append(f'<tr data-company="{c}"><td>{E(CO[c]["name"])}</td><td class="n" data-label="пользователи">{fmt(h["users"])}</td><td class="n" data-label="платящие">{fmt(h["paid"])}</td><td class="n" data-label="выручка в месяц">{money(h["mrr"])}</td><td class="n" data-label="доля">{h["mrr"]/tot*100:.0f}%</td><td class="n" data-label="потрачено">{money(spent)}</td><td class="n" data-label="средний CAC">{"$"+fmt(sum(cac)/len(cac)) if cac else "-"}</td><td class="small">{E(CO[c]["goal"])}</td></tr>')
    table = f'<div class="wide"><div class="lbl" style="margin-top:0">цифры после третьего квартала</div><table class="t nums"><tr><th>компания</th><th class="n">пользователи</th><th class="n">платящие</th><th class="n">выручка в месяц</th><th class="n">доля</th><th class="n">потрачено</th><th class="n">средний CAC</th><th>цель роли</th></tr>{"".join(det)}</table></div>'
    quotes = state.get('quotes', {})
    qc = []
    for c in ORDER:
        logs = ''.join('<div>' + E(_re.sub(r'(?<=[0-9]),(?=[0-9])', ' ', l)) + '</div>' for l in res['logs'].get(c, []))
        qs = ''.join(f'<div class="q">«{E(q)}»</div>' for q in quotes.get(c, []))
        qc.append(f'<div class="card">{head(c)}</div>{qs}<div class="lbl">события</div><div class="log">{logs or "без особых событий"}</div></div>')
    body = f'''<h1>итоги рынка<span>победила команда {E(CO[rank[0]]["name"])}</span></h1><div class="sub">Счёт не про размер компании. Каждая команда играла свою роль со своего старта: лидер защищал долю, претендент рос, нишевые брали свой сегмент, новичок захватывал ICP</div>
{ranking}<div class="wide"><div class="lbl" style="margin-top:0">выручка в месяц по кварталам</div>{mrr_svg(res)}</div>{table}<div class="grid">{"".join(qc)}</div>'''
    return page('Итоги рынка', body, 'финал')

def view_wait():
    cards = ''.join(f'<div class="card">{head(c)}</div><div class="lbl">бюджет на игру</div><div class="pv">{money(CO[c]["budget"])}</div><div class="lbl">выручка в месяц на старте</div><div class="pv">{money(sum(CO[c]["paid"].values())*CO[c]["price"])}</div><div class="lbl">цель роли</div><div class="ad">{E(CO[c]["goal"])}</div></div>' for c in ORDER)
    body = f'<h1>дашборд рынка<span>до старта игры</span></h1><div class="sub">После чекпоинта 1 здесь появятся открытые части ходов всех компаний</div><div class="grid">{cards}</div>'
    return page('Рыночная война · дашборд', body, 'старт')

if __name__ == '__main__':
    view, state_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
    state = json.load(open(state_path, encoding='utf-8'))
    moves = {'quarters': state.get('quarters', [])}
    if view == 'wait':
        html_ = view_wait()
    elif view in ('public1', 'public2', 'public3'):
        html_ = view_public(state, int(view[-1]))
    elif view == 'sim1':
        res = sim.run(moves, seed=state.get('seed', 7), upto=2); html_ = view_sim1(state, res)
    elif view == 'final':
        res = sim.run(moves, seed=state.get('seed', 7)); fs = sim.final_scores(res, state.get('icps', {})); html_ = view_final(state, res, fs)
    else:
        sys.exit(f'unknown view {view}: wait | public1 | public2 | public3 | sim1 | final')
    open(out, 'w', encoding='utf-8').write(html_)
    print('ok', out, len(html_))
