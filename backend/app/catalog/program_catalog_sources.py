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
    content_type: str = 'text/html'

    @property
    def host(self):
        return urlsplit(self.url).hostname


@dataclass(frozen=True)
class SourceObservation:
    key: str
    fetched_at: str
    sha256: str
    status: str
    note: str


OBSERVATIONS = (
    SourceObservation('itmo-announcements-2027', '2026-11-22T17:27:37.389475+00:00',
        'c04beda726b7a265251ec7356878481ed66b0378a01f27632160852e89957c75',
        'programme_scope_unconfirmed', 'Календарь дней открытых дверей 2026 года для будущих абитуриентов.'),
    SourceObservation('rudn-admission-2027', '2026-11-22T17:27:40.759420+00:00',
        '1c02f4e256749831ce681e37656c733c88df4885b19df4362f3d5705d2c5e8b8',
        'campaign_unconfirmed', 'Страница этапов содержит материалы приёма 2026 года и общие инструкции.'),
    SourceObservation('sfu-admission-2027', '2026-11-22T17:27:45.016217+00:00',
        '241ba0731d683cfb3974fed797240f93258508b8aae4ebe221120188c55c88c9',
        'publication_pending', 'Страница обещает сведения для поступающих до 20.01.2027 и ссылается на проект перечня испытаний.'),
)


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
    reviews = tuple(ProgrammeSource(r['key'], r['university_id'], r['year'], r['url'], r, r['content_type'])
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
                or source.content_type not in {'text/html', 'application/pdf'}
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
