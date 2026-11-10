"""National denominator from the Rosobrnadzor accreditation register (KAN-217).

The artifact is built by scripts/build_accreditation_registry.py from open data
set 7701537808-RAOO. It holds organisation-level public facts only: OGRN, INN,
names, region, website, certificate number and counts of accredited bachelor
and specialist programmes. The whole file is validated before use; a damaged
artifact is never partly trusted.
"""
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from types import MappingProxyType

from .national_catalog import clean_text, load_catalog, valid_url

DEFAULT_PATH = Path(__file__).with_name('data')/'accreditation-registry.json'
SOURCE_URL = 'https://isga.obrnadzor.gov.ru/accredreestr/opendata/'
MATCH_METHODS = frozenset({'name', 'domain', 'core-region', 'honorary-name-region', 'fuzzy-region'})
CODE = re.compile(r'\d{2}\.\d{2}\.\d{2}')


@dataclass(frozen=True)
class Organisation:
    ogrn: str
    inn: str | None
    name: str
    short_name: str | None
    region: str | None
    abroad: bool
    departmental: bool
    official_url: str | None
    certificate_number: str | None
    branches_with_programs: int
    bachelor_programs: int
    specialist_programs: int
    catalog_registry_id: str | None
    match_method: str | None

    @property
    def id(self):
        return 'raoo-' + self.ogrn


@dataclass(frozen=True)
class Registry:
    organisations: tuple[Organisation, ...]
    dataset_date: date
    built_at: datetime
    archive_sha256: str
    sha256: str
    denominator: int
    departmental: int
    matched_catalog_heads: int
    unmatched_catalog_heads: tuple[str, ...]
    ambiguous: MappingProxyType
    catalog_edition: int

    @property
    def by_catalog_id(self):
        return {o.catalog_registry_id: o for o in self.organisations if o.catalog_registry_id}

    @property
    def registry_only(self):
        """Domestic organisations absent from the monitoring catalog, without ambiguous duplicates."""
        return tuple(o for o in self.organisations if not o.abroad and o.catalog_registry_id is None and o.ogrn not in self.ambiguous)


def _optional_text(value, maximum):
    return None if value is None else clean_text(value, maximum)


def _count(value):
    if type(value) is not int or not 0 <= value <= 100000:
        raise ValueError('invalid count')
    return value


def parse_registry(body, *, catalog=None):
    if not isinstance(body, bytes) or not 1 <= len(body) <= 8*1024*1024:
        raise ValueError('invalid registry size')
    catalog = catalog or load_catalog()
    try:
        data = json.loads(body.decode('utf-8'))
        if data['format'] != 'raoo-heads-v1' or data['datasetId'] != '7701537808-RAOO' or data['sourceUrl'] != SOURCE_URL:
            raise ValueError('unsupported registry')
        if not re.fullmatch(r'[a-f0-9]{64}', data['archiveSha256']):
            raise ValueError('invalid archive hash')
        dataset_date = date.fromisoformat(data['datasetDate'])
        built = datetime.fromisoformat(data['builtAt'])
        if built.tzinfo is None or built.date() < dataset_date:
            raise ValueError('invalid build time')
        heads = {r.registry_id for r in catalog.institutions if not r.is_branch}
        if data['catalogEdition'] != catalog.edition or data['catalogHeads'] != len(heads):
            raise ValueError('registry was built for another catalog edition')
        organisations, seen, matched = [], set(), set()
        for row in data['organisations']:
            ogrn = row['ogrn']
            foreign = isinstance(ogrn, str) and ogrn.startswith('foreign:')
            if not isinstance(ogrn, str) or not (re.fullmatch(r'\d{13}', ogrn) or (foreign and row['abroad'] is True)) or ogrn in seen:
                raise ValueError('invalid OGRN')
            seen.add(ogrn)
            if row['inn'] is not None and not re.fullmatch(r'\d{10}', row['inn']) and not foreign:
                raise ValueError('invalid INN')
            if type(row['abroad']) is not bool or type(row['departmental']) is not bool:
                raise ValueError('invalid flag')
            codes = row['programCodes']
            if not isinstance(codes, list) or codes != sorted(set(codes)) or not all(isinstance(c, str) and CODE.fullmatch(c) for c in codes):
                raise ValueError('invalid programme codes')
            bachelor, specialist = _count(row['bachelorPrograms']), _count(row['specialistPrograms'])
            if bachelor + specialist != len(codes) or not codes:
                raise ValueError('inconsistent programme counts')
            match = row['catalogMatch']
            registry_id = method = None
            if match is not None:
                registry_id, method = match['registryId'], match['method']
                if registry_id not in heads or method not in MATCH_METHODS or registry_id in matched:
                    raise ValueError('invalid catalog match')
                matched.add(registry_id)
            certificate = row['certificate']
            organisations.append(Organisation(
                ogrn=ogrn, inn=row['inn'], name=clean_text(row['name'], 1500), short_name=_optional_text(row['shortName'], 600),
                region=_optional_text(row['region'], 200), abroad=row['abroad'], departmental=row['departmental'],
                official_url=valid_url(row['officialUrl']) if row['officialUrl'] is not None else None,
                certificate_number=_optional_text(certificate['regNumber'], 80), branches_with_programs=_count(row['branchesWithPrograms']),
                bachelor_programs=bachelor, specialist_programs=specialist, catalog_registry_id=registry_id, match_method=method))
        domestic = [o for o in organisations if not o.abroad]
        if not domestic or data['denominator'] != len(domestic) or data['abroad'] != len(organisations) - len(domestic):
            raise ValueError('inconsistent denominator')
        matched_domestic = sum(1 for o in domestic if o.catalog_registry_id)
        if data['departmental'] != sum(o.departmental for o in domestic) or data['matchedCatalogHeads'] != matched_domestic:
            raise ValueError('inconsistent summary')
        unmatched = tuple(data['unmatchedCatalogHeads'])
        ambiguous = {k: tuple(v) for k, v in data['ambiguousCatalogMatches'].items()}
        listed = set(unmatched) | {i for v in ambiguous.values() for i in v}
        if not listed.isdisjoint(matched) or not listed <= heads or any(k not in seen for k in ambiguous):
            raise ValueError('inconsistent unmatched list')
        if len(matched) + len(set(unmatched)) + len({i for v in ambiguous.values() for i in v}) != len(heads):
            raise ValueError('every catalog head must be matched, unmatched or ambiguous')
        return Registry(tuple(organisations), dataset_date, built, data['archiveSha256'], hashlib.sha256(body).hexdigest(),
                        len(domestic), data['departmental'], matched_domestic, unmatched, MappingProxyType(ambiguous), data['catalogEdition'])
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid accreditation registry') from error


@lru_cache(maxsize=1)
def load_registry():
    return parse_registry(DEFAULT_PATH.read_bytes())


def summary(registry=None):
    """Coverage of the reference catalog against the national denominator."""
    registry = registry or load_registry()
    domestic = [o for o in registry.organisations if not o.abroad]
    civil = [o for o in domestic if not o.departmental]
    return dict(datasetDate=registry.dataset_date.isoformat(), sourceUrl=SOURCE_URL, archiveSha256=registry.archive_sha256,
                denominator=registry.denominator, departmental=registry.departmental, civilDenominator=len(civil),
                catalogMatched=registry.matched_catalog_heads, civilCatalogMatched=sum(1 for o in civil if o.catalog_registry_id),
                registryOnly=len(registry.registry_only), unmatchedCatalogHeads=len(registry.unmatched_catalog_heads),
                ambiguousCatalogHeads=sum(len(v) for v in registry.ambiguous.values()))
