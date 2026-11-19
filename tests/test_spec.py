import os
import re

from conftest import ROOT, SCRIPTS
import extract
import sim
from spec import ACTIONS, CHANNELS, COMPANIES, FREE_COST, PAID_COST, SEG_IDS, SEGMENTS

CIDS = [c['id'] for c in COMPANIES]
# Channels that do not work in some segments, by design (None in spec.py).
UNREACHABLE = {('sales', 'stud'), ('sales', 'dev')}
SKIP_DIRS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'live', 'out'}


def test_five_unique_company_ids():
    assert len(CIDS) == 5
    assert len(set(CIDS)) == 5
    assert CIDS == ['lovable', 'bolt', 'v0', 'base44', 'rork']


def test_shape_five_segments_twelve_channels_fourteen_cards():
    assert len(SEGMENTS) == 5 and len(set(SEG_IDS)) == 5
    assert len(CHANNELS) == 12 and len({c['id'] for c in CHANNELS}) == 12
    assert len(ACTIONS) == 14 and len({a['id'] for a in ACTIONS}) == 14


def test_every_channel_has_lo_below_hi_for_all_five_segments():
    for ch in CHANNELS:
        assert set(ch['cpu']) == set(SEG_IDS), ch['id']
        for s in SEG_IDS:
            rng = ch['cpu'][s]
            if (ch['id'], s) in UNREACHABLE:
                assert rng is None
                continue
            lo, hi = rng
            assert 0 < lo < hi, (ch['id'], s, rng)


def test_only_sales_is_unreachable_and_only_for_stud_and_dev():
    none = {(c['id'], s) for c in CHANNELS for s in SEG_IDS if c['cpu'][s] is None}
    assert none == UNREACHABLE


def test_cost_dicts_keyed_exactly_by_company_ids():
    assert set(PAID_COST) == set(CIDS)
    assert set(FREE_COST) == set(CIDS)
    for c in COMPANIES:
        assert set(c['paid']) == set(SEG_IDS), c['id']
    assert set(sim.ASSET_SCORE) <= set(CIDS)


def test_channel_delays_sum_to_one_and_targets_in_range():
    for ch in CHANNELS:
        assert abs(sum(ch['delay']) - 1.0) < 1e-9, ch['id']
        assert 0 <= ch['target'] <= 1
        assert ch['min_k'] > 0 and 0 < ch['var'] < 1


def test_extract_channel_table_matches_spec():
    assert extract.CH_IDS == [c['id'] for c in CHANNELS]
    assert extract.CH_NAMES == [c['name'] for c in CHANNELS]


def test_card_prices_in_sim_match_card_text():
    text = {a['id']: a['cost'] for a in ACTIONS}
    for aid, cost in sim.ACTION_COST.items():
        assert text[aid].startswith(f'${cost // 1000}k'), (aid, cost, text[aid])
    assert set(sim.ACTION_COST) <= set(text)


def test_lovable_starting_share_matches_goal_text():
    mrr = {c['id']: sum(c['paid'].values()) * c['price'] for c in COMPANIES}
    share = round(mrr['lovable'] / sum(mrr.values()) * 100)
    goal = next(c['goal'] for c in COMPANIES if c['id'] == 'lovable')
    assert f'{share}%' in goal


def test_no_trace_of_removed_company_anywhere_in_repo():
    needle = ('dy' + 'ad').encode()
    hits = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in dirs + files:
            if needle in name.lower().encode():
                hits.append(os.path.join(base, name))
        for name in files:
            path = os.path.join(base, name)
            with open(path, 'rb') as f:
                if needle in f.read().lower():
                    hits.append(path)
    assert hits == []


def test_runtime_scripts_use_only_stdlib():
    allowed = {'os', 'sys', 'json', 'math', 'random', 'copy', 're', 'html',
               'spec', 'sim', 'extract', 'dashboard'}
    for name in os.listdir(SCRIPTS):
        if not name.endswith('.py'):
            continue
        src = open(os.path.join(SCRIPTS, name), encoding='utf-8').read()
        for line in src.splitlines():
            m = re.match(r'\s*(?:import|from)\s+([\w.]+)', line)
            if m:
                mods = [m.group(1)] if line.lstrip().startswith('from') else \
                    [x.strip().split(' ')[0] for x in line.split('import', 1)[1].split(';')[0].split(',')]
                for mod in mods:
                    assert mod.split('.')[0] in allowed, (name, line)
