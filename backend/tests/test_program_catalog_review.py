"""Synthetic documents exercise extraction; real-original evidence lives in reviews."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from app.program_catalog_review import EXTRACTORS, extract_reviewed, load_reviews

HSE = '''<div id="w-3369"><p class="lead">В 2027 году: бакалаврские программы
<a href="http://design.hse.ru/ba/program/fashion">«Example Fashion»</a>,
<a href="http://design.hse.ru/ba/program/art">«Example Art»</a>
(Школа дизайна НИУ ВШЭ — Москва),
<a href="http://design.hse.ru/ba/program/branch">«Example Fashion»</a> Санкт-Петербург.</p></div>
<p>В 2026 году 100 мест, бюджет, ЕГЭ: эти сведения не относятся к2027.</p>'''
SGU = '''<li class="burger-menu__wrap-sub-disclosure"><a class="burger-menu__sub-disclosure">Приём 2026</a>
<a href="https://www.sgu.ru/node/240763">Source plan</a></li>
<h2>Количество мест по очной форме обучения</h2><div class="subtitle">СГУ (головной вуз) Бакалавриат</div>
<table><tr><th>Faculty</th><th>Programme</th><th>Бюджет (общее число мест)</th><th>15.04.2026</th><th>Special</th><th>Отдельная квота</th><th>платных</th><th></th></tr>
<tr><td>Faculty A</td><td class="direction-name">06.03.01 Example Biology</td><td>50</td><td></td><td>5</td><td>5</td><td>15</td><td></td></tr>
<tr><td>Faculty B</td><td><div class="direction-name">05.03.02 Example Geography</div></td><td>15</td><td></td><td>2</td><td>2</td><td>15</td><td></td></tr></table>'''


def package(source):
    hse = source == 'hse'
    text = HSE if hse else SGU
    review = dict(university_id='miccedu-1766' if hse else 'sgu-saratov', year=2027 if hse else 2026,
        level='bachelor', url='https://design.hse.ru/ba/join' if hse else 'https://www.sgu.ru/node/240763',
        original_sha256=hashlib.sha256(text.encode()).hexdigest(),
        extractor_version='hse-moscow-announcement-v1' if hse else 'sgu-head-full-time-plan-v1',
        selection=[dict(source_key=k) for k in (['/ba/program/fashion', '/ba/program/art'] if hse else ['06.03.01', '05.03.02'])])
    review['programs'] = EXTRACTORS[review['extractor_version']](BeautifulSoup(text, 'html.parser'), review)
    return text.encode(), review


def test_target_announcement_does_not_import_historical_conditions():
    body, review = package('hse')
    result = extract_reviewed(body, review)
    assert [p['title'] for p in result] == ['Example Fashion', 'Example Art']
    assert all(p['code'] is p['study_form'] is p['funding'] is p['category'] is p['seats'] is None for p in result)
    assert all(p['groups'] == [] and p['admission_totals'] is None for p in result)


def test_totals_quotas_and_blank_targets_are_not_general_competition_seats():
    body, review = package('sgu')
    result = extract_reviewed(body, review)
    assert [p['code'] for p in result] == ['06.03.01', '05.03.02']
    assert result[0]['admission_totals'] == dict(budget_total=50, target_quota=None, special_quota=5, separate_quota=5, paid_total=15)
    assert all(p['seats'] is None and p['funding'] is None and p['category'] is None and p['groups'] == [] for p in result)
    assert all(p['study_form'] == 'full-time' for p in result)


@pytest.mark.parametrize('source', ['hse', 'sgu'])
def test_hash_and_reviewed_facts_cannot_be_changed_silently(source):
    body, review = package(source)
    with pytest.raises(ValueError, match='original_hash_mismatch'):
        extract_reviewed(body + b' ', review)
    changed = deepcopy(review)
    changed['programs'][0]['seats'] = 0
    with pytest.raises(ValueError, match='review_facts_mismatch'):
        extract_reviewed(body, changed)
    changed = deepcopy(review)
    changed['year'] += 1
    with pytest.raises(ValueError, match='campaign_mismatch'):
        extract_reviewed(body, changed)


def test_same_title_from_a_branch_is_not_a_moscow_programme():
    body, review = package('hse')
    review['selection'][0]['source_key'] = '/ba/program/branch'
    with pytest.raises(ValueError, match='university_scope_mismatch'):
        extract_reviewed(body, review)


@pytest.mark.parametrize('before,after', [
    ('СГУ (головной вуз)', 'СГУ (филиал)'), ('по очной форме', 'по заочной форме'),
    ('(общее число мест)', '(неизвестная колонка)'), ('<td>50</td>', '<td>unknown</td>'),
])
def test_new_structures_are_rejected_even_after_a_new_checksum_is_declared(before, after):
    body, review = package('sgu')
    changed = body.decode().replace(before, after).encode()
    review['original_sha256'] = hashlib.sha256(changed).hexdigest()
    with pytest.raises(ValueError):
        extract_reviewed(changed, review)


def test_review_package_keeps_actual_target_and_archive_years_separate():
    reviews = load_reviews()
    assert {r['key']: (r['university_id'], r['year']) for r in reviews} == {
        'hse-design-2027': ('miccedu-1766', 2027), 'sgu-seats-2026': ('sgu-saratov', 2026),
        'hse-urban-planning-2027': ('miccedu-1766', 2027), 'nntu-metallurgy-2027': ('miccedu-169', 2027),
    }
    assert all(r['completeness'] == 'partial' for r in reviews)
    assert all(len(r['original_sha256']) == 64 for r in reviews)


@pytest.mark.parametrize(('change', 'error'), [
    ('archive', 'catalog_campaign_mismatch'),
    ('branch', 'catalog_university_scope_mismatch'),
    ('form', 'catalog_campaign_mismatch'),
    ('profile', 'catalog_program_identity_ambiguous'),
    ('placement', 'catalog_source_structure_changed'),
    (None, None),
])
def test_pdf_requires_the_approved_admission_scope(monkeypatch, change, error):
    import pypdf

    byte_fixture = b'synthetic PDF input, page content supplied by test'
    review = next(r for r in load_reviews() if r['key'] == 'nntu-metallurgy-2027')
    review['original_sha256'] = hashlib.sha256(byte_fixture).hexdigest()
    cover = ('Нижегородский государственный технический университет им. Р.Е. Алексеева\n'
             'Кафедра «Металлургические технологии и оборудование»')
    admission = ('В 2027 году проводится приём для ОЧНОГО обучения по следующим образовательным программам:\n'
                 'Бакалавриат 22.03.02 «Металлургия»\nПрофиль «Производство и сбыт металлопродукции»\n'
                 'Магистратура 22.04.02 «Металлургия»')
    if change == 'archive':
        admission = admission.replace('2027', '2026')
    if change == 'branch':
        cover = 'Иной филиал того же университета'
    if change == 'form':
        admission = admission.replace('ОЧНОГО', 'ЗАОЧНОГО')
    if change == 'profile':
        admission = admission.replace('Производство и сбыт металлопродукции', 'Иной профиль')
    if change == 'placement':
        admission = admission.replace('Бакалавриат', 'Перечень программ: Бакалавриат')
    monkeypatch.setattr(pypdf, 'PdfReader', lambda *a, **kw: SimpleNamespace(is_encrypted=False,
        pages=[SimpleNamespace(extract_text=lambda: cover), SimpleNamespace(extract_text=lambda: admission)]))
    if error:
        with pytest.raises(ValueError, match=error):
            extract_reviewed(byte_fixture, review)
    else:
        assert extract_reviewed(byte_fixture, review) == review['programs']
