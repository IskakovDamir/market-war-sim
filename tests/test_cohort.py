import pytest

from conftest import move, quarter, run
from spec import SEG_IDS

PRO = lambda p: [{'name': 'Free', 'price': 0}, {'name': 'Pro', 'price': p}]


def test_price_cut_reaches_existing_customers():
    res = run(quarter(lovable=dict(spend={'social': 100000})),
              quarter(lovable=dict(plans=PRO(15), spend={'social': 100000})))
    q1, q2 = res['hist'][0]['lovable'], res['hist'][1]['lovable']
    assert all(q1['seg_arpu'][s] == pytest.approx(25) for s in SEG_IDS)
    assert all(q2['seg_arpu'][s] == pytest.approx(15) for s in SEG_IDS)
    assert q2['mrr'] == pytest.approx(15 * q2['paid'])


def test_price_raise_keeps_existing_customers_on_the_old_price():
    res = run(quarter(), quarter(lovable=dict(plans=PRO(40))))
    q2 = res['hist'][1]['lovable']
    assert q2['new_paid'] == 0
    assert all(q2['seg_arpu'][s] == pytest.approx(25) for s in SEG_IDS)


def test_price_raise_charges_new_customers_the_new_price():
    res = run(quarter(), quarter(lovable=dict(plans=PRO(40), spend={'social': 150000})))
    q2 = res['hist'][1]['lovable']
    for s in SEG_IDS:
        if q2['arrivals'][s] > 0:
            assert 25 < q2['seg_arpu'][s] < 40, s


def test_cohort_arpu_is_the_paid_weighted_blend():
    res = run(quarter(), quarter(lovable=dict(plans=PRO(40), spend={'social': 150000})))
    q1, q2 = res['hist'][0]['lovable'], res['hist'][1]['lovable']
    s = 'fnd'
    # old cohort at 25 shrinks with churn, new cohort at 40 joins before churn: blend weights are pre-churn counts
    old = q1['seg_paid'][s]
    new = q2['seg_paid'][s] / 0.75 - old
    assert q2['seg_arpu'][s] == pytest.approx((old * 25 + new * 40) / (old + new))


def test_decoy_and_upsell_raise_new_customer_price():
    res = run(quarter(), quarter(lovable=dict(spend={'social': 150000},
                                              actions=[{'id': 'decoy'}, {'id': 'upsell'}])))
    q1, q2 = res['hist'][0]['lovable'], res['hist'][1]['lovable']
    s = 'fnd'
    old = q1['seg_paid'][s]
    new = q2['seg_paid'][s] / 0.75 - old
    assert q2['seg_arpu'][s] == pytest.approx((old * 25 + new * 25 * 1.15 * 1.10) / (old + new))


def test_premium_survives_unchanged_price():
    res = run(quarter(lovable=dict(spend={'social': 200000}, actions=[{'id': 'decoy'}])), quarter())
    q1, q2 = res['hist'][0]['lovable'], res['hist'][1]['lovable']
    assert q1['seg_arpu']['fnd'] > 25
    for s in SEG_IDS:
        assert q2['seg_arpu'][s] == pytest.approx(q1['seg_arpu'][s]), s


def test_price_cut_after_a_premium_moves_existing_customers_to_the_new_price():
    res = run(quarter(lovable=dict(spend={'social': 200000}, actions=[{'id': 'decoy'}])),
              quarter(lovable=dict(plans=PRO(20))))
    q2 = res['hist'][1]['lovable']
    assert all(q2['seg_arpu'][s] == pytest.approx(20) for s in SEG_IDS)
