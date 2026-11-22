"""Versioned keys for reviewed catalog identities, never evidence of verification.

Existing database IDs always win over calculated IDs. Callers must resolve the
stored natural identity first and quarantine incompatible attributes. Names,
URLs, parser versions and mutable facts must not be used as identity keys.
"""
import json
import re
from uuid import UUID, uuid5


# Frozen namespace: changing this or the canonical payload requires a new version.
NAMESPACE_V1 = UUID('b06035cb-13c1-59f6-84e2-96f183a81321')
LEVELS = frozenset({'bachelor', 'specialist'})


def identity_text(value, maximum):
    """Preserve case/leading zeroes; reject ambiguous trimming and control chars."""
    if (not isinstance(value, str) or not 1 <= len(value) <= maximum
            or value != value.strip() or re.search(r'[\x00-\x1f\x7f]', value)):
        raise ValueError('invalid_catalog_identity')
    return value


def _level(value):
    if not isinstance(value, str) or value not in LEVELS:
        raise ValueError('invalid_catalog_level')
    return value


def _key(kind, *parts):
    payload = json.dumps(['admitflow-catalog-v1', kind, *parts], ensure_ascii=False, separators=(',', ':'))
    return str(uuid5(NAMESPACE_V1, payload))


def campaign_id(university_id, year, level):
    if type(year) is not int or not 2000 <= year <= 2100:
        raise ValueError('invalid_catalog_year')
    return _key('campaign', identity_text(university_id, 80), year, _level(level))


def program_id(university_id, level, origin_campaign_id, source_namespace, source_key):
    """Conservative campaign-scoped identity; cross-year matching is explicit.

    source_key is a reviewed official ID or an unambiguous compound key.
    Reuse this stored Program for another campaign only after reviewing official
    continuity; a new year's repeated number is insufficient on its own.
    """
    return _key('program', identity_text(university_id, 80), _level(level),
                identity_text(origin_campaign_id, 36), identity_text(source_namespace, 160),
                identity_text(source_key, 300))


def competition_group_id(campaign_id, source_namespace, source_key, *, study_form, funding, category):
    """All discriminators must be confirmed; None never creates a placeholder group."""
    return _key('competition-group', identity_text(campaign_id, 36),
                identity_text(source_namespace, 160), identity_text(source_key, 300),
                identity_text(study_form, 40), identity_text(funding, 40), identity_text(category, 80))


def compound_source_key(attributes):
    """Canonical fallback from reviewed distinguishing attributes, never names.

    A family adapter is responsible for proving uniqueness in the official
    document. This function only rejects unsafe inputs and ambiguous encoding.
    """
    allowed = {'code', 'profile_id', 'campus_id', 'curriculum_id', 'official_id'}
    if (not isinstance(attributes, dict) or not attributes
            or any(not isinstance(k, str) or k not in allowed for k in attributes)):
        raise ValueError('ambiguous_catalog_identity')
    pairs = [[k, identity_text(v, 160)] for k, v in sorted(attributes.items())]
    return identity_text(json.dumps(pairs, ensure_ascii=False, separators=(',', ':')), 300)
