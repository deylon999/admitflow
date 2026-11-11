"""KAN-232: historical admission indicators are parsed strictly, reproducibly and without future leakage."""
import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import build_admission_history as history  # noqa: E402
import capture_admission_history as capture  # noqa: E402

FIXTURE = Path(__file__).with_name('fixtures')/'admission-history'/'sample.jsonl'


def records():
    return [json.loads(line) for line in FIXTURE.read_text(encoding='utf-8').splitlines()]


def build(items):
    heads, by_catalog = history.reference()
    return history.build(items, capture_sha256='0'*64, heads=heads, by_catalog=by_catalog)


def test_real_pages_parse_into_university_year_rows():
    rows, meta = build(records())
    assert rows and all(r['admission_year'] == r['edition'] - 1 for r in rows)
    first = next(r for r in rows if r['registry_id'] == '1' and r['edition'] == 2025)
    assert first['avg_ege_budget'] == 64.03 and first['avg_ege_paid'] == 57.52 and first['avg_min_ege'] == 51.43
    assert first['ogrn'] and first['region'] == 'Республика Адыгея' and first['ownership'] == 'state'
    assert first['target_admitted'] is None  # Not published in the sample: empty, never zero.
    assert first['source_url'].endswith('/iam/2025/_vpo/inst.php?id=1') and len(first['page_sha256']) == 64
    assert meta['pages']['parsed'] == len(rows)
    for row in rows:
        for column in history.SCORES:
            assert row[column] is None or 0 < row[column] <= 100


def test_output_is_reproducible_and_sorted():
    items = records()
    first = history.to_csv(build(items)[0])
    second = history.to_csv(build(list(reversed(items)))[0])
    assert first == second
    table = list(csv.DictReader(io.StringIO(first.decode())))
    assert [(int(r['registry_id']), int(r['edition'])) for r in table] == sorted((int(r['registry_id']), int(r['edition'])) for r in table)
    assert tuple(table[0]) == history.COLUMNS


@pytest.mark.parametrize('damage', [
    lambda r: r.update(url=r['url'].replace('id=', 'id=9')),
    lambda r: r.update(edition=2015, url=r['url'].replace('/2025/', '/2015/')),
    lambda r: r.update(registryId='999999999', url=r['url'].rsplit('=', 1)[0] + '=999999999'),
    lambda r: r.update(edu=r['edu'].replace('<td>0</td>', '<td>0,5</td>', 1)),
    lambda r: r.update(sha256=None),
    lambda r: r.update(edu=r['edu'].replace('64,03', '164,03')),
    lambda r: r.update(edu=r['edu'].replace('64,03', 'шестьдесят')),
])
def test_capture_problems_reject_the_whole_build(damage):
    items = records()
    target = next(r for r in items if r['registryId'] == '1' and r['edition'] == 2025)
    damage(target)
    with pytest.raises(history.CaptureError):
        build(items)


def test_duplicate_page_is_rejected():
    items = records()
    with pytest.raises(history.CaptureError, match='duplicate'):
        build(items + [items[0]])


def test_missing_pages_and_unknown_labels_are_counted_not_dropped():
    items = records()
    target = next(r for r in items if r['edu'])
    target['edu'] = target['edu'].replace('Усредненный по реализуемым', 'Новый показатель по реализуемым')
    gone = dict(items[1], status=404, info=None, edu=None, sha256=None)
    rows, meta = build([gone if r is items[1] else r for r in items])
    assert meta['pages'].get('http_404') == 1 and meta['pages'].get('no_institution_page') == 1
    assert any('Новый показатель' in label for label in meta['unknownLabels'])


def test_training_rows_never_see_campaigns_published_after_the_forecast_year():
    rows = [dict(admission_year=y) for y in range(2015, 2025)]
    seen = history.training_rows(rows, 2026)
    assert max(r['admission_year'] for r in seen) == 2024
    assert max(r['admission_year'] for r in history.training_rows(rows, 2024)) == 2022
    assert history.training_rows(rows, 2016) == []
    with pytest.raises(TypeError):
        history.training_rows(rows, '2026')


def test_committed_dataset_and_passport_agree():
    if not history.OUTPUT.exists():
        pytest.skip('dataset is not built yet: the capture needs a Russian network')
    table = list(csv.DictReader(io.StringIO(history.OUTPUT.read_text(encoding='utf-8'))))
    card = json.loads(history.PASSPORT.read_text(encoding='utf-8'))
    heads, _ = history.reference()
    assert card['rows'] == len(table) and card['headsInCatalog'] == len(heads)
    keys = [(r['registry_id'], r['edition']) for r in table]
    assert len(keys) == len(set(keys))
    assert all(r['registry_id'] in heads and int(r['admission_year']) == int(r['edition']) - 1 for r in table)
    assert all(not r[c] or 0 < float(r[c]) <= 100 for r in table for c in history.SCORES)
    assert sum(y['universities'] for y in card['years']) == len(table)
    assert card['groupLevel']['usableGroups'] == 0


def test_capture_keeps_only_the_needed_tables():
    sample = next(r for r in records() if r['edu'])
    page = f"<html><body><table id='x'><tr><td>menu</td></tr></table>{sample['info']}{sample['edu']}</body></html>".encode()
    row = capture.record(sample['registryId'], sample['edition'], lambda url: (200, page))
    assert row['sha256'] and row['info'] and row['edu'] and row['result'] is None
    values, _ = history.parse_edu(row['edu'])
    assert values == history.parse_edu(sample['edu'])[0]
    assert capture.record('1', 2025, lambda url: (404, b''))['edu'] is None
