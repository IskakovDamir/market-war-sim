import pytest

from conftest import CIDS, CO, golden, move, quarter, run
import sim


def assert_within_budget(res):
    for qi, h in enumerate(res['hist']):
        groups = {}
        for c in CIDS:
            groups.setdefault(res['owners'][c], []).append(c)
        for owner, members in groups.items():
            spent = sum(h[c]['spent_total'] for c in members)
            budget = sum(CO[c]['budget'] for c in members)
            assert spent <= budget + 1e-6, (qi + 1, owner, spent, budget)


def test_golden_game_never_exceeds_budget():
    res = sim.run(golden())
    assert_within_budget(res)
    for h in res['hist']:
        for c in CIDS:
            assert h[c]['budget_left'] >= -1e-6


def test_everyone_overspending_for_three_quarters_stays_within_budget():
    q = {c: move(c, spend={'social': CO[c]['budget'], 'creators': CO[c]['budget'] / 2}) for c in CIDS}
    res = run(q, q, q)
    assert_within_budget(res)
    for c in CIDS:
        assert res['hist'][-1][c]['spent_total'] == pytest.approx(CO[c]['budget'])


def test_overspend_scales_channels_down_proportionally():
    res = sim.run(golden())
    h2, h3 = res['hist'][1]['base44'], res['hist'][2]['base44']
    left = h2['budget_left']
    assert left == 90000
    # Q3: sales 60k + search 40k + decoy 10k = 110k > 90k -> channels x (90k - 10k) / 100k = 80%
    assert h3['spend'] == pytest.approx(left)
    assert 'Q3: перерасход, траты на каналы урезаны до 80%' in res['logs']['base44']


def test_overspend_keeps_the_channel_mix():
    big = move('rork', spend={'social': 200000, 'creators': 100000})
    small = move('rork', spend={'social': 100000, 'creators': 50000})
    a = run(quarter(rork=big))
    b = run(quarter(rork=small))
    # 300k asked with 150k budget scales to exactly the 150k request
    assert a['hist'][0]['rork']['spend'] == pytest.approx(150000)
    assert a['hist'][0]['rork']['arrivals'] == pytest.approx(b['hist'][0]['rork']['arrivals'])


def test_cards_cannot_exceed_budget():
    res = run(quarter(rork=dict(spend={'creators': 150000})),
              quarter(rork=dict(actions=[{'id': 'copy', 'target': 'v0', 'seg': 'des'}])))
    assert res['hist'][-1]['rork']['spent_total'] <= 150000
    assert_within_budget(res)
    assert res['hist'][-1]['rork']['score']['des'] == 5.0  # the card was not played
    assert 'Q2: не хватает бюджета на карточку «Скопировать фичу соперника», карточка не сыграна' in res['logs']['rork']


def test_cards_that_fit_are_played_in_order_and_channels_get_the_rest():
    acts = [{'id': 'onboarding'}, {'id': 'copy', 'target': 'v0', 'seg': 'des'}, {'id': 'decoy'}]
    res = run(quarter(rork=dict(spend={'creators': 100000})),
              quarter(rork=dict(spend={'creators': 30000}, actions=acts)))
    q2 = res['hist'][1]['rork']
    # 50k left: onboarding 30k fits, copy 60k does not, decoy 10k fits, channels get 10k of 30k
    assert q2['spend'] == pytest.approx(50000)
    assert q2['spent_total'] == pytest.approx(150000)
    assert any('«Скопировать фичу соперника»' in l for l in res['logs']['rork'])
    assert 'Q2: перерасход, траты на каналы урезаны до 33%' in res['logs']['rork']


def test_referral_cannot_exceed_budget():
    res = run(quarter(bolt=dict(spend={'social': 580000}, actions=[{'id': 'referral'}])))
    assert res['hist'][-1]['bolt']['spent_total'] == pytest.approx(600000)
    assert any('рефералка урезана' in l for l in res['logs']['bolt'])
    full = run(quarter(bolt=dict(actions=[{'id': 'referral'}])))
    invites = (4000 + 30000) * 0.06 * (sum(full['hist'][0]['bolt']['score'].values()) / 5 / 6)
    assert full['hist'][0]['bolt']['spent_total'] == pytest.approx(20000 + 10 * invites)
