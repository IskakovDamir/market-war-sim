"""Role goals and the final score on small hand-built results."""
import pytest

from conftest import CIDS, golden
import sim
from spec import SEG_IDS

START = dict(lovable=225000, bolt=100000, v0=60000, base44=75000, rork=20000)


def result(mrr, seg=None, spent=None, start=START, owners=None):
    """One quarter of history. seg: company -> {segment: revenue}; the rest of MRR goes to stud."""
    hist = {}
    for c in CIDS:
        sr = {s: 0.0 for s in SEG_IDS}
        sr.update((seg or {}).get(c, {}))
        sr['stud'] += mrr[c] - sum(sr.values())
        hist[c] = dict(mrr=mrr[c], seg_rev=sr, spent_total=(spent or {}).get(c, 100000))
    return dict(hist=[hist], start_mrr=dict(start), owners=owners or {c: c for c in CIDS})


def market(lovable_share, total=1_000_000):
    rest = total * (1 - lovable_share) / 4
    return dict(lovable=total * lovable_share, bolt=rest, v0=rest, base44=rest, rork=rest)


@pytest.mark.parametrize('share,goal', [(0.38, 88), (0.40, 100), (0.47, 100), (0.30, 40), (0.20, 0)])
def test_lovable_goal_minus_6_per_point_below_40(share, goal):
    fs = sim.final_scores(result(market(share)), {})
    assert fs['goals']['lovable'] == pytest.approx(goal)


@pytest.mark.parametrize('mult,goal', [(2.0, 100), (1.5, 50), (1.0, 0), (0.8, 0), (3.0, 100)])
def test_bolt_goal_is_doubling_mrr(mult, goal):
    m = market(0.4)
    m['bolt'] = START['bolt'] * mult
    assert sim.final_scores(result(m), {})['goals']['bolt'] == pytest.approx(goal)


@pytest.mark.parametrize('cid,seg', [('v0', 'des'), ('base44', 'smb')])
def test_niche_goal_is_number_one_in_its_segment(cid, seg):
    m = market(0.4)
    first = result(m, seg={cid: {seg: 50000}, 'lovable': {seg: 40000}})
    assert sim.final_scores(first, {})['goals'][cid] == 100
    second = result(m, seg={cid: {seg: 30000}, 'lovable': {seg: 40000}})
    assert sim.final_scores(second, {})['goals'][cid] == pytest.approx(75)


def test_rork_goal_is_20_percent_of_its_checkpoint_1_icp():
    m = market(0.4)
    seg = {'rork': {'smb': 20000}, 'base44': {'smb': 80000}, 'lovable': {'fnd': 100000}}
    assert sim.final_scores(result(m, seg=seg), {'rork': 'smb'})['goals']['rork'] == pytest.approx(100)
    seg['base44']['smb'] = 180000
    assert sim.final_scores(result(m, seg=seg), {'rork': 'smb'})['goals']['rork'] == pytest.approx(50)
    # without the checkpoint 1 ICP the goal falls back to fnd, where Rork has nothing
    assert sim.final_scores(result(m, seg=seg), {})['goals']['rork'] == 0


def test_final_is_70_percent_goal_plus_30_percent_efficiency():
    fs = sim.final_scores(sim.run(golden()), {'rork': 'fnd'})
    for c in CIDS:
        assert fs['final'][c] == pytest.approx(0.7 * fs['goals'][c] + 0.3 * fs['eff_score'][c])
    assert max(fs['eff_score'].values()) == pytest.approx(100)


def test_efficiency_is_revenue_gain_per_dollar():
    m = dict(START)
    m['bolt'] = 150000
    fs = sim.final_scores(result(m, spent=dict(bolt=50000)), {})
    assert fs['eff']['bolt'] == pytest.approx((150000 - 100000) * 3 / 50000)
    assert fs['eff_score']['bolt'] == 100
    assert fs['eff_score']['lovable'] == 0


def test_zero_spend_does_not_zero_others():
    m = dict(START)
    m['bolt'] = 150000
    m['rork'] = 25000
    fs = sim.final_scores(result(m, spent=dict(bolt=50000, rork=0)), {})
    assert fs['eff_score']['bolt'] == 100
    assert fs['eff_score']['rork'] == 0


def test_zero_spend_team_in_the_golden_game_leaves_other_scores_alone():
    g = golden()
    for q in g['quarters']:
        q['rork'] = dict(q['rork'], spend={}, actions=[])
    fs = sim.final_scores(sim.run(g), {'rork': 'fnd'})
    assert fs['eff_score']['rork'] == 0
    assert max(fs['eff_score'][c] for c in CIDS if c != 'rork') == pytest.approx(100)
