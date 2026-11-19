"""The live game of 19 November 2026, replayed from its state after checkpoints 1 and 2.

EXPECTED_* are the numbers from market-war-live/EXPECTED.md: what the live code computed during the game.
Every one must match exactly, so the final simulation after checkpoint 3 continues the same game.
The fixture holds only what the simulation reads (seed, ICPs, forecasts, moves), no team texts.
The game ran before fix B12, so its state carries arpu_reset=True: existing customers' ARPU drops to the plan
price whenever it is above it. Without the switch only Q2 MRR of Lovable and Bolt (decoy and upsell in Q1) moves.
"""
import json
import os

import pytest

from conftest import CIDS, ROOT

import dashboard  # noqa: E402
import sim  # noqa: E402

FIXTURE = os.path.join(ROOT, 'tests', 'fixtures', 'live_2026-11-19.json')

# company: (users, paid, MRR $, spent total $), rounded the way report.py and the dashboards round
EXPECTED_QUARTERS = {
    1: dict(lovable=(64754, 12107, 363906, 385000),
            bolt=(35027, 4921, 154518, 230000),
            v0=(22258, 3098, 68482, 170000),
            base44=(14164, 2795, 104286, 150000),
            rork=(4540, 540, 13500, 0)),
    2: dict(lovable=(77660, 13782, 439677, 755148),
            bolt=(37282, 5134, 176036, 485000),
            v0=(24570, 3556, 91601, 380000),
            base44=(19086, 4163, 217669, 320000),
            rork=(5606, 613, 17949, 95000)),
}
EXPECTED_LOGS = {
    1: {c: [] for c in CIDS},
    2: dict(lovable=['Q2: рефералка привела 4,015 пользователей'], bolt=[], v0=[],
            base44=['Q2: атака на Lovable сработала: +153 платящих'], rork=[]),
}
EXPECTED_ICPS = dict(lovable='fnd', bolt='fnd', v0='des', base44='smb', rork='fnd')
EXPECTED_PREDICTIONS = {
    'lovable': dict(lovable=70000, bolt=44000, v0=26000, base44=18000, rork=8000),
    'bolt': dict(lovable=60000, bolt=33000, v0=23000, base44=15500, rork=7000),
    'v0': dict(lovable=62300, bolt=35200, v0=22800, base44=15100, rork=5600),
    'base44': dict(lovable=62000, bolt=33000, v0=22000, base44=20000, rork=6200),
    'rork': dict(lovable=56000, bolt=35000, v0=22000, base44=15000, rork=6500),
}
FIELDS = ('users', 'paid', 'mrr', 'spent_total')


@pytest.fixture(scope='module')
def game():
    with open(FIXTURE, encoding='utf-8') as f:
        return json.load(f)


def replay(game, upto, arpu_reset=None):
    rule = game['arpu_reset'] if arpu_reset is None else arpu_reset
    return sim.run({'quarters': game['quarters']}, seed=game['seed'], upto=upto, arpu_reset=rule)


@pytest.fixture(scope='module')
def results(game):
    """Quarter q replayed on its own (upto=q), as the room saw it after that quarter."""
    return {q: replay(game, q) for q in EXPECTED_QUARTERS}


def test_fixture_is_the_live_game(game):
    assert game['seed'] == 7
    assert game['arpu_reset'] is True
    assert len(game['quarters']) == 2
    assert all(sorted(q) == sorted(CIDS) for q in game['quarters'])


@pytest.mark.parametrize('q', sorted(EXPECTED_QUARTERS))
@pytest.mark.parametrize('cid', CIDS)
def test_quarter_numbers_match_expected(results, q, cid):
    h = results[q]['hist'][q - 1][cid]
    got = dict(zip(FIELDS, (round(h[k]) for k in FIELDS)))
    assert got == dict(zip(FIELDS, EXPECTED_QUARTERS[q][cid]))


@pytest.mark.parametrize('q', sorted(EXPECTED_QUARTERS))
def test_event_logs_match_expected(results, q):
    assert results[q]['logs'] == EXPECTED_LOGS[q]


def test_quarter_1_is_the_same_inside_the_two_quarter_run(results):
    """Adding quarter 2 must not rewrite quarter 1."""
    assert results[2]['hist'][0] == results[1]['hist'][0]


def test_default_rule_moves_only_q2_mrr_of_lovable_and_bolt(game):
    """Pins the cause of the only parity gap: fix B12 keeps the Q1 decoy/upsell premium on existing customers."""
    b12 = replay(game, 2, arpu_reset=False)
    diff = {(q, c, k): round(b12['hist'][q - 1][c][k])
            for q in EXPECTED_QUARTERS for c in CIDS for k in FIELDS
            if round(b12['hist'][q - 1][c][k]) != EXPECTED_QUARTERS[q][c][FIELDS.index(k)]}
    assert diff == {(2, 'lovable', 'mrr'): 455537, (2, 'bolt', 'mrr'): 177295}


def test_icps_and_predictions_match_expected(game):
    assert game['icps'] == EXPECTED_ICPS
    assert game['predictions'] == EXPECTED_PREDICTIONS


def test_no_company_was_bought_or_skipped(results):
    assert results[2]['owners'] == {c: c for c in CIDS}
    assert results[2]['warnings'] == []


def test_segment_users_add_up_to_users(results):
    for snap in results[2]['hist']:
        for cid, h in snap.items():
            assert sum(h['seg_users'].values()) == pytest.approx(h['users'])
            assert sum(h['seg_paid'].values()) == pytest.approx(h['paid'])


def test_sim1_views_render_the_live_numbers(game, results):
    res = results[2]
    state = dict(game, public={}, raw={})
    market = dashboard.view_sim1_market(state, res)
    total = sum(v[0] for v in EXPECTED_QUARTERS[2].values())
    assert dashboard.k_(total) in market
    assert 'точность прогнозов' in market and '+5 баллов' in market
    for cid in CIDS:
        team = dashboard.view_sim1_team(state, res, cid)
        assert dashboard.k_(EXPECTED_QUARTERS[2][cid][0]) in team
        for line in EXPECTED_LOGS[2][cid]:
            assert line in team
