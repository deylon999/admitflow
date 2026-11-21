"""Offline, conservative display names. No HTTP, DB mutation or invented aliases.

The legal name/branch flag belong to the source snapshot. Reviewed overrides are
independent of imports and bound to that exact identity; a renamed organisation
falls back until its override is reviewed again.
"""
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
import re

from app.catalog.national_catalog import clean_text, valid_url

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'university-names.json'
RULE_VERSION = 'legal-prefix-v1'
# Complete, anchored constructions only. Never remove words inside a name.
LEGAL_PREFIXES = (
    'федеральное государственное бюджетное образовательное учреждение высшего образования',
    'федеральное государственное автономное образовательное учреждение высшего образования',
    'федеральное государственное казенное образовательное учреждение высшего образования',
    'федеральное государственное казённое образовательное учреждение высшего образования',
    'государственное бюджетное образовательное учреждение высшего образования',
    'государственное автономное образовательное учреждение высшего образования',
    'автономная некоммерческая организация высшего образования',
    'автономная некоммерческая образовательная организация высшего образования',
    'частное образовательное учреждение высшего образования',
    'образовательное частное учреждение высшего образования',
    'негосударственное образовательное частное учреждение высшего образования',
    'негосударственное частное образовательное учреждение высшего образования',
)
QUOTES = {'"': '"', '«': '»', '„': '“', '“': '”'}


def identity(value):
    """Comparison only: case, whitespace and typographic quotes; not fuzzy matching."""
    return ' '.join(value.translate(str.maketrans('«»„“”', '"""""')).casefold().split())


def usable_short(value):
    if not value or len(re.findall(r'[A-Za-zА-Яа-яЁё]', value)) < 3:
        return False
    return identity(value).strip(' .-') not in {'нет', 'отсутствует', 'не имеется', 'не предусмотрено', 'не указано'}


def normalize_legal_name(full_name, *, is_branch):
    """Remove one known wrapper, preserving every identifying word, or abstain."""
    if is_branch or re.search(r'филиал|представительств', full_name, re.I):
        return None
    value = ' '.join(full_name.split())
    for prefix in LEGAL_PREFIXES:
        if not value.casefold().startswith(prefix + ' '):
            continue
        rest = value[len(prefix):].strip()
        # Strip a single enclosing pair only; no extraction of arbitrary quotes.
        if rest[:1] in QUOTES:
            if not rest.endswith(QUOTES[rest[0]]):
                return None
            inner = rest[1:-1]
            if any(char in inner for char in QUOTES) or '»' in inner or '”' in inner:
                return None
            rest = inner
        elif any(char in rest for char in ('"', '«', '»', '„', '“', '”')):
            return None
        # Require an institution noun and meaningful remaining text. A legal
        # phrase without an actual name is not a university's display name.
        if len(rest) < 10 or not re.search(r'\b(университет|институт|академия|школа|консерватория)\b', rest, re.I):
            return None
        return rest
    return None


@dataclass(frozen=True)
class NameChoice:
    value: str
    kind: str
    source_url: str
    verified_at: datetime
    source_sha256: str
    rule_version: str | None = None
    aliases: tuple[str, ...] = ()
    parent_name: str | None = None
    city: str | None = None
    branch_source_url: str | None = None
    branch_verified_at: datetime | None = None
    branch_source_sha256: str | None = None


def parse_reviews(body):
    """Validate the complete overlay, including unpublished candidates, up front."""
    data = json.loads(body)
    if data['format'] != 'university-names-v1' or not isinstance(data['records'], list):
        raise ValueError('invalid name review format')
    result = {}
    for item in data['records']:
        key = clean_text(item['id'], 80)
        if key in result or item['status'] not in ('verified', 'candidate') or item['kind'] not in ('official', 'manual'):
            raise ValueError('invalid or duplicate name review')
        clean_text(item['fullName'], 1500)
        if type(item['isBranch']) is not bool:
            raise ValueError('invalid branch flag')
        clean_text(item['displayName'], 600)
        if not usable_short(item['displayName']):
            raise ValueError('invalid display name')
        source = item['source']
        valid_url(source['url'])
        if datetime.fromisoformat(source['verifiedAt']).tzinfo is None or not re.fullmatch(r'[a-f0-9]{64}', source['sha256']):
            raise ValueError('invalid name provenance')
        if not isinstance(item['aliases'], list) or any(not usable_short(clean_text(alias, 600)) for alias in item['aliases']):
            raise ValueError('invalid aliases')
        for field in ('parentUniversityName', 'city'):
            if item[field] is not None:
                clean_text(item[field], 1500 if field == 'parentUniversityName' else 120)
                if not item['isBranch']:
                    raise ValueError('branch facts on a head organisation')
        if item['isBranch'] and not re.search('филиал', item['displayName'], re.I) and not item['parentUniversityName']:
            raise ValueError('branch name requires explicit branch identity')
        result[key] = item
    return result


@lru_cache(maxsize=1)
def load_reviews():
    return parse_reviews(DEFAULT_PATH.read_text(encoding='utf-8'))


def choose_name(*, identifier, full_name, is_branch, provenance, source_sha256, registry_org=None, registry=None, reviews=None):
    reviews = load_reviews() if reviews is None else reviews
    review = reviews.get(identifier)
    # Byte-exact original + explicit branch flag: no stale/manual/fuzzy join.
    if review and (review['status'] != 'verified' or review['fullName'] != full_name or review['isBranch'] != is_branch):
        review = None
    official = None
    if review and review['kind'] == 'official':
        official = review
    if official:
        source = official['source']
        choice = NameChoice(official['displayName'], 'official', source['url'], datetime.fromisoformat(source['verifiedAt']),
                            source['sha256'], aliases=tuple(official['aliases']))
    elif (not is_branch and registry_org and registry and identity(full_name) == identity(registry_org.name)
          and usable_short(registry_org.short_name)):
        from app.catalog.accreditation_registry import SOURCE_URL
        choice = NameChoice(registry_org.short_name.strip(), 'official', SOURCE_URL,
                            registry.built_at, registry.archive_sha256)
    elif (normalized := normalize_legal_name(full_name, is_branch=is_branch)):
        choice = NameChoice(normalized, 'normalized', provenance.url, provenance.verified_at, source_sha256, RULE_VERSION)
    elif review:
        source = review['source']
        choice = NameChoice(review['displayName'], 'manual', source['url'], datetime.fromisoformat(source['verifiedAt']),
                            source['sha256'], aliases=tuple(review['aliases']))
    else:
        choice = NameChoice(full_name, 'original', provenance.url, provenance.verified_at, source_sha256)
    if review and is_branch:
        from dataclasses import replace
        source = review['source']
        choice = replace(choice, parent_name=review['parentUniversityName'], city=review['city'],
                         branch_source_url=source['url'], branch_verified_at=datetime.fromisoformat(source['verifiedAt']),
                         branch_source_sha256=source['sha256'])
    return choice
