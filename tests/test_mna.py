import pytest

from conftest import CIDS, CO, quarter, run
import sim
import dashboard

B5 = pytest.mark.xfail(strict=True, reason='B5: seller side M&A action crashes the run')
BUY = lambda price=500000: [{'id': 'mna', 'target': 'rork', 'price': price}]
SELL = [{'id': 'mna', 'buyer': 'lovable'}]


def deal(price=500000, seller=True):
    return quarter(lovable=dict(actions=BUY(price)), rork=dict(actions=SELL if seller else []))


@B5
def test_seller_side_action_does_not_crash():
    res = run(deal())
    assert res['owners']['rork'] == 'lovable'
    assert 'Q1: купили Rork за $500,000' in res['logs']['lovable']


@B5
def test_mna_price_leaves_the_buyer_budget():
    res = run(deal(), quarter())
    assert res['hist'][0]['lovable']['spent_total'] == 500000
    assert res['hist'][1]['lovable']['budget_left'] == 500000


@B5
def test_mna_users_and_revenue_move_to_the_buyer_group_without_double_counting():
    res = run(deal(), quarter(), quarter())
    fs = sim.final_scores(res, {'rork': 'fnd'})
    last = res['hist'][-1]
    market = sum(last[c]['mrr'] for c in CIDS)
    group = last['lovable']['mrr'] + last['rork']['mrr']
    share = group / market * 100
    assert fs['goals']['lovable'] == pytest.approx(max(0, 100 - 6 * max(0, 40 - share)))
    assert fs['goals']['rork'] == fs['goals']['lovable']
    assert fs['final']['rork'] == fs['final']['lovable']
    # efficiency counts the group's revenue and spend once
    rev3 = sum((h['lovable']['mrr'] + h['rork']['mrr']) * 3 for h in res['hist'])
    base3 = (res['start_mrr']['lovable'] + res['start_mrr']['rork']) * 3 * 3
    spent = last['lovable']['spent_total'] + last['rork']['spent_total']
    assert fs['eff']['lovable'] == pytest.approx((rev3 - base3) / spent)
    html = dashboard.view_final({}, res, fs)
    assert 'куплена Lovable' in html


def test_mna_needs_both_sides():
    res = run(deal(seller=False))
    assert res['owners']['rork'] == 'rork'
    assert res['hist'][0]['lovable']['spent_total'] == 0
    assert any('не засчитана' in l for l in res['logs']['lovable'])


@B5
def test_mna_below_three_quarterly_revenues_is_rejected():
    minimum = 3 * 3 * sum(CO['rork']['paid'].values()) * CO['rork']['price']
    assert minimum == 180000
    low = run(deal(price=179000))
    assert low['owners']['rork'] == 'rork'
    assert low['hist'][0]['lovable']['spent_total'] == 0
    ok = run(deal(price=180000))
    assert ok['owners']['rork'] == 'lovable'


@pytest.mark.xfail(strict=True, reason='B8: after M&A the target budget is counted twice')
def test_group_budget_not_double_counted():
    res = run(deal(), quarter(lovable=dict(spend={'social': 650000}), rork=dict(spend={'creators': 150000})))
    h = res['hist'][-1]
    assert h['lovable']['spent_total'] + h['rork']['spent_total'] <= 1_150_000 + 1e-6


@pytest.mark.xfail(strict=True, reason='B9: the same M&A declared again is bought and paid again')
def test_repeat_declaration_charged_once():
    res = run(deal(), deal())
    assert res['hist'][-1]['lovable']['spent_total'] == 500000
    assert sum('купили Rork' in l for l in res['logs']['lovable']) == 1


@pytest.mark.xfail(strict=True, reason='B10: M&A price is not checked against the buyer budget')
def test_price_above_budget_rejected():
    res = run(deal(price=5_000_000))
    assert res['owners']['rork'] == 'rork'
    assert res['hist'][0]['lovable']['spent_total'] == 0
