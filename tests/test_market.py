import pytest

from conftest import CIDS, CO, move, quarter, run, start_paid
import sim
from spec import SEGMENTS, SEG_IDS

SIZE = {s['id']: s['size'] for s in SEGMENTS}


def test_pool_cap_limits_arrivals_per_segment():
    flood = dict(icp='stud', spend={'shorts': 400000, 'social': 400000})
    res = run(quarter(lovable=flood, bolt=dict(icp='stud', spend={'shorts': 300000})))
    h = res['hist'][0]
    for s in SEG_IDS:
        total = sum(h[c]['arrivals'][s] for c in CIDS)
        assert total <= sim.POOL_SHARE * SIZE[s] + 1e-6, s
    stud = sum(h[c]['arrivals']['stud'] for c in CIDS)
    assert stud == pytest.approx(0.35 * 120000)  # the cap binds


def test_pool_cap_scales_every_company_by_the_same_factor():
    def arrivals(k):
        q = quarter(lovable=dict(icp='stud', spend={'shorts': 400000 * k}),
                    bolt=dict(icp='stud', spend={'shorts': 300000 * k}))
        h = run(q)['hist'][0]
        return h['lovable']['arrivals']['stud'], h['bolt']['arrivals']['stud']
    capped, free = arrivals(1), arrivals(0.02)
    assert sum(capped) == pytest.approx(0.35 * 120000)
    assert sum(free) < 0.35 * 120000
    assert capped[0] / capped[1] == pytest.approx(free[0] / free[1])


def test_zero_spend_churn_is_25_percent_paid_and_20_percent_free():
    res = run(quarter(), quarter())
    for qi in range(2):
        h = res['hist'][qi]
        for c in CIDS:
            paid = start_paid(c) * 0.75 ** (qi + 1)
            free = CO[c]['free'] * 0.80 ** (qi + 1)
            assert h[c]['paid'] == pytest.approx(paid), c
            assert h[c]['users'] - h[c]['paid'] == pytest.approx(free), c
            assert h[c]['new_paid'] == 0 and h[c]['spend'] == 0


def test_community_cuts_paid_churn_by_20_percent_this_and_next_quarter():
    res = run(quarter(v0=dict(icp='dev', spend={'community': 30000})), quarter(), quarter())
    v = [h['v0'] for h in res['hist']]
    churn = 0.25 * (1 - 0.2)
    assert v[0]['paid'] == pytest.approx((start_paid('v0') + v[0]['new_paid']) * (1 - churn))
    assert v[1]['paid'] == pytest.approx((v[0]['paid'] + v[1]['new_paid']) * (1 - churn))
    assert v[2]['paid'] == pytest.approx((v[1]['paid'] + v[2]['new_paid']) * 0.75)


def test_onboarding_cuts_paid_churn_by_30_percent():
    res = run(quarter(base44=dict(actions=[{'id': 'onboarding'}])))
    h = res['hist'][0]['base44']
    assert h['paid'] == pytest.approx(start_paid('base44') * (1 - 0.25 * 0.7))
    assert h['spend'] == 30000


def _arrivals(**lov):
    return run(quarter(lovable=dict(spend={'social': 100000}, **lov)))['hist'][0]['lovable']


def test_consistency_half_raises_cost_per_user_by_10_percent():
    full, half = _arrivals(consistency=1), _arrivals(consistency=0.5)
    for s in SEG_IDS:
        assert half['arrivals'][s] == pytest.approx(full['arrivals'][s] / 1.10)
    assert half['score'] == full['score']


def test_consistency_zero_raises_cost_by_25_percent_and_takes_one_point():
    six = {s: 6 for s in SEG_IDS}
    five = {s: 5 for s in SEG_IDS}
    zero = _arrivals(consistency=0, scores=six)
    ref = _arrivals(consistency=1, scores=five)
    assert zero['score'] == {s: 5.0 for s in SEG_IDS}
    for s in SEG_IDS:
        assert zero['arrivals'][s] == pytest.approx(ref['arrivals'][s] / 1.25)


def test_bid_below_minimum_works_at_30_percent():
    below = run(quarter(lovable=dict(spend={'social': 9000})))
    at_min = run(quarter(lovable=dict(spend={'social': 10000})))
    for s in SEG_IDS:
        assert below['hist'][0]['lovable']['arrivals'][s] == pytest.approx(
            at_min['hist'][0]['lovable']['arrivals'][s] * 0.3 * 9000 / 10000)
    assert any('ставка ниже минимальной' in l for l in below['logs']['lovable'])


def test_auction_adds_15_percent_per_rival_on_the_same_icp():
    same = run(quarter(lovable=dict(spend={'social': 100000}),
                       bolt=dict(icp='fnd', spend={'social': 50000})))['hist'][0]['lovable']['arrivals']
    other = run(quarter(lovable=dict(spend={'social': 100000}),
                        bolt=dict(icp='des', spend={'social': 50000})))['hist'][0]['lovable']['arrivals']
    assert same['fnd'] == pytest.approx(other['fnd'] / 1.15)
    assert same['des'] == pytest.approx(other['des'] * 1.15)
    assert same['stud'] == pytest.approx(other['stud'])


def test_sales_needs_a_plan_of_at_least_50_dollars():
    cheap = run(quarter(base44=dict(icp='smb', spend={'sales': 50000})))
    rich = run(quarter(base44=dict(icp='smb', spend={'sales': 50000},
                                   plans=[{'name': 'Free', 'price': 0}, {'name': 'Biz', 'price': 80}])))
    assert sum(cheap['hist'][0]['base44']['arrivals'].values()) == 0
    assert cheap['hist'][0]['base44']['spend'] == 50000
    assert any('Продажи без тарифа от $50' in l for l in cheap['logs']['base44'])
    assert rich['hist'][0]['base44']['arrivals']['smb'] > 0
    assert rich['hist'][0]['base44']['new_paid'] > 0


def test_cost_per_user_falls_linearly_with_score():
    lo = _arrivals(scores={s: 1 for s in SEG_IDS})
    hi = _arrivals(scores={s: 10 for s in SEG_IDS})
    # social fnd range 25..60: score 1 pays 60, score 10 pays 25
    assert hi['arrivals']['fnd'] / lo['arrivals']['fnd'] == pytest.approx(60 / 25)
