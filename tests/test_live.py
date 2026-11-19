"""live.py end to end in a temp folder, the way the host runs it in class."""
import json
import os
import subprocess
import sys

import pytest

from conftest import ROOT, SAMPLES, SCRIPTS

LIVE = os.path.join(SCRIPTS, 'live.py')
DOC = os.path.join(SAMPLES, 'team_doc_filled_rork.md')


def cli(tmp_path, *args, check=True):
    env = dict(os.environ, MARKET_WAR_LIVE=str(tmp_path / 'live'))
    p = subprocess.run([sys.executable, LIVE, *map(str, args)], cwd=tmp_path, env=env,
                       capture_output=True, text=True)
    if check:
        assert p.returncode == 0, p.stderr
    return p


def state(tmp_path):
    return json.load(open(tmp_path / 'live' / 'state.json', encoding='utf-8'))


def test_live_end_to_end_in_a_temp_dir(tmp_path):
    assert cli(tmp_path, 'reset').stdout.strip() == 'reset'
    out = cli(tmp_path, 'ingest', 1, DOC, os.path.join(SAMPLES, 'team_doc_template.md')).stdout
    assert '=== rork' in out
    assert '!! не понял компанию' in out  # the empty template names no company
    for cp in (2, 3):
        cli(tmp_path, 'ingest', cp, DOC)
    for cp in (1, 2, 3):
        assert 'ok' in cli(tmp_path, 'moves', cp, os.path.join(SAMPLES, f'moves_cp{cp}.json')).stdout
    pages = {}
    for view in ('public1', 'public2', 'public3', 'sim1', 'final'):
        dest = tmp_path / f'{view}.html'
        res = cli(tmp_path, 'render', view, dest)
        assert f'rendered {dest}' in res.stdout
        pages[view] = dest.read_text(encoding='utf-8')
        if view == 'final':
            assert "'final': {'lovable': 85.5, 'bolt': 25.2, 'v0': 74.5, 'base44': 90.7, 'rork': 78.1}" in res.stdout
    assert 'после чекпоинта 1' in pages['public1']
    assert 'Твоё приложение в App Store через неделю' in pages['public1']
    assert 'пользователи после двух кварталов' in pages['sim1']
    assert 'итоги рынка' in pages['final']
    s = state(tmp_path)
    assert len(s['quarters']) == 3 and s['icps']['rork'] == 'fnd'
    assert not (tmp_path / 'live' / 'index.html').exists()
    cli(tmp_path, 'render', 'public1')
    assert (tmp_path / 'live' / 'index.html').exists()
    assert cli(tmp_path, 'reset').stdout.strip() == 'reset'
    assert not (tmp_path / 'live' / 'state.json').exists()


def test_moves_fill_plans_and_spend_from_the_ingested_doc(tmp_path):
    cli(tmp_path, 'reset')
    cli(tmp_path, 'ingest', 1, DOC)
    mv = tmp_path / 'm.json'
    mv.write_text(json.dumps({'rork': {'icp': 'smb', 'scores': {'fnd': 8}, 'consistency': 1, 'actions': []}}))
    cli(tmp_path, 'moves', 1, mv)
    m = state(tmp_path)['quarters'][0]['rork']
    assert m['plans'] == [{'name': 'Free', 'price': 0}, {'name': 'Pro', 'price': 25}]
    assert m['spend'] == {'creators': 20000, 'telegram': 20000}
    assert state(tmp_path)['icps'] == {'rork': 'smb'}


def test_icp_is_fixed_at_checkpoint_1_only(tmp_path):
    cli(tmp_path, 'reset')
    for cp, icp in ((1, 'fnd'), (2, 'smb')):
        mv = tmp_path / f'm{cp}.json'
        mv.write_text(json.dumps({'rork': {'icp': icp}}))
        cli(tmp_path, 'moves', cp, mv)
    assert state(tmp_path)['icps'] == {'rork': 'fnd'}
    assert state(tmp_path)['quarters'][1]['rork']['plans'] == [{'name': 'Pro', 'price': 25}]


@pytest.mark.xfail(strict=True, reason='B15: unknown view names render the final view')
def test_render_wait_and_unknown_view(tmp_path):
    cli(tmp_path, 'reset')
    cli(tmp_path, 'render', 'wait', tmp_path / 'w.html')
    assert 'до старта игры' in (tmp_path / 'w.html').read_text(encoding='utf-8')
    bad = cli(tmp_path, 'render', 'finall', tmp_path / 'x.html', check=False)
    assert bad.returncode != 0
    assert not (tmp_path / 'x.html').exists()


@pytest.mark.xfail(strict=True, reason='B16: public view of a checkpoint nobody submitted crashes')
def test_public_view_before_ingest(tmp_path):
    cli(tmp_path, 'reset')
    cli(tmp_path, 'render', 'public2', tmp_path / 'p.html')
    assert (tmp_path / 'p.html').read_text(encoding='utf-8').count('ход не сдан') == 5
