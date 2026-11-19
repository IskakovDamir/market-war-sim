import copy
import json
import os
import subprocess
import sys

import pytest

from conftest import GOLDEN_FINAL, GOLDEN_GOALS, ROOT, SCRIPTS, golden, load_json
import sim


@pytest.fixture(scope='module')
def scores():
    return sim.final_scores(sim.run(golden()), {'rork': 'fnd'})


@pytest.mark.parametrize('cid', list(GOLDEN_GOALS))
def test_golden_goal(scores, cid):
    assert scores['goals'][cid] == pytest.approx(GOLDEN_GOALS[cid], abs=0.1)


@pytest.mark.parametrize('cid', list(GOLDEN_FINAL))
def test_golden_final(scores, cid):
    assert scores['final'][cid] == pytest.approx(GOLDEN_FINAL[cid], abs=0.1)


def test_same_seed_gives_identical_output():
    a = sim.run(golden(), seed=7)
    b = sim.run(golden(), seed=7)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    fa = sim.final_scores(a, {'rork': 'fnd'})
    fb = sim.final_scores(b, {'rork': 'fnd'})
    assert json.dumps(fa, sort_keys=True) == json.dumps(fb, sort_keys=True)


def test_seed_is_the_only_source_of_randomness():
    a = sim.run(golden(), seed=7)
    b = sim.run(golden(), seed=8)
    assert json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True)
    assert sim.run(golden())['hist'] == a['hist']  # default seed is 7


def test_run_does_not_mutate_moves():
    m = golden()
    before = copy.deepcopy(m)
    sim.run(m)
    assert m == before


def test_upto_is_a_prefix_of_the_full_game():
    full = sim.run(golden())
    two = sim.run(golden(), upto=2)
    assert len(two['hist']) == 2
    assert json.dumps(two['hist'], sort_keys=True) == json.dumps(full['hist'][:2], sort_keys=True)


def test_checkpoint_files_equal_the_full_game():
    g = golden()
    for cp in (1, 2, 3):
        assert load_json(f'moves_cp{cp}.json') == g['quarters'][cp - 1]


def test_report_cli_prints_golden_scores_from_any_cwd(tmp_path):
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'report.py'),
                          os.path.join(ROOT, 'samples', 'test_moves.json')],
                         cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    line = next(l for l in out.splitlines() if l.startswith('final '))
    assert "'lovable': 85.5" in line and "'rork': 78.1" in line
