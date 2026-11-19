import copy

import pytest

from conftest import CO, golden, move, quarter, run
import sim


def test_missing_submission_keeps_previous_offer_with_no_spend_and_no_cards():
    g = golden()
    del g['quarters'][1]['rork']
    res = sim.run(g)
    q1, q2 = res['hist'][0]['rork'], res['hist'][1]['rork']
    assert q2['spend'] == 0
    assert q2['spent_total'] == q1['spent_total']
    # Q1 move kept: same scores (fnd differs only because Lovable copies Rork there in Q2)
    for s in ('stud', 'des', 'dev', 'smb'):
        assert q2['score'][s] == q1['score'][s]
    assert q2['score']['fnd'] == q1['score']['fnd'] - 0.5
    full = sim.run(golden())
    assert full['hist'][1]['rork']['spend'] > 0


def test_missing_first_submission_uses_list_price_and_neutral_scores():
    res = run({'lovable': move('lovable')})
    r = res['hist'][0]['rork']
    assert r['spend'] == 0
    assert r['score'] == {'stud': 5.0, 'fnd': 6.0, 'des': 5.0, 'dev': 5.0, 'smb': 6.0}
    assert r['seg_arpu']['fnd'] == pytest.approx(CO['rork']['price'])


def test_missing_submission_is_not_a_crash_for_any_company():
    for cid in CO:
        g = golden()
        for q in g['quarters']:
            q.pop(cid)
        res = sim.run(g)
        assert res['hist'][-1][cid]['spent_total'] == 0


@pytest.mark.xfail(strict=True, reason='B3: unknown channel id crashes the run')
def test_unknown_channel_skipped():
    res = run(quarter(rork=dict(spend={'tiktok': 10000, 'creators': 20000})))
    assert res['hist'][0]['rork']['spent_total'] == 20000
    assert any('tiktok' in l for l in res['logs']['rork'])


@pytest.mark.xfail(strict=True, reason='B4: unknown action id is ignored without a log line')
def test_unknown_action_skipped():
    res = run(quarter(rork=dict(actions=[{'id': 'bribe'}])))
    assert res['hist'][0]['rork']['spent_total'] == 0
    assert any('bribe' in l for l in res['logs']['rork'])


@pytest.mark.xfail(strict=True, reason='B20: a known card with a missing field crashes the run')
def test_card_with_missing_fields_skipped():
    res = run(quarter(bolt=dict(actions=[{'id': 'attack', 'seg': 'fnd'}, {'id': 'copy'},
                                         {'id': 'exclusive'}, {'id': 'team_deal'}, {'id': 'mna'}])))
    assert res['hist'][0]['bolt']['spent_total'] == 0
    assert sum('пропущена' in l for l in res['logs']['bolt']) == 5


@pytest.mark.xfail(strict=True, reason='B14: unknown company id crashes the run')
def test_unknown_company_skipped():
    q = quarter()
    q['acme'] = move('rork')
    res = run(q)
    assert set(res['hist'][0]) == set(CO)
    assert any('acme' in w for w in res['warnings'])
