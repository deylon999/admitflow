"""KAN-217: the national denominator comes from the accreditation register and is validated whole."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

from app.accreditation_registry import DEFAULT_PATH, load_registry, parse_registry, summary
from app.national_catalog import load_catalog

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
import build_accreditation_registry as builder  # noqa: E402


def body():
    return DEFAULT_PATH.read_bytes()


def damaged(change):
    data = json.loads(body())
    change(data)
    return json.dumps(data, ensure_ascii=False).encode()


def test_shipped_registry_is_consistent_and_covers_the_catalog():
    registry = load_registry()
    numbers = summary(registry)
    assert registry.dataset_date.isoformat() == '2026-11-10'
    assert numbers['denominator'] == 785 and numbers['civilDenominator'] == 702 and numbers['departmental'] == 83
    assert numbers['catalogMatched'] == 675 and numbers['registryOnly'] == 109
    # KAN-217 target: the reference catalog covers at least 60 % of the national denominator.
    assert numbers['catalogMatched'] / numbers['denominator'] >= 0.6
    domestic = [o for o in registry.organisations if not o.abroad]
    assert len({o.ogrn for o in domestic}) == len(domestic) == registry.denominator
    assert all(not o.name.casefold().startswith('филиал') for o in domestic)


def test_every_catalog_head_is_accounted_for_exactly_once():
    registry = load_registry()
    heads = {r.registry_id for r in load_catalog().institutions if not r.is_branch}
    matched = [o.catalog_registry_id for o in registry.organisations if o.catalog_registry_id]
    ambiguous = [i for v in registry.ambiguous.values() for i in v]
    listed = matched + list(registry.unmatched_catalog_heads) + ambiguous
    assert sorted(listed) == sorted(heads)
    branches = {r.registry_id for r in load_catalog().institutions if r.is_branch}
    assert branches.isdisjoint(listed)


def test_registry_only_records_exclude_matched_ambiguous_and_foreign():
    registry = load_registry()
    only = registry.registry_only
    assert all(o.catalog_registry_id is None and not o.abroad and o.ogrn not in registry.ambiguous for o in only)
    assert len(only) + registry.matched_catalog_heads + len(registry.ambiguous) == registry.denominator


@pytest.mark.parametrize('change', [
    lambda d: d.update(denominator=d['denominator'] + 1),
    lambda d: d.update(format='raoo-heads-v2'),
    lambda d: d.update(catalogEdition=d['catalogEdition'] + 1),
    lambda d: d['organisations'][0].update(ogrn='123'),
    lambda d: d['organisations'][0].update(bachelorPrograms=d['organisations'][0]['bachelorPrograms'] + 1),
    lambda d: d['organisations'][0].update(programCodes=['bad']),
    lambda d: d['organisations'].append(dict(d['organisations'][0])),
    lambda d: d['organisations'][0].update(officialUrl='javascript:alert(1)'),
    lambda d: d.update(unmatchedCatalogHeads=d['unmatchedCatalogHeads'][1:]),
    lambda d: next(o for o in d['organisations'] if o['catalogMatch']).update(catalogMatch=dict(registryId='999999999', method='name')),
])
def test_damaged_registry_is_refused_whole(change):
    with pytest.raises(ValueError):
        parse_registry(damaged(change))


def certificate(ogrn, name, region, status='Действующее', level='Высшее образование - бакалавриат', code='09.03.01', branch=None, site='https://u.example'):
    branch_xml = '' if branch is None else f'<Supplement><StatusName>Действующее</StatusName><IsForBranch>1</IsForBranch><ActualEducationOrganization><Id>b</Id><FullName>Филиал {name}</FullName><OGRN>{ogrn}</OGRN><WebSite/></ActualEducationOrganization><EducationalPrograms><EducationalProgram><EduLevelName>{level}</EduLevelName><ProgrammCode>{branch}</ProgrammCode><IsCanceled/><IsSuspended/></EducationalProgram></EducationalPrograms></Supplement>'
    return (f'<Certificate><Id>c{ogrn}</Id><StatusName>{status}</StatusName><RegionName>{region}</RegionName><RegNumber>1</RegNumber>'
            f'<EduOrgFullName>{name}</EduOrgFullName><EduOrgINN>1234567890</EduOrgINN><EduOrgOGRN>{ogrn}</EduOrgOGRN>'
            f'<ActualEducationOrganization><Id>o{ogrn}</Id><FullName>{name}</FullName><ShortName>U</ShortName><IsBranch>1</IsBranch>'
            f'<OGRN>{ogrn}</OGRN><INN>1234567890</INN><WebSite>{site}</WebSite><RegionName>{region}</RegionName><HeadName>Private Person</HeadName><Phone>+7 000</Phone>'
            f'</ActualEducationOrganization><Supplements><Supplement><StatusName>Действующее</StatusName><IsForBranch/>'
            f'<ActualEducationOrganization><Id>o{ogrn}</Id><FullName>{name}</FullName><OGRN>{ogrn}</OGRN><WebSite>{site}</WebSite></ActualEducationOrganization>'
            f'<EducationalPrograms><EducationalProgram><EduLevelName>{level}</EduLevelName><ProgrammName>P</ProgrammName><ProgrammCode>{code}</ProgrammCode><IsCanceled/><IsSuspended/></EducationalProgram></EducationalPrograms>'
            f'</Supplement>{branch_xml}</Supplements></Certificate>')


def test_builder_counts_legal_entities_once_and_drops_private_fields(tmp_path):
    xml = ('<?xml version="1.0" encoding="UTF-8"?><OpenData><Certificates>'
           + certificate('1000000000001', 'Университет А', 'Тверская область', branch='38.03.01')
           + certificate('1000000000001', 'Университет А', 'Тверская область', code='05.03.01')
           + certificate('1000000000002', 'Университет Б', 'Тверская область', status='Недействующее')
           + certificate('1000000000003', 'Институт В', 'Тверская область', level='Высшее образование - магистратура', code='09.04.01')
           + certificate('1000000000004', 'Университет Г', 'Тверская область', level='Высшее образование - специалитет', code='31.05.01', site='сайт, www.g.example')
           + '</Certificates></OpenData>')
    archive = tmp_path/'data-20261110-structure-20160713.zip'
    with zipfile.ZipFile(archive, 'w') as bundle:
        bundle.writestr('data-20261110-structure-20160713.xml', xml)
    heads, programmes = builder.build_heads(builder.read_register(archive))
    assert [h['ogrn'] for h in heads] == ['1000000000001', '1000000000004']
    first, second = heads
    assert first['programCodes'] == ['05.03.01', '09.03.01', '38.03.01'] and first['branchesWithPrograms'] == 1
    assert (second['specialistPrograms'], second['officialUrl']) == (1, 'http://www.g.example')
    assert 'Private Person' not in json.dumps(heads, ensure_ascii=False) and '+7 000' not in json.dumps(heads)


def test_matching_accepts_only_unique_answers():
    heads = [dict(ogrn='1', names=['ФГБОУ ВО «Тверской университет»'], domains=['tver.example'], region='Тверская область'),
             dict(ogrn='2', names=['ФГБОУ ВО «Тверской технический университет»'], domains=['shared.example'], region='Тверская область'),
             dict(ogrn='3', names=['ЧОУ ВО «Другой институт»'], domains=['shared.example'], region='Тверская область'),
             dict(ogrn='4', names=['ФГБОУ ВО «Орловский университет имени Тургенева»'], domains=[], region='Орловская область')]
    catalog = dict(institutions=[
        dict(registryId='10', name='ФГБОУ ВО «Тверской университет»', officialUrl=None, region='Тверская область', isBranch=False),
        dict(registryId='11', name='Переименованный', officialUrl='https://shared.example', region='Тверская область', isBranch=False),
        dict(registryId='12', name='ФГБОУ ВО «Орловский университет»', officialUrl=None, region='Орловская область', isBranch=False),
        dict(registryId='13', name='Филиал', officialUrl='https://tver.example', region='Тверская область', isBranch=True)])
    matches, unmatched = builder.match_catalog(heads, catalog)
    assert matches == {'1': [('10', 'name')], '4': [('12', 'honorary-name-region')]} and unmatched == ['11']
