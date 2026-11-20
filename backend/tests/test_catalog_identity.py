"""Stable identity contract: no dependence on process, names, mutable facts or URL."""
import os
import subprocess
import sys
from uuid import UUID

import pytest

from app.catalog_identity import campaign_id, competition_group_id, compound_source_key, program_id


def test_frozen_campaign_identity_survives_a_new_python_process():
    expected = campaign_id('sgu-saratov', 2027, 'bachelor')
    assert expected == 'b32e1311-739c-5220-8330-59bc3517829b'
    assert str(UUID(expected)) == expected
    env = {**os.environ, 'PYTHONHASHSEED': '42'}
    actual = subprocess.check_output([sys.executable, '-c',
        "from app.catalog_identity import campaign_id; print(campaign_id('sgu-saratov', 2027, 'bachelor'))"], env=env, text=True)
    assert actual.strip() == expected


def test_campaign_discriminators():
    base = campaign_id('head', 2027, 'bachelor')
    assert len({base, campaign_id('branch', 2027, 'bachelor'), campaign_id('head', 2026, 'bachelor'),
                campaign_id('head', 2027, 'specialist')}) == 4


def test_program_discriminators_and_literal_official_ids():
    args = ['head', 'bachelor', 'campaign-2027', 'admission-system', '001A']
    baseline = program_id(*args)
    for index, changed in enumerate(['branch', 'specialist', 'campaign-2026', 'other-system', '001a']):
        other = args.copy()
        other[index] = changed
        assert program_id(*other) != baseline
    assert program_id(*args[:-1], '1A') != baseline
    assert program_id(*args) == baseline


@pytest.mark.parametrize('field,changed', [('campaign_id', '2026'), ('source_namespace', 'other'),
    ('source_key', '01'), ('study_form', 'part-time'), ('funding', 'paid'),
    ('category', 'special-quota'), ('category', 'separate-quota'), ('category', 'target-quota')])
def test_group_discriminators(field, changed):
    data = dict(campaign_id='2027', source_namespace='official-system', source_key='1',
                study_form='full-time', funding='budget', category='general')
    baseline = competition_group_id(**data)
    data[field] = changed
    assert competition_group_id(**data) != baseline


def test_compound_identity_is_sorted_unambiguous_and_rejects_names():
    first = compound_source_key({'profile_id': 'A', 'code': '09.03.04'})
    assert first == compound_source_key({'code': '09.03.04', 'profile_id': 'A'})
    assert first != compound_source_key({'code': '09.03.04', 'profile_id': 'B'})
    for value in ({}, {'name': 'Same title'}, {'code': None}, {'profile_id': ' A'}):
        with pytest.raises(ValueError):
            compound_source_key(value)
    assert compound_source_key({'official_id': 'a:b', 'profile_id': 'c'}) != compound_source_key({'official_id': 'a', 'profile_id': 'b:c'})


@pytest.mark.parametrize('year', [None, True, 2027.0, '2027', 1999, 2101])
def test_invalid_year_refused(year):
    with pytest.raises(ValueError):
        campaign_id('head', year, 'bachelor')


@pytest.mark.parametrize('value', [None, '', ' ', ' A', 'A ', 'A\nB', 'A\x00B', 'A\x7fB', 1, 'x' * 301])
def test_missing_or_invalid_source_key_refused(value):
    with pytest.raises(ValueError):
        program_id('head', 'bachelor', '2027', 'official-system', value)


@pytest.mark.parametrize('field', ['study_form', 'funding', 'category'])
def test_unknown_conditions_do_not_create_a_group(field):
    data = dict(campaign_id='2027', source_namespace='official-system', source_key='1',
                study_form='full-time', funding='budget', category='general')
    data[field] = None
    with pytest.raises(ValueError):
        competition_group_id(**data)


@pytest.mark.parametrize('level', ['master', 'unknown', None, []])
def test_unsupported_levels_refused(level):
    with pytest.raises(ValueError):
        campaign_id('head', 2027, level)
