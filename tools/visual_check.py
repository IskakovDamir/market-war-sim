"""Render every dashboard view with Playwright at desktop and phone size, check the layout, save screenshots.

python3 tools/visual_check.py [--out reference/proof]

Views: wait (pre-game), public1, public2, public3, sim1, final. Each is rendered through
scripts/live.py from a demo game (samples/moves_cp*.json + tools/fixtures/demo_public.json)
in a temp live folder, then opened at 1440x900 and 390x844.

A page fails on:
  - text overflowing its container (scrollWidth > clientWidth) or the page scrolling sideways
  - two text boxes overlapping, or a chart mark (bar, start tick, dot) covering text
  - a company list (cards, table rows, chart rows, legend) with fewer or more than the 5 companies
  - text under 14px on desktop (under 12px on the phone)
  - the name of the removed sixth company anywhere in the page
Needs the dev venv: .venv/bin/python tools/visual_check.py
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
sys.path.insert(0, SCRIPTS)
from spec import COMPANIES  # noqa: E402

VIEWS = ['wait', 'public1', 'public2', 'public3', 'sim1', 'final']
VIEWPORTS = {'desktop': dict(width=1440, height=900), 'mobile': dict(width=390, height=844)}
MIN_FONT = {'desktop': 14, 'mobile': 12}
CIDS = [c['id'] for c in COMPANIES]
BANNED = 'dy' + 'ad'

CHECK_JS = r"""
([minFont, cids, banned]) => {
  const problems = [];
  const vw = document.documentElement.clientWidth;
  const displayed = el => {
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') return false;
    }
    return true;
  };
  const shown = el => {
    const r = el.getBoundingClientRect();
    return displayed(el) && r.width > 0 && r.height > 0;
  };
  const label = el => `<${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.split(' ').join('.') : ''}>`;
  const text = el => (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 50);

  // 1. sideways scroll and overflowing containers
  if (document.documentElement.scrollWidth > vw + 1)
    problems.push(`page scrolls sideways: ${document.documentElement.scrollWidth}px > ${vw}px`);
  for (const el of document.body.querySelectorAll('*')) {
    if (el instanceof SVGElement || !shown(el)) continue;
    const d = getComputedStyle(el).display;
    if (d === 'inline' || d === 'contents' || !text(el)) continue;
    if (el.scrollWidth > el.clientWidth + 1)
      problems.push(`overflow ${label(el)} ${el.scrollWidth}px > ${el.clientWidth}px: "${text(el)}"`);
  }

  // 2. text boxes: overlap and font size
  const boxes = [];
  const seenSvg = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode;
    const p = n.parentElement;
    if (!n.textContent.trim() || !p || p.closest('title, style, script') || !shown(p)) continue;
    let size = parseFloat(getComputedStyle(p).fontSize);
    if (p instanceof SVGElement) {
      const svg = p.ownerSVGElement;
      const vb = svg.viewBox.baseVal;
      if (vb && vb.width) size *= svg.getBoundingClientRect().width / vb.width;
      const t = p.closest('text');
      if (seenSvg.has(t)) continue;
      seenSvg.add(t);
      boxes.push({r: t.getBoundingClientRect(), el: t});
    } else {
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) if (r.width > 0.5 && r.height > 0.5) boxes.push({r, el: p});
    }
    if (size < minFont - 0.05) problems.push(`font ${size.toFixed(1)}px < ${minFont}px in ${label(p)}: "${text(p)}"`);
  }
  // glyphs sit inside the line box: shrink each box 20% top and bottom before comparing
  const core = r => ({l: r.left, r: r.right, t: r.top + r.height * 0.2, b: r.bottom - r.height * 0.2});
  for (let i = 0; i < boxes.length; i++) {
    const a = core(boxes[i].r);
    for (let j = i + 1; j < boxes.length; j++) {
      if (boxes[i].el === boxes[j].el) continue;
      const b = core(boxes[j].r);
      const w = Math.min(a.r, b.r) - Math.max(a.l, b.l), h = Math.min(a.b, b.b) - Math.max(a.t, b.t);
      if (w > 1 && h > 1)
        problems.push(`overlap "${text(boxes[i].el)}" and "${text(boxes[j].el)}"`);
    }
  }

  // chart marks (bars, red start ticks, dots) must not cover text; light grid lines may
  for (const m of document.querySelectorAll('svg rect, svg circle, svg line')) {
    if (!displayed(m) || (m.getAttribute('stroke') || '').toUpperCase() === '#E6ECF5') continue;   // a vertical tick has zero width
    const g = m.getBoundingClientRect(), svg = m.ownerSVGElement, vb = svg.viewBox.baseVal;
    const half = parseFloat(m.getAttribute('stroke-width') || 0) / 2 * (vb && vb.width ? svg.getBoundingClientRect().width / vb.width : 1);
    const r = {left: g.left - half, right: g.right + half, top: g.top - half, bottom: g.bottom + half};
    for (const t of boxes) {
      const a = core(t.r);
      const w = Math.min(a.r, r.right) - Math.max(a.l, r.left), h = Math.min(a.b, r.bottom) - Math.max(a.t, r.top);
      if (w > 1 && h > 1) problems.push(`chart mark <${m.tagName}> covers "${text(t.el)}"`);
    }
  }

  // 3. every company list shows exactly the 5 companies
  const groups = new Map();
  for (const el of document.querySelectorAll('[data-company]')) {
    if (!shown(el)) continue;
    const box = el.closest('.grid, table, svg, .legend') || document.body;
    const key = box;
    if (!groups.has(key)) groups.set(key, {name: label(box) + ' ' + el.tagName.toLowerCase(), ids: []});
    groups.get(key).ids.push(el.getAttribute('data-company'));
  }
  if (!groups.size) problems.push('no company list found');
  for (const g of groups.values()) {
    const byTag = {};
    g.ids.forEach(id => (byTag[id] = (byTag[id] || 0) + 1));
    const ids = Object.keys(byTag).sort().join(',');
    const per = new Set(Object.values(byTag));
    if (ids !== [...cids].sort().join(',') || per.size !== 1)
      problems.push(`company list ${g.name} shows ${ids} (${g.ids.length} blocks)`);
  }

  // 4. the removed company
  const all = (document.body.innerText + document.documentElement.outerHTML).toLowerCase();
  if (all.includes(banned)) problems.push('mentions the removed company');
  return problems;
}
"""


def demo_state():
    fx = json.load(open(os.path.join(ROOT, 'tools', 'fixtures', 'demo_public.json'), encoding='utf-8'))
    quarters = [json.load(open(os.path.join(ROOT, 'samples', f'moves_cp{cp}.json'), encoding='utf-8'))
                for cp in (1, 2, 3)]
    public = {}
    for cp in ('1', '2', '3'):
        public[cp] = {}
        for cid in CIDS:
            p = dict(fx['public'][cid][cp])
            p['plans'] = [dict(name=x['name'], price=x['price']) for x in quarters[int(cp) - 1][cid]['plans']]
            public[cp][cid] = p
    return dict(public=public, raw={}, quarters=quarters, seed=7, icps={'rork': 'fnd'},
                predictions=fx['predictions'], bonus=fx['bonus'], quotes=fx['quotes'])


def render_all(tmp):
    live = os.path.join(tmp, 'live')
    os.makedirs(live)
    json.dump(demo_state(), open(os.path.join(live, 'state.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    env = dict(os.environ, MARKET_WAR_LIVE=live)
    pages = {}
    for view in VIEWS:
        out = os.path.join(tmp, f'{view}.html')
        subprocess.run([sys.executable, os.path.join(SCRIPTS, 'live.py'), 'render', view, out],
                       env=env, check=True, capture_output=True, text=True)
        pages[view] = out
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'reference', 'proof'))
    args = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit('playwright is missing: run with .venv/bin/python (python3 tools/check_all.py sets it up)')
    os.makedirs(args.out, exist_ok=True)
    failed = 0
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        pages = render_all(tmp)
        browser = pw.chromium.launch()
        for vp_name, vp in VIEWPORTS.items():
            mobile = vp_name == 'mobile'
            ctx = browser.new_context(viewport=vp, device_scale_factor=2 if mobile else 1,
                                      is_mobile=mobile, has_touch=mobile)
            page = ctx.new_page()
            for view in VIEWS:
                page.goto('file://' + pages[view], wait_until='networkidle')
                page.evaluate('document.fonts.ready.then(() => true)')
                problems = page.evaluate(CHECK_JS, [MIN_FONT[vp_name], CIDS, BANNED])
                shot = os.path.join(args.out, f'{view}-{vp_name}.png')
                page.screenshot(path=shot, full_page=True)
                status = 'PASS' if not problems else 'FAIL'
                failed += bool(problems)
                print(f'{status}  {view:8s} {vp_name:7s} {os.path.relpath(shot, ROOT)}')
                for p in problems[:15]:
                    print(f'      - {p}')
                if len(problems) > 15:
                    print(f'      ... and {len(problems) - 15} more')
            ctx.close()
        browser.close()
    print(f'{len(VIEWS) * len(VIEWPORTS) - failed}/{len(VIEWS) * len(VIEWPORTS)} pages pass')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
