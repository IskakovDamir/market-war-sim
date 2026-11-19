import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, 'scripts')
SAMPLES = os.path.join(ROOT, 'samples')
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import sim  # noqa: E402
from spec import COMPANIES, SEG_IDS  # noqa: E402

CIDS = [c['id'] for c in COMPANIES]
CO = {c['id']: c for c in COMPANIES}

# Golden game: samples/test_moves.json, seed 7, Rork ICP fnd.
GOLDEN_GOALS = dict(lovable=100, bolt=32.4, v0=100, base44=100, rork=68.7)
GOLDEN_FINAL = dict(lovable=85.5, bolt=25.2, v0=74.5, base44=90.7, rork=78.1)

# Scores that cancel the asset bonus, so every company has the same effective score 5
# and nobody switches: a quiet market where one effect can be measured alone.
QUIET_SCORES = {
    'lovable': {s: 5 for s in SEG_IDS},
    'bolt': dict(stud=4, fnd=5, des=5, dev=4, smb=5),
    'v0': {s: 5 for s in SEG_IDS},
    'base44': {s: 5 for s in SEG_IDS},
    'rork': dict(stud=5, fnd=4, des=5, dev=5, smb=4),
}
FREE_PRO = [{'name': 'Free', 'price': 0}, {'name': 'Pro', 'price': 25}]


def printed_scores(stdout, key):
    """The {'goals': {...}, 'final': {...}} or "final {...}" dict a CLI printed, as numbers."""
    import ast
    for line in stdout.splitlines():
        if line.startswith(key + ' '):
            return ast.literal_eval(line[len(key) + 1:])
        if line.startswith('{') and f"'{key}'" in line:
            return ast.literal_eval(line)[key]
    raise AssertionError(f'{key} not printed:\n{stdout}')


def load_json(name):
    with open(os.path.join(SAMPLES, name), encoding='utf-8') as f:
        return json.load(f)


def golden():
    return load_json('test_moves.json')


def move(cid, **kw):
    """A quiet move for one company; keyword arguments override fields."""
    m = dict(plans=copy.deepcopy(FREE_PRO), icp='fnd', scores=dict(QUIET_SCORES[cid]),
             consistency=1, spend={}, actions=[])
    m.update(copy.deepcopy(kw))
    return m


def quarter(**overrides):
    """All five companies quiet; overrides maps company id -> dict of fields."""
    return {cid: move(cid, **overrides.get(cid, {})) for cid in CIDS}


def run(*quarters, seed=7):
    return sim.run({'quarters': list(quarters)}, seed=seed)


def start_paid(cid):
    return sum(CO[cid]['paid'].values())


@pytest.fixture
def golden_moves():
    return golden()
