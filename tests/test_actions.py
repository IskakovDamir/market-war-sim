import pytest

from conftest import golden, move, quarter, run, start_paid
import sim
from spec import SEG_IDS


def test_overpromise_lifts_conversion_30_percent_then_refunds_half():
    base = run(quarter(lovable=dict(spend={'social': 100000})))['hist'][0]['lovable']
    res = run(quarter(lovable=dict(spend={'social': 100000}, actions=[{'id': 'overpromise'}])))
    op = res['hist'][0]['lovable']
    assert op['new_paid'] == pytest.approx(base['new_paid'] * 1.30)
    expected = (start_paid('lovable') + op['new_paid']) * 0.75 - 0.5 * op['new_paid']
    assert op['paid'] == pytest.approx(expected)
    assert op['paid'] < base['paid']  # the trap: fewer payers than without the card
    assert any('возвраты после обещания' in l for l in res['logs']['lovable'])


def test_overpromise_costs_one_point_next_quarter_only():
    res = run(quarter(lovable=dict(actions=[{'id': 'overpromise'}])), quarter(), quarter())
    scores = [h['lovable']['score'] for h in res['hist']]
    assert scores[0] == {s: 5.0 for s in SEG_IDS}
    assert scores[1] == {s: 4.0 for s in SEG_IDS}
    assert scores[2] == {s: 5.0 for s in SEG_IDS}


def _deal(partner_declares, partner_points_to='rork'):
    rork = dict(actions=[{'id': 'team_deal', 'partner': 'v0', 'seg': 'fnd'}])
    v0 = dict(actions=[{'id': 'team_deal', 'partner': partner_points_to, 'seg': 'fnd'}]) if partner_declares else {}
    return run(quarter(rork=rork, v0=v0))['hist'][0]


def test_team_deal_applies_only_when_both_sides_declare_it():
    one = _deal(False)
    both = _deal(True)
    assert one['rork']['score']['fnd'] == 5.0  # 4 + asset 1
    assert one['v0']['score']['fnd'] == 5.0
    assert both['rork']['score']['fnd'] == 5.5
    assert both['v0']['score']['fnd'] == 5.5
    assert both['rork']['score']['des'] == 5.0


def test_team_deal_with_the_wrong_partner_does_not_count():
    wrong = _deal(True, partner_points_to='bolt')
    assert wrong['rork']['score']['fnd'] == 5.0
    assert wrong['v0']['score']['fnd'] == 5.0


def test_decoy_is_charged_once_per_game():
    res = run(quarter(base44=dict(actions=[{'id': 'decoy'}])), quarter(base44=dict(actions=[{'id': 'decoy'}])))
    assert res['hist'][0]['base44']['spend'] == 10000
    assert res['hist'][1]['base44']['spend'] == 0


def test_viral_roll_is_deterministic_and_logged():
    a = sim.run(golden())
    b = sim.run(golden())
    roll = [l for l in a['logs']['bolt'] if 'вирусная акция' in l]
    assert roll == ['Q3: вирусная акция, кубик 5: +15,000 пользователей']
    assert roll == [l for l in b['logs']['bolt'] if 'вирусная акция' in l]


def test_attack_with_higher_score_takes_rival_payers():
    hi = dict(scores={**{s: 5 for s in SEG_IDS}, 'fnd': 8, 'stud': 4, 'dev': 4})
    without = run(quarter(bolt=hi))['hist'][0]
    res = run(quarter(bolt=dict(hi, actions=[{'id': 'attack', 'target': 'lovable', 'seg': 'fnd'}])))
    with_ = res['hist'][0]
    look = 0.10 * 3500
    assert with_['lovable']['seg_paid']['fnd'] == pytest.approx(without['lovable']['seg_paid']['fnd'] - look * 0.75)
    assert with_['bolt']['seg_paid']['fnd'] == pytest.approx(without['bolt']['seg_paid']['fnd'] + look * 0.75)
    assert with_['bolt']['spend'] == 30000
    assert any('сработала' in l for l in res['logs']['bolt'])


def test_attack_with_lower_score_backfires():
    lo = dict(scores={**{s: 5 for s in SEG_IDS}, 'fnd': 4, 'stud': 4, 'dev': 4})
    without = run(quarter(bolt=lo))['hist'][0]
    res = run(quarter(bolt=dict(lo, actions=[{'id': 'attack', 'target': 'lovable', 'seg': 'fnd'}])))
    loss = 0.05 * 1200
    assert res['hist'][0]['bolt']['seg_paid']['fnd'] == pytest.approx(
        without['bolt']['seg_paid']['fnd'] - loss * 0.75)
    assert any('ударила по вам' in l for l in res['logs']['bolt'])


def test_copy_adds_a_point_and_halves_the_rival_asset():
    copy_card = {'id': 'copy', 'target': 'rork', 'seg': 'fnd'}
    res = run(quarter(lovable=dict(actions=[copy_card])), quarter(lovable=dict(actions=[copy_card])))
    q1, q2 = res['hist'][0], res['hist'][1]
    assert q1['lovable']['score']['fnd'] == 6.0
    assert q1['rork']['score']['fnd'] == 4.5  # 4 + asset 1 x 50%
    # second copy in the game: positioning blurs, -0.5 everywhere
    assert q2['lovable']['score']['fnd'] == 5.5
    assert q2['lovable']['score']['des'] == 4.5
    assert q1['lovable']['spend'] == 60000


def test_events_give_half_a_point_in_the_icp_next_quarter():
    res = run(quarter(v0=dict(icp='des', spend={'events': 30000})), quarter(v0=dict(icp='des')))
    assert res['hist'][0]['v0']['score']['des'] == 5.0
    assert res['hist'][1]['v0']['score']['des'] == 5.5
    assert res['hist'][1]['v0']['score']['fnd'] == 5.0


def test_telegram_above_60k_costs_a_point_everywhere():
    res = run(quarter(rork=dict(spend={'telegram': 61000})))
    assert res['hist'][0]['rork']['score']['stud'] == 4.0
    assert res['hist'][0]['rork']['score']['fnd'] == 4.0  # 4 + asset 1 - 1
    assert any('перебор с Telegram' in l for l in res['logs']['rork'])


def test_free_tier_brings_more_users_and_fewer_payers_per_user():
    base = run(quarter(lovable=dict(spend={'social': 100000})))['hist'][0]['lovable']
    ft = run(quarter(lovable=dict(spend={'social': 100000}, actions=[{'id': 'free_tier'}])))['hist'][0]['lovable']
    for s in SEG_IDS:
        assert ft['arrivals'][s] == pytest.approx(base['arrivals'][s] * 1.4)
    assert ft['new_paid'] == pytest.approx(base['new_paid'] * 1.4 * 0.75)


@pytest.mark.xfail(strict=True, reason='B11: exclusive partner works in the quarter it is bought')
def test_exclusive_starts_next_quarter():
    def users(card_q1, spend_q):
        acts = [{'id': 'exclusive', 'seg': 'smb'}] if card_q1 else []
        q1 = quarter(base44=dict(icp='smb', actions=acts, spend={'partners': 40000} if spend_q == 1 else {}))
        q2 = quarter(base44=dict(icp='smb', spend={'partners': 40000} if spend_q == 2 else {}))
        return run(q1, q2, quarter())['hist'][spend_q]['base44']['arrivals']['smb']
    assert users(True, 1) == pytest.approx(users(False, 1))  # bought in Q1: Q1 money is not discounted
    assert users(True, 2) == pytest.approx(users(False, 2) / 0.6)  # from Q2 on: x0.6 cost for the owner


@pytest.mark.xfail(strict=True, reason='B13: custom card "as" mapping is ignored by churn and arrivals')
def test_custom_as_onboarding_cuts_churn():
    real = run(quarter(v0=dict(actions=[{'id': 'onboarding'}])))['hist'][0]['v0']
    custom = run(quarter(v0=dict(actions=[{'id': 'custom', 'cost': 30000, 'as': 'onboarding'}])))['hist'][0]['v0']
    assert custom['paid'] == pytest.approx(real['paid'])
    ft = run(quarter(v0=dict(spend={'creators': 50000}, actions=[{'id': 'free_tier'}])))['hist'][0]['v0']
    cft = run(quarter(v0=dict(spend={'creators': 50000},
                              actions=[{'id': 'custom', 'cost': 20000, 'as': 'free_tier'}])))['hist'][0]['v0']
    assert cft['arrivals'] == pytest.approx(ft['arrivals'])
