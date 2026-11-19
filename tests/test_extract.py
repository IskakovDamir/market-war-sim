import os

import pytest

from conftest import SAMPLES
from extract import extract, money

FILLED = open(os.path.join(SAMPLES, 'team_doc_filled_rork.md'), encoding='utf-8').read()
TEMPLATE = open(os.path.join(SAMPLES, 'team_doc_template.md'), encoding='utf-8').read()
B2 = pytest.mark.xfail(strict=True, reason='B2: unit letters inside words count as units')


@pytest.mark.parametrize('text,value', [
    ('$50k', 50000),
    ('50 000', 50000),
    ('50 000', 50000),
    ('$1.2M', 1200000),
    ('50к', 50000),
    ('50 тыс', 50000),
    ('1,5к', 1500),
    ('\\$20k', 20000),
    ('**30k**', 30000),
    ('', 0),
    ('   ', 0),
    ('abc', 0),
    ('не знаю', 0),
    ('n/a', 0),
    ('50,000', 50000),
    ('$1,200,000', 1200000),
    ('1,25M', 1250000),
])
def test_money(text, value):
    assert money(text) == value


@B2
def test_money_unit_inside_word():
    assert money('$29 со скидкой') == 29
    assert money('25 мес') == 25
    assert money('$40 в месяц') == 40


def test_extract_filled_doc_checkpoint_1():
    d = extract(FILLED, 1)
    assert d['company'] == 'Rork'
    assert d['positioning'].startswith('Для фаундеров, которым нужно мобильное приложение')
    assert d['ad'] == 'Твоё приложение в App Store через неделю'
    assert d['h1'] == 'Настоящее мобильное приложение'
    assert d['h2cta'] == 'iOS и Android из одного описания. Кнопка: Начать'
    assert d['plans'] == [dict(name='Free', price=0, what='5 сборок'),
                          dict(name='Pro', price=25, what='публикация в App Store')]
    assert d['icp'].startswith('Фаундеры без кода')
    assert d['war'].startswith('Захват сегмента')
    assert d['spend'] == {'creators': 20000, 'telegram': 20000}
    assert d['actions'] == [dict(card='Атака мы против X', params='Lovable, фаундеры', cost='30k')]
    assert d['deal'] == 'С v0: совместная реклама для фаундеров'
    assert 'target' not in d and 'learned' not in d and 'mna' not in d


@pytest.mark.parametrize('cp', [2, 3])
def test_extract_filled_doc_later_checkpoints_are_empty(cp):
    d = extract(FILLED, cp)
    assert d['company'] == 'Rork'
    assert d['plans'] == [] and d['spend'] == {} and d['actions'] == []
    assert d['positioning'] == '' and d['icp'] == ''
    keys = {'target', 'threat', 'counter', 'mna'} if cp == 2 else {'learned', 'change', 'mna'}
    assert keys <= set(d)


@pytest.mark.parametrize('cp', [1, 2, 3])
def test_extract_template_parses_every_checkpoint_as_empty(cp):
    d = extract(TEMPLATE, cp)
    assert d['company'] == ''
    assert d['plans'] == [] and d['spend'] == {} and d['actions'] == [] and d['econ'] == {}
    for k in ('positioning', 'ad', 'h1', 'h2cta', 'icp', 'war', 'custom', 'deal'):
        assert d[k] == '', k


def test_extract_reads_only_the_requested_checkpoint():
    doc = FILLED.replace('| Продажи | \\$40k | Сразу |  |', '| Продажи | \\$40k | Сразу || 45 000 |', 1)
    assert extract(doc, 1)['spend']['sales'] == 45000
    assert 'sales' not in extract(doc, 2)['spend']


def test_extract_free_plan_words():
    doc = FILLED.replace('| Free | бесплатно | 5 сборок |', '| Starter | $0 | 5 сборок |')
    assert extract(doc, 1)['plans'][0]['price'] == 0
    doc = FILLED.replace('| Free | бесплатно | 5 сборок |', '| Starter | free | 5 сборок |')
    assert extract(doc, 1)['plans'][0]['price'] == 0
