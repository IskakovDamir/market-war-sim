"""Run every check and print a PASS/FAIL table. Exit 0 only when every row passes.

python3 tools/check_all.py

1. dev venv      creates .venv from requirements-dev.txt and installs Playwright Chromium when missing
2. compile       byte-compiles every .py in scripts/, tools/ and tests/ with this interpreter
3. pytest        tests/ in the venv: at least 40 passed, nothing failed
4. visual check  tools/visual_check.py: 6 views x 2 viewports, screenshots to reference/proof/
5. golden game   samples/test_moves.json, seed 7: goals and final scores within 0.1 of the reference
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(ROOT, '.venv')
VPY = os.path.join(VENV, 'bin', 'python')
GOALS = dict(lovable=100, bolt=32.4, v0=100, base44=100, rork=68.7)
FINAL = dict(lovable=85.5, bolt=25.2, v0=74.5, base44=90.7, rork=78.1)
MIN_TESTS = 40


def sh(*cmd, timeout=900):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def check_venv():
    if not os.path.exists(VPY):
        code, out = sh(sys.executable, '-m', 'venv', VENV)
        if code:
            return False, 'python3 -m venv failed: ' + out.strip()[-200:]
    code, _ = sh(VPY, '-c', 'import pytest, playwright')
    if code:
        code, out = sh(VPY, '-m', 'pip', 'install', '-q', '-r', 'requirements-dev.txt')
        if code:
            return False, 'pip install failed: ' + out.strip()[-200:]
    code, out = sh(VPY, '-m', 'playwright', 'install', 'chromium')
    if code:
        return False, 'playwright install chromium failed: ' + out.strip()[-200:]
    code, out = sh(VPY, '-c', 'import pytest, playwright.sync_api; print(pytest.__version__)')
    return code == 0, f'.venv ready, pytest {out.strip()}' if code == 0 else out.strip()[-200:]


def check_compile():
    files = [os.path.join(d, f) for sub in ('scripts', 'tools', 'tests')
             for d, _, fs in os.walk(os.path.join(ROOT, sub)) if '__pycache__' not in d
             for f in fs if f.endswith('.py')]
    bad = []
    for f in files:
        try:
            compile(open(f, encoding='utf-8').read(), f, 'exec')   # byte-compile, write nothing
        except SyntaxError as e:
            bad.append(f'{os.path.relpath(f, ROOT)}:{e.lineno}: {e.msg}')
    return not bad, f'{len(files)} files' if not bad else '; '.join(bad)


def check_pytest():
    code, out = sh(VPY, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests')
    counts = {k: int(v) for v, k in re.findall(r'(\d+) (passed|failed|errors?|xfailed|xpassed|skipped)', out)}
    passed, failed = counts.get('passed', 0), counts.get('failed', 0) + counts.get('error', 0) + counts.get('errors', 0)
    detail = ', '.join(f'{v} {k}' for k, v in counts.items()) or out.strip()[-200:]
    return code == 0 and passed >= MIN_TESTS and failed == 0, detail


def check_visual():
    code, out = sh(VPY, os.path.join('tools', 'visual_check.py'))
    m = re.search(r'(\d+)/(\d+) pages pass', out)
    detail = f'{m.group(1)}/{m.group(2)} pages, screenshots in reference/proof/' if m else out.strip()[-300:]
    if code:
        detail += '; ' + '; '.join(l.strip() for l in out.splitlines() if l.startswith('FAIL') or l.startswith('      -'))[:400]
    return code == 0, detail


def check_golden():
    sys.path.insert(0, os.path.join(ROOT, 'scripts'))
    import json
    import sim
    moves = json.load(open(os.path.join(ROOT, 'samples', 'test_moves.json'), encoding='utf-8'))
    fs = sim.final_scores(sim.run(moves, seed=7), {'rork': 'fnd'})
    off = [f'{k} {c} {fs[k][c]:.2f} vs {ref[c]}' for k, ref in (('goals', GOALS), ('final', FINAL))
           for c in ref if abs(fs[k][c] - ref[c]) > 0.1]
    shown = ' '.join(f'{c} {fs["final"][c]:.1f}' for c in FINAL)
    return not off, f'final {shown}' if not off else '; '.join(off)


def main():
    rows = []
    ok_venv, detail = check_venv()
    rows.append(('dev venv', ok_venv, detail))
    rows.append(('compile', *check_compile()))
    for name, fn in (('pytest', check_pytest), ('visual check', check_visual)):
        rows.append((name, *fn()) if ok_venv else (name, False, 'skipped: no dev venv'))
    rows.append(('golden game', *check_golden()))
    print(f'{"CHECK":14s} {"RESULT":6s}  DETAIL')
    for name, ok, detail in rows:
        print(f'{name:14s} {"PASS" if ok else "FAIL":6s}  {detail}')
    all_ok = all(ok for _, ok, _ in rows)
    print('ALL PASS' if all_ok else 'SOME CHECKS FAILED')
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
