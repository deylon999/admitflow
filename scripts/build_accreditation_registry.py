#!/usr/bin/env python3
"""Build the national denominator of higher-education organisations (KAN-217).

Input is the official Rosobrnadzor open data set 7701537808-RAOO, the state
accreditation register, downloaded as a ZIP from
https://isga.obrnadzor.gov.ru/accredreestr/opendata/ (about 350 MB, updated daily).
The archive is not committed: the output records its SHA-256 and date.

Denominator: legal entities (unique OGRN) located in Russia whose certificate
is active and has an active supplement with at least one active bachelor or
specialist programme. Branches share the OGRN of their parent, so they are
counted once and only reported as a number. Head names, phones, e-mails and
addresses are never read into the output.

The MICCEDU monitoring catalog is matched to the register by exact full name,
then by unique website domain, then by the quoted core name within one
region. Anything else stays unmatched and is listed in the report.
"""
import argparse
import collections
import difflib
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'backend/app/data/national-catalog.json'
OUTPUT = ROOT / 'backend/app/data/accreditation-registry.json'
DATASET_URL = 'https://isga.obrnadzor.gov.ru/accredreestr/opendata/'
ABROAD = 'образовательные учреждения, находящиеся за пределами российской федерации'
LEVELS = {'бакалав': 'bachelor', 'специалит': 'specialist'}
CODE = re.compile(r'^\d{2}\.\d{2}\.\d{2}$')
# Admission to these organisations goes through departmental selection, not the
# general lists. Name-based and reported as a subset only; never excluded.
DEPARTMENTAL = re.compile(r'военн|министерства обороны|внутренних дел|мвд|федеральной службы безопасности|пограничн|'
                          r'исполнения наказаний|чрезвычайным ситуациям|противопожарн|национальной гвардии|'
                          r'федеральной службы охраны|следственного комитета|прокуратуры|береговой охраны|внешней разведки')


def text(element, tag):
    value = element.findtext(tag)
    return value.strip() if value and value.strip() else None


def norm(value):
    value = (value or '').lower().replace('ё', 'е')
    value = re.sub(r'[«»"“”„\'`]', ' ', value)
    return ' '.join(re.sub(r'[^0-9a-zа-я]+', ' ', value).split())


def core(value):
    """Quoted part of an official name: «Х», "Х"; falls back to the whole name."""
    found = re.findall(r'[«"“]([^«»"“”]{3,})[»"”]', value or '')
    return norm(max(found, key=len)) if found else norm(value)


def region_key(value):
    value = norm(value).replace('республика ', '').replace('г ', '')
    return re.sub(r'\s*\(.*', '', value).split(' ')[0] if value else ''


def domain(url):
    if not url:
        return None
    url = url.strip()
    try:
        host = (urlsplit(url if '://' in url else 'http://' + url).hostname or '').lower()
    except ValueError:
        return None
    host = host[4:] if host.startswith('www.') else host
    return host or None


def official_site(url):
    """First well-formed http(s) address of a free-text register field, else None."""
    for token in re.split(r'[\s,;]+', (url or '').strip()):
        token = token.strip('.,;()<>«»"\'')
        if not token:
            continue
        candidate = token if token.startswith(('http://', 'https://')) else 'http://' + token
        try:
            parts = urlsplit(candidate)
            parts.port
        except ValueError:
            continue
        host = parts.hostname or ''
        if '.' in host and not parts.username and not parts.password and len(candidate) <= 2048 and re.fullmatch(r'[0-9a-zа-яё.\-]+', host):
            return candidate
    return None


def level_of(name):
    lowered = (name or '').lower()
    return next((value for key, value in LEVELS.items() if key in lowered), None)


def organisation(element):
    if element is None:
        return None
    return {key: text(element, key) for key in ('Id', 'FullName', 'ShortName', 'IsBranch', 'HeadEduOrgId', 'OGRN', 'INN', 'KPP', 'WebSite', 'RegionName')}


def read_register(archive):
    """Yield active certificates with bachelor/specialist programmes, streaming the XML."""
    with zipfile.ZipFile(archive) as bundle:
        members = [name for name in bundle.namelist() if name.endswith('.xml')]
        if len(members) != 1:
            raise SystemExit('expected exactly one XML file in the archive')
        with bundle.open(members[0]) as stream:
            for _, element in ET.iterparse(stream, events=('end',)):
                if element.tag != 'Certificate':
                    continue
                if text(element, 'StatusName') == 'Действующее':
                    supplements = []
                    for supplement in element.iterfind('Supplements/Supplement'):
                        if text(supplement, 'StatusName') != 'Действующее':
                            continue
                        codes = {}
                        for program in supplement.iterfind('EducationalPrograms/EducationalProgram'):
                            level = level_of(text(program, 'EduLevelName'))
                            flags = [(text(program, key) or '').lower() in ('1', 'true') for key in ('IsCanceled', 'IsSuspended')]
                            code = text(program, 'ProgrammCode')
                            if level and not any(flags) and code and CODE.match(code):
                                codes[code] = (level, text(program, 'ProgrammName'))
                        if codes:
                            supplements.append(dict(org=organisation(supplement.find('ActualEducationOrganization')),
                                                    forBranch=text(supplement, 'IsForBranch') == '1', codes=codes))
                    if supplements:
                        yield dict(id=text(element, 'Id'), regNumber=text(element, 'RegNumber'), issueDate=text(element, 'IssueDate'),
                                   region=text(element, 'RegionName'), ogrn=text(element, 'EduOrgOGRN'), inn=text(element, 'EduOrgINN'),
                                   fullName=text(element, 'EduOrgFullName'), org=organisation(element.find('ActualEducationOrganization')),
                                   supplements=supplements)
                element.clear()


def is_branch_org(org):
    # IsBranch and HeadEduOrgId are set on a few head organisations after reorganisation
    # (for example 1025401932753). A certificate belongs to a legal entity, so only the name decides.
    return bool(org) and norm(org.get('FullName')).startswith('филиал')


def build_heads(certificates):
    by_ogrn = collections.defaultdict(list)
    for certificate in certificates:
        ogrn = (certificate['org'] or {}).get('OGRN') or certificate['ogrn']
        if ogrn and re.fullmatch(r'\d{13}', ogrn):
            by_ogrn[ogrn].append(certificate)
        elif ogrn and norm(certificate['region']) == norm(ABROAD):
            # Foreign registration numbers are not OGRN; keep them listed as abroad.
            by_ogrn['foreign:' + ogrn].append(certificate)
    heads, programmes = [], {}
    for ogrn, group in sorted(by_ogrn.items()):
        head_orgs = [c['org'] for c in group if c['org'] and not is_branch_org(c['org'])]
        head_orgs += [s['org'] for c in group for s in c['supplements'] if s['org'] and not s['forBranch'] and not is_branch_org(s['org'])]
        main = next((o for o in head_orgs if o.get('FullName')), None) or group[0]['org'] or {}
        certificate = next((c for c in group if c['org'] and not is_branch_org(c['org'])), group[0])
        branches, codes = set(), {}
        for c in group:
            for supplement in c['supplements']:
                org = supplement['org'] or {}
                if supplement['forBranch'] or is_branch_org(org):
                    branches.add(org.get('Id') or org.get('FullName'))
                for code, (level, name) in supplement['codes'].items():
                    codes[code] = level
                    if name:
                        programmes.setdefault(code, [level, name])
        region = main.get('RegionName') or certificate['region']
        name = main.get('FullName') or certificate['fullName']
        heads.append(dict(
            ogrn=ogrn, inn=main.get('INN') or certificate['inn'], name=name, shortName=main.get('ShortName'),
            region=region,
            # A Russian OGRN means a Russian legal entity even when the register files it under the
            # foreign region label (1239000004572, Azov pedagogical university). Foreign numbers mark abroad.
            abroad=ogrn.startswith('foreign:'),
            departmental=bool(DEPARTMENTAL.search(norm(name))), officialUrl=official_site(main.get('WebSite')),
            certificate=dict(id=certificate['id'], regNumber=certificate['regNumber'], issueDate=certificate['issueDate']),
            branchesWithPrograms=len(branches), bachelorPrograms=sum(v == 'bachelor' for v in codes.values()),
            specialistPrograms=sum(v == 'specialist' for v in codes.values()), programCodes=sorted(codes),
            names=sorted({o.get('FullName') for o in head_orgs if o.get('FullName')} | {c['fullName'] for c in group if c['fullName']}),
            domains=sorted({d for o in head_orgs for d in [domain(o.get('WebSite'))] if d})))
    return heads, programmes


def similar(left, right):
    return difflib.SequenceMatcher(None, left, right).ratio()


def match_catalog(heads, catalog):
    """MICCEDU head -> OGRN. Only unique answers are accepted at each step."""
    by_name, by_domain, by_core = (collections.defaultdict(set) for _ in range(3))
    for head in heads:
        for name in head['names']:
            by_name[norm(name)].add(head['ogrn'])
            by_core[(core(name), region_key(head['region']))].add(head['ogrn'])
        for value in head['domains']:
            by_domain[value].add(head['ogrn'])
    matches, unmatched = {}, []
    for row in catalog['institutions']:
        if row['isBranch']:
            continue
        steps = (('name', by_name.get(norm(row['name']))), ('domain', by_domain.get(domain(row['officialUrl'])) if row['officialUrl'] else None),
                 ('core-region', by_core.get((core(row['name']), region_key(row['region'])))))
        found = next(((method, next(iter(hit))) for method, hit in steps if hit and len(hit) == 1), None)
        if not found:
            # Honorary names are appended on renaming: «X» -> «X имени Y».
            key = core(row['name'])
            prefixed = {head['ogrn'] for head in heads if region_key(head['region']) == region_key(row['region'])
                        and len(key) >= 15 and any(core(name).startswith(key + ' имени') for name in head['names'])}
            if len(prefixed) == 1:
                found = ('honorary-name-region', next(iter(prefixed)))
        if not found:
            # Renamed organisations: one clearly best quoted name in the same region.
            scored = sorted(((max(similar(core(row['name']), core(name)) for name in head['names']), head['ogrn'])
                             for head in heads if region_key(head['region']) == region_key(row['region'])), reverse=True)
            if scored and scored[0][0] >= 0.75 and (len(scored) == 1 or scored[0][0] - scored[1][0] >= 0.15):
                found = ('fuzzy-region', scored[0][1])
        if found:
            matches.setdefault(found[1], []).append((row['registryId'], found[0]))
        else:
            unmatched.append(row['registryId'])
    return matches, unmatched


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('archive', type=Path, help='data-YYYYMMDD-structure-20160713.zip from the RAOO open data page')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    stamp = re.search(r'data-(\d{8})-structure', args.archive.name)
    if not stamp:
        raise SystemExit('archive name must keep the official data-YYYYMMDD-structure-*.zip form')
    dataset_date = datetime.strptime(stamp[1], '%Y%m%d').date()
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    heads, programmes = build_heads(read_register(args.archive))
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    matches, unmatched = match_catalog(heads, catalog)
    duplicates = {ogrn: rows for ogrn, rows in matches.items() if len(rows) > 1}
    for head in heads:
        rows = matches.get(head['ogrn'], [])
        head['catalogMatch'] = None if len(rows) != 1 else dict(registryId=rows[0][0], method=rows[0][1])
        del head['names'], head['domains']
    domestic = [h for h in heads if not h['abroad']]
    output = dict(
        format='raoo-heads-v1', datasetId='7701537808-RAOO', sourceUrl=DATASET_URL, datasetDate=dataset_date.isoformat(),
        archiveSha256=digest, builtAt=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        catalogEdition=catalog['edition'],
        rule=('Unique OGRN with an active certificate and an active supplement containing an active bachelor or specialist '
              'programme. Branches are counted with their parent. Organisations registered abroad (no Russian OGRN) are listed but excluded.'),
        denominator=len(domestic), abroad=len(heads) - len(domestic), departmental=sum(h['departmental'] for h in domestic),
        catalogHeads=sum(not r['isBranch'] for r in catalog['institutions']),
        matchedCatalogHeads=sum(1 for h in domestic if h['catalogMatch']),
        matchMethods=dict(collections.Counter(h['catalogMatch']['method'] for h in domestic if h['catalogMatch'])),
        unmatchedCatalogHeads=sorted(unmatched, key=int),
        ambiguousCatalogMatches={ogrn: sorted(r[0] for r in rows) for ogrn, rows in sorted(duplicates.items())},
        programmes={code: programmes[code] for code in sorted(programmes)},
        organisations=heads)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    summary = {key: output[key] for key in ('datasetDate', 'denominator', 'abroad', 'departmental', 'catalogHeads', 'matchedCatalogHeads', 'matchMethods')}
    summary.update(unmatchedCatalogHeads=len(unmatched), ambiguous=len(duplicates), programmes=len(programmes))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
