import copy
import json
import os

import pytest

from conftest import CIDS, CO, ROOT, SAMPLES, golden
import dashboard
import sim
from extract import extract

DASHES = ('–', '—')
DOC = open(os.path.join(SAMPLES, 'team_doc_filled_rork.md'), encoding='utf-8').read()


def game_state():
    d = extract(DOC, 1)
    pub = dict(positioning=d['positioning'], ad=d['ad'], h1=d['h1'], h2='iOS и Android из одного описания',
               cta='Начать', plans=d['plans'], announce='')
    g = golden()
    return dict(public={'1': {'rork': pub}}, raw={'1': {'rork': d}}, quarters=g['quarters'], seed=7,
                icps={'rork': 'fnd'}, predictions={'bolt': {'lovable': 70000, 'rork': 10000}},
                bonus={'bolt': 5}, quotes={'rork': ['Наконец-то настоящее приложение']})


def all_views(state=None):
    s = state or game_state()
    r2 = sim.run({'quarters': s['quarters']}, upto=2)
    r3 = sim.run({'quarters': s['quarters']})
    fs = sim.final_scores(r3, s['icps'])
    return dict(wait=dashboard.view_wait(), public1=dashboard.view_public(s, 1),
                sim1=dashboard.view_sim1(s, r2), final=dashboard.view_final(s, r3, fs))


def test_every_view_shows_all_five_companies():
    for name, html in all_views().items():
        for c in CIDS:
            assert CO[c]['name'] in html, (name, c)


def test_public_view_shows_open_answers_only():
    s = game_state()
    html = dashboard.view_public(s, 1)
    raw = s['raw']['1']['rork']
    assert raw['positioning'] in html
    assert raw['icp'] not in html and raw['war'] not in html and raw['deal'] not in html
    assert html.count('ход не сдан') == 4


def test_sim1_shows_users_not_revenue():
    html = all_views()['sim1']
    assert '$' not in html
    assert '+5 баллов' in html


def test_final_adds_the_bonus_and_shows_quotes():
    s = game_state()
    html = all_views(s)['final']
    assert 'бонус +5' in html
    assert '«Наконец-то настоящее приложение»' in html


def test_dashboard_escapes_team_text():
    s = game_state()
    s['public']['1']['rork']['positioning'] = '<script>alert(1)</script>'
    html = dashboard.view_public(s, 1)
    assert '<script>alert' not in html and '&lt;script&gt;' in html


def test_docs_and_skill_text_have_no_em_or_en_dash():
    bad = []
    for base in ('references', 'reference'):
        for name in os.listdir(os.path.join(ROOT, base)):
            if name.endswith('.md'):
                bad += [f'{base}/{name}:{i}' for i, l in enumerate(open(os.path.join(ROOT, base, name), encoding='utf-8'), 1)
                        if any(d in l for d in DASHES)]
    for name in ('SKILL.md', 'README.md'):
        bad += [f'{name}:{i}' for i, l in enumerate(open(os.path.join(ROOT, name), encoding='utf-8'), 1)
                if any(d in l for d in DASHES)]
    assert bad == []


def test_no_em_or_en_dash_in_ui():
    s = game_state()
    for q in s['quarters']:
        q['rork'] = dict(q['rork'], spend={}, actions=[])  # no new payers -> no CAC
    for name, html in all_views(s).items():
        assert not any(d in html for d in DASHES), name
    src = open(os.path.join(ROOT, 'scripts', 'dashboard.py'), encoding='utf-8').read()
    assert not any(d in src for d in DASHES)


def test_final_names_the_winning_team_not_the_biggest_company():
    s = game_state()
    s['bonus'] = {}
    html = all_views(s)['final']
    assert 'победила команда Base44' in html  # Lovable has 2x the revenue, Base44 played its role better


def test_final_shows_where_each_team_started_and_what_its_role_needed():
    s = game_state()
    html = all_views(s)['final']
    for line in ('доля выручки рынка: <b>47% → 45%</b>',
                 'выручка в месяц: <b>$100k → $132k</b>',
                 '«Дизайнеры и продакты»: <b>№2 → №1</b>',
                 '«Малый бизнес и агентства»: <b>№2 → №1</b>',
                 '«Фаундеры без кода»: <b>7% → 14%</b>'):
        assert line in html, line
    assert html.count('старт → финиш') == 5
    assert 'нужно $200k · выполнено на 32%' in html


def test_rork_goal_line_follows_the_checkpoint_1_icp():
    s = game_state()
    s['icps'] = {'rork': 'smb'}
    rows = all_views(s)['final'].split('<div class="tm')[1:]
    rork = next(r for r in rows if 'data-company="rork"' in r)
    assert 'доля выручки в сегменте «Малый бизнес и агентства»: <b>' in rork
