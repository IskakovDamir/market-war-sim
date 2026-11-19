"""live.py end to end in a temp folder, the way the host runs it in class."""
import json
import os
import subprocess
import sys

import pytest

from conftest import GOLDEN_FINAL, ROOT, SAMPLES, SCRIPTS, printed_scores

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
            final = printed_scores(res.stdout, 'final')
            for cid, value in GOLDEN_FINAL.items():
                assert final[cid] == pytest.approx(value, abs=0.1)
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


def test_render_wait_and_unknown_view(tmp_path):
    cli(tmp_path, 'reset')
    cli(tmp_path, 'render', 'wait', tmp_path / 'w.html')
    assert 'до старта игры' in (tmp_path / 'w.html').read_text(encoding='utf-8')
    bad = cli(tmp_path, 'render', 'finall', tmp_path / 'x.html', check=False)
    assert bad.returncode != 0
    assert not (tmp_path / 'x.html').exists()
    assert 'неизвестный экран' in bad.stderr
    empty = cli(tmp_path, 'render', 'final', tmp_path / 'f.html', check=False)
    assert empty.returncode != 0 and 'нет ходов' in empty.stderr


def test_public_view_before_ingest(tmp_path):
    cli(tmp_path, 'reset')
    cli(tmp_path, 'render', 'public2', tmp_path / 'p.html')
    assert (tmp_path / 'p.html').read_text(encoding='utf-8').count('ход не сдан') == 5


def test_ingest_helpers_scale_thousands_and_tidy_answers():
    sys.path.insert(0, SCRIPTS)
    import live
    assert live.thousands({'seo': 50, 'geo': 20}) == {'seo': 50000, 'geo': 20000}
    assert live.thousands({'seo': 50, 'geo': 20000}) == {'seo': 50, 'geo': 20000}   # one real number: leave as written
    assert live.thousands({}) == {}
    assert live.tidy('Заголовок: «Запустите MVP за выходные».') == 'Запустите MVP за выходные'
    assert live.tidy('"Для фаундеров без кода"') == 'Для фаундеров без кода'
    assert live.tidy('. Кнопка') == 'Кнопка'
    assert live.tidy('«Один» и «два»') == '«Один» и «два»'   # two quoted parts: not a wrapping pair


def test_ingest_keeps_previous_answers_and_forecast_in_thousands(tmp_path):
    def doc(cp, positioning, spend, plans, forecast=''):
        return '\n'.join([
            f'# **Чекпоинт {cp}. Ход**', '**Наша компания:** Rork', '',
            '| Поле | Кто | Статус | Ответ |', '| :---- | :---- | :---- | :---- |',
            f'| Позиционирование. Одна фраза | Strategic Growth | Обязательно | {positioning} |',
            '| Главная реклама: текст объявления | Conversion | Обязательно | «Приложение в App Store за неделю». |',
            '| Первый экран сайта: подзаголовок и текст кнопки | Conversion | Обязательно | Подзаголовок: Опиши идею. Кнопка: «Начать» |', '',
            '| Тариф | Цена в месяц | Что входит |', '| :---- | :---- | :---- |', *plans, '',
            '| Канал | Минимальная ставка | Когда работает | Сумма, $ |', '| :---- | :---- | :---- | :---- |', *spend, '',
            forecast, '# **END**'])
    (tmp_path / 'rork1.md').write_text(doc(1, 'Для фаундеров без кода', ['| SEO и контент | $20k | Медленно | 30 |', '| Продажи | $40k | Сразу | 40 |'],
                                            ['| Free | 0$ | |', '| Pro | 40$ | |', '| Max | по запросу | |']), encoding='utf-8')
    (tmp_path / 'rork2.md').write_text(doc(2, '', ['| Продажи | $40k | Сразу | 45,000 |'], [],
                                            '| Компания | Пользователей после симуляции 1 |\n| :---- | :---- |\n| Lovable | 70 |\n| Rork | 8 |\n'), encoding='utf-8')
    cli(tmp_path, 'reset')
    cli(tmp_path, 'ingest', 1, tmp_path / 'rork1.md')
    cli(tmp_path, 'ingest', 2, tmp_path / 'rork2.md')
    s = state(tmp_path)
    assert s['raw']['1']['rork']['spend'] == {'seo': 30000, 'sales': 40000}
    assert s['raw']['2']['rork']['spend'] == {'sales': 45000}
    p1, p2 = s['public']['1']['rork'], s['public']['2']['rork']
    assert p1['ad'] == 'Приложение в App Store за неделю'
    assert (p1['h2'], p1['cta']) == ('Опиши идею', 'Начать')
    assert p2['positioning'] == 'Для фаундеров без кода'   # empty answer keeps checkpoint 1
    assert p2['plans'] == p1['plans'] and p1['plans'][2]['price'] is None
    assert s['predictions'] == {'rork': {'lovable': 70000, 'rork': 8000}}
    mv = tmp_path / 'm.json'
    mv.write_text(json.dumps({'rork': {'icp': 'fnd', 'scores': {'fnd': 7}, 'consistency': 1, 'actions': []}}))
    cli(tmp_path, 'moves', 2, mv)
    assert state(tmp_path)['quarters'][1]['rork']['plans'] == [{'name': 'Free', 'price': 0}, {'name': 'Pro', 'price': 40}]


def test_sim1split_writes_the_room_page_and_one_page_per_team(tmp_path):
    cli(tmp_path, 'reset')
    assert cli(tmp_path, 'sim1split', tmp_path / 'sim1', check=False).returncode != 0
    for cp in (1, 2):
        cli(tmp_path, 'moves', cp, os.path.join(SAMPLES, f'moves_cp{cp}.json'))
    out = cli(tmp_path, 'sim1split', tmp_path / 'sim1').stdout
    names = sorted(p.name for p in (tmp_path / 'sim1').iterdir())
    assert names == sorted(['market.html', 'lovable.html', 'bolt.html', 'v0.html', 'base44.html', 'rork.html'])
    assert 'рынок после двух кварталов' in (tmp_path / 'sim1' / 'market.html').read_text(encoding='utf-8')
    assert 'Только для команды Rork' in (tmp_path / 'sim1' / 'rork.html').read_text(encoding='utf-8')
    assert 'rendered' in out
