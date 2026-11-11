"""Historical admission indicators of Russian universities for ML (KAN-232).

Source: the official monitoring of higher education (MICCEDU), institution
pages /iam/<edition>/_vpo/inst.php?id=<id>, editions 2016-2025. Each edition
reports the previous calendar year: the 2025 edition says that salary data
"за 2024 год" is closed, so edition E describes the admission campaign E-1.

Grain: university x admission year. The monitoring publishes no competition
group cutoffs, so this dataset has no group-level labels; that is stated in
the passport instead of being approximated.

Input: capture records (JSON lines, optionally gzip), one per page:
    {"registryId", "edition", "url", "fetchedAt", "status", "bytes", "sha256",
     "info": <table#info HTML or null>, "edu": <indicator table HTML or null>, "result": ...}
Records come from scripts/capture_admission_history.py or the equivalent
browser capture described in ml/README.md.

Output: ml/data/miccedu-admission-history.csv and its passport (.passport.json).
The output depends only on the inputs: a repeated run gives the same bytes.

Usage:
    python scripts/build_admission_history.py <capture.jsonl[.gz]> [--check]
"""
import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'backend'/'app'/'data'/'national-catalog.json'
REGISTRY = ROOT/'backend'/'app'/'data'/'accreditation-registry.json'
OUTPUT = ROOT/'ml'/'data'/'miccedu-admission-history.csv'
PASSPORT = OUTPUT.with_suffix('.passport.json')
EDITIONS = tuple(range(2016, 2026))
URL = re.compile(r'https://monitoring\.miccedu\.ru/iam/(\d{4})/_vpo/inst\.php\?id=(\d{1,12})')
SOURCE = 'https://monitoring.miccedu.ru/?m=vpo'
DATA_YEAR_EVIDENCE = ('Edition 2025, institution page: «...заработной плате ... за 2024 год носят закрытый характер, '
                      'показатель «E.5. Заработная плата ППС» не публикуется». Edition E reports year E-1.')
# The 2025 edition was published with update date 03.02.2026 (docs/catalog-coverage.md). Data for the campaign of
# year Y appears in edition Y+1, published in the following year, so a model for campaign T may use Y <= T-2.
PUBLICATION_LAG_YEARS = 2

# Indicator label prefixes (normalised spaces, case-folded) -> column. Labels are matched by text, not by number,
# because numbering is not guaranteed across editions. Unknown labels are counted in the passport.
INDICATORS = (
    ('avg_ege_budget_excl_special', 'средний балл егэ студентов университета, принятых по результатам егэ на обучение по очной форме по программам бакалавриата и специалитета за счет средств соответствующих бюджетов'),
    ('avg_ege_budget', 'средний балл егэ студентов, принятых по результатам егэ на обучение по очной форме по программам бакалавриата и специалитета за счет средств соответствующих бюджетов'),
    ('avg_ege_paid', 'средний балл егэ студентов, принятых по результатам егэ на обучение по очной форме по программам бакалавриата и специалитета с оплатой стоимости затрат'),
    ('avg_min_ege', 'усредненный по реализуемым направлениям (специальностям) минимальный балл егэ студентов, принятых по результатам егэ на обучение по очной форме'),
    ('olympiad_final_stage', 'численность студентов, победителей и призеров заключительного этапа всероссийской олимпиады школьников'),
    ('olympiad_other', 'численность студентов, победителей и призеров олимпиад школьников, принятых на очную форму обучения'),
    ('target_admitted', 'численность студентов, принятых по результатам целевого приема на первый курс на очную форму обучения'),
)
SCORES = ('avg_ege_budget', 'avg_ege_budget_excl_special', 'avg_ege_paid', 'avg_min_ege')
COUNTS = ('olympiad_final_stage', 'olympiad_other', 'target_admitted')
COLUMNS = ('registry_id', 'ogrn', 'region', 'ownership', 'departmental', 'edition', 'admission_year', *SCORES, *COUNTS,
           'source_url', 'page_sha256', 'fetched_at')


class CaptureError(ValueError):
    pass


def norm(text):
    return ' '.join((text or '').replace('\xa0', ' ').split()).casefold().replace('ё', 'е')


def number(text, *, integer):
    value = (text or '').replace('\xa0', '').replace(' ', '').replace(',', '.').strip()
    if value in ('', '-', '–', '—', 'н/д', 'нет'):
        return None
    if not re.fullmatch(r'\d{1,7}(\.\d{1,4})?', value):
        raise CaptureError(f'unexpected value {text!r}')
    parsed = float(value)
    if integer:
        if parsed != int(parsed):
            raise CaptureError(f'fractional count {text!r}')
        return int(parsed)
    if not 0 < parsed <= 100:
        # An average EGE score is between 0 and 100; anything else is a different unit or a parsing error.
        raise CaptureError(f'score out of range {text!r}')
    return round(parsed, 2)


def parse_edu(html):
    """Indicator table -> (values by column, labels that matched nothing)."""
    values, unknown = {}, []
    for row in BeautifulSoup(html, 'html.parser').find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in row.find_all(['td', 'th'], recursive=False)]
        if len(cells) < 4 or not re.fullmatch(r'1\.\d{1,2}', cells[0]):
            continue
        label = norm(cells[1])
        column = next((name for name, prefix in INDICATORS if label.startswith(prefix)), None)
        if column is None:
            unknown.append(cells[0] + ' ' + cells[1][:120])
            continue
        if column in values:
            raise CaptureError(f'indicator appears twice: {column}')
        values[column] = number(cells[3], integer=column in COUNTS)
    return values, unknown


def parse_name(html):
    for row in BeautifulSoup(html, 'html.parser').find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in row.find_all('td', recursive=False)]
        if len(cells) == 2 and norm(cells[0]).startswith('наименование'):
            return ' '.join(cells[1].split())
    return None


def ownership(name):
    text = norm(name)
    if any(k in text for k in ('негосударствен', 'частное', 'частная', 'некоммерческ', 'религиозн', 'духовн', 'профсоюз')):
        return 'non_state'
    if any(k in text for k in ('государственн', 'муниципальн', 'федеральн')):
        return 'state'
    return 'unknown'


def read_capture(path):
    raw = Path(path).read_bytes()
    body = gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw
    records = [json.loads(line) for line in body.decode('utf-8').splitlines() if line.strip()]
    return records, hashlib.sha256(raw).hexdigest()


def reference():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    heads = {r['registryId']: r for r in catalog['institutions'] if not r['isBranch']}
    registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
    by_catalog = {o['catalogMatch']['registryId']: o for o in registry['organisations'] if o['catalogMatch']}
    return heads, by_catalog


def build(records, *, capture_sha256, heads, by_catalog):
    seen, rows, problems = set(), [], Counter()
    unknown_labels, fetched = Counter(), []
    pages = Counter()
    for record in records:
        match = URL.fullmatch(record.get('url', ''))
        key = (record.get('registryId'), record.get('edition'))
        if not match or (match[2], int(match[1])) != key or key[1] not in EDITIONS or key in seen:
            raise CaptureError(f'bad or duplicate capture record {key}')
        seen.add(key)
        if key[0] not in heads:
            raise CaptureError(f'not a head organisation of the catalog: {key[0]}')
        fetched.append(record['fetchedAt'])
        if record.get('status') != 200:
            pages['http_' + str(record.get('status'))] += 1
            continue
        if not re.fullmatch(r'[0-9a-f]{64}', record.get('sha256') or ''):
            raise CaptureError(f'missing page hash {key}')
        if not record.get('info'):
            pages['no_institution_page'] += 1
            continue
        if not record.get('edu'):
            pages['no_indicator_table'] += 1
            continue
        pages['parsed'] += 1
        values, unknown = parse_edu(record['edu'])
        unknown_labels.update(f"{key[1]} {label}" for label in unknown)
        org = by_catalog.get(key[0])
        name = parse_name(record['info']) or heads[key[0]]['name']
        rows.append(dict(
            registry_id=key[0], ogrn=org['ogrn'] if org else '', region=heads[key[0]]['region'], ownership=ownership(name),
            departmental='' if org is None else ('yes' if org['departmental'] else 'no'), edition=key[1], admission_year=key[1] - 1,
            **{c: values.get(c) for c in (*SCORES, *COUNTS)},
            source_url=record['url'], page_sha256=record['sha256'], fetched_at=record['fetchedAt']))
    missing = sorted(set(heads) - {r for r, _ in seen})
    if missing:
        problems['heads_not_captured'] = len(missing)
    rows.sort(key=lambda r: (int(r['registry_id']), r['edition']))
    return rows, dict(pages=dict(sorted(pages.items())), unknownLabels=dict(sorted(unknown_labels.items())),
                      captureSha256=capture_sha256, fetched=(min(fetched), max(fetched)) if fetched else None,
                      notCaptured=missing, problems=dict(problems))


def to_csv(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: '' if row[k] is None else row[k] for k in COLUMNS})
    return out.getvalue().encode('utf-8')


def share(part, total):
    return round(part / total, 4) if total else None


def passport(rows, meta, *, heads):
    total = len(heads)
    by_year = defaultdict(list)
    for row in rows:
        by_year[row['admission_year']].append(row)
    years = []
    for year in sorted(by_year):
        items = by_year[year]
        years.append(dict(admissionYear=year, edition=year + 1, universities=len(items), share=share(len(items), total),
                          **{c: sum(r[c] is not None for r in items) for c in SCORES}))
    series = Counter(sum(1 for r in rows if r['registry_id'] == rid and r['avg_min_ege'] is not None) for rid in heads)
    covered = {r['registry_id'] for r in rows if r['avg_min_ege'] is not None}

    def profile(ids):
        own = Counter(ownership(heads[i]['name']) for i in ids)
        return dict(total=len(ids), **{k: own[k] for k in ('state', 'non_state', 'unknown')})
    latest = max(by_year) if by_year else None
    latest_ids = {r['registry_id'] for r in by_year.get(latest, []) if r['avg_min_ege'] is not None}
    return dict(
        format='admission-history-passport-v1', dataset=str(OUTPUT.relative_to(ROOT)), sourceUrl=SOURCE,
        grain='university x admission year (head organisations of the 2025 monitoring catalog)',
        dataYearRule=dict(rule='admission_year = edition - 1', evidence=DATA_YEAR_EVIDENCE),
        leakageRule=dict(rule=f'for campaign T use only admission_year <= T - {PUBLICATION_LAG_YEARS}',
                         reason='Edition 2025 (admission 2024) was published on 03.02.2026; data of a campaign appears in the next edition, published the year after.'),
        capture=dict(sha256=meta['captureSha256'], fetchedFrom=meta['fetched'][0] if meta['fetched'] else None,
                     fetchedTo=meta['fetched'][1] if meta['fetched'] else None, pages=meta['pages'],
                     notCaptured=len(meta['notCaptured'])),
        headsInCatalog=total, rows=len(rows), years=years,
        universitiesByYearsWithMinScore={str(k): v for k, v in sorted(series.items())},
        groupLevel=dict(usableGroups=0, reason='The monitoring publishes university-level averages only. No source in the project has confirmed '
                                               'competition group cutoffs or last enrolled scores for past campaigns; the 2026 archive lists '
                                               'of 15 groups are lists before enrolment, not outcomes.'),
        bias=dict(
            note='Universities closed or merged before 2025 are absent (survivorship). Departmental, military and law-enforcement '
                 'universities are excluded by the monitoring itself. Non-state universities rarely have budget places, so '
                 'budget averages are missing for them.',
            withMinScoreAnyYear=profile(covered), withoutMinScore=profile(set(heads) - covered),
            latestYear=latest, withMinScoreLatestYear=profile(latest_ids)),
        unknownLabels=meta['unknownLabels'],
    )


def write(capture):
    records, digest = read_capture(capture)
    heads, by_catalog = reference()
    rows, meta = build(records, capture_sha256=digest, heads=heads, by_catalog=by_catalog)
    return to_csv(rows), (json.dumps(passport(rows, meta, heads=heads), ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def training_rows(rows, campaign_year):
    """Rows a model for the campaign of `campaign_year` may see: published before that campaign."""
    if type(campaign_year) is not int:
        raise TypeError('campaign_year must be an int')
    return [r for r in rows if int(r['admission_year']) <= campaign_year - PUBLICATION_LAG_YEARS]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('capture', help='Capture JSON lines, optionally gzip')
    parser.add_argument('--check', action='store_true', help='Fail if the committed dataset differs from a fresh build')
    args = parser.parse_args(argv)
    try:
        data, card = write(args.capture)
    except CaptureError as error:
        print(f'capture rejected: {error}', file=sys.stderr)
        return 1
    if args.check:
        same = OUTPUT.exists() and OUTPUT.read_bytes() == data and PASSPORT.read_bytes() == card
        print('dataset is up to date' if same else 'dataset differs from a fresh build')
        return 0 if same else 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(data)
    PASSPORT.write_bytes(card)
    rows = data.count(b'\n') - 1
    print(f'wrote {OUTPUT.relative_to(ROOT)} ({rows} rows) and the passport')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
