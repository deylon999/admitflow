"""Operator-reviewed exact URLs for programme research and publication."""
from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from app.catalog.national_catalog import load_catalog
from app.catalog.program_catalog_review import load_reviews
from app.sources.fetcher import valid_domains


@dataclass(frozen=True)
class ProgrammeSource:
    key: str
    university_id: str
    year: int
    url: str
    review: dict | None = None

    @property
    def host(self):
        return urlsplit(self.url).hostname


# Discovery is an operator decision. No links are followed from downloaded HTML.
# Candidates can be captured for review but are never eligible for publication.
CANDIDATES = (
    ProgrammeSource('sfu-admission-2027', 'miccedu-1507', 2027,
                    'https://sfu.ru/ru/admission/bachelor/exams-destinations?tab=e9253131d1a508'),
    ProgrammeSource('rudn-admission-2027', 'miccedu-222', 2027,
                    'https://admission.rudn.ru/undergraduate/way/'),
    ProgrammeSource('itmo-announcements-2027', 'miccedu-234', 2027,
                    'https://news.itmo.ru/ru/news/15087/'),
)


def load_sources():
    reviews = tuple(ProgrammeSource(r['key'], r['university_id'], r['year'], r['url'], r)
                    for r in load_reviews())
    sources = reviews + CANDIDATES
    known_heads = {row.id for row in load_catalog().institutions if not row.is_branch}
    if len({source.key for source in sources}) != len(sources):
        raise ValueError('catalog_duplicate_source_key')
    for source in sources:
        url = urlsplit(source.url)
        if (not re.fullmatch(r'[a-z0-9-]{1,80}', source.key) or source.university_id not in known_heads
                or type(source.year) is not int or not 2000 <= source.year <= 2100
                or url.scheme != 'https' or not valid_domains(frozenset({url.hostname}))
                or url.port is not None or url.username or url.password or url.fragment or not url.path
                or (source.review is not None and source.review['final_url'] != source.url)):
            raise ValueError('catalog_invalid_source_registry')
    return tuple(sorted(sources, key=lambda source: source.key))


def select_sources(year, keys=None):
    sources = [source for source in load_sources() if source.year == year]
    if keys is not None:
        if len(keys) != len(set(keys)) or not set(keys) <= {source.key for source in sources}:
            raise ValueError('catalog_unknown_source_for_year')
        sources = [source for source in sources if source.key in keys]
    if not sources:
        raise ValueError('catalog_empty_source_batch')
    return sources
