"""Reviewed JSON and CSV list decoders behind the same Adapter interface as HTML (KAN-220).

A profile describes one reviewed official list: where the records are, which
field holds rank, public code, score, consent, priority and status, and how many
rows the source declares. Decoding is strict in the same way as the HTML table
family: rows must follow the official order 1..N, codes are hashed into
scoped keys immediately, and anything unexpected fails the whole list with
the stable code invalid_format. Nothing is attested here: a profile only
reaches the runtime registry with an Attestation from the reviewed source.
"""
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import io
import json
import re
from urllib.parse import urlsplit

from .contracts import AdapterError, CandidateRow, ParsedList, scoped_candidate_key
from .registry import Adapter, Attestation

JSON_VERSION = 'reviewed-json-list-v1'
CSV_VERSION = 'reviewed-csv-list-v1'
VERSIONS = (JSON_VERSION, CSV_VERSION)
EMPTY = frozenset({'', '-', '--', '---'})
FIELDS = frozenset({'rank', 'code', 'score', 'consent', 'priority', 'status'})
MAX_RECORDS = 100_000


@dataclass(frozen=True)
class StructuredProfile:
    source_id: str
    group_id: str
    url: str
    year: int
    rows: int
    seats: int | None
    version: str
    fields: tuple[tuple[str, str], ...]
    proof: Attestation | None = None
    kind: str = 'archive'
    items_path: tuple[str, ...] = ()
    delimiter: str = ';'
    headers: tuple[str, ...] = ()
    consent_values: tuple[tuple[str, bool], ...] = (('да', True), ('нет', False), ('true', True), ('false', False))
    enrolled_values: tuple[str, ...] = ('зачислен',)
    withdrawn_values: tuple[str, ...] = ('отозвано', 'забрал документы')
    code_pattern: str = r'[A-Za-z0-9-]{1,64}'

    def __post_init__(self):
        names = [name for name, _ in self.fields]
        if (self.version not in VERSIONS or not {'rank', 'code'} <= set(names) or not set(names) <= FIELDS or len(names) != len(set(names))
                or not 1 <= self.rows <= MAX_RECORDS or self.kind not in ('archive', 'live')
                or (self.version == CSV_VERSION and (len(self.delimiter) != 1 or not self.headers))
                or (self.version == JSON_VERSION and any(not isinstance(part, str) or not part for part in self.items_path))):
            raise ValueError('invalid_structured_profile')


def text(value):
    """Scalar from JSON or CSV as stripped text; nested structures are a format change."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        if value != value or value in (float('inf'), float('-inf')):
            raise ValueError()
        return format(Decimal(str(value)).normalize(), 'f')
    if isinstance(value, str):
        return ' '.join(value.replace('\xa0', ' ').split())
    raise ValueError()


def records_from_json(body, profile):
    data = json.loads(body, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    for part in profile.items_path:
        if not isinstance(data, dict) or part not in data:
            raise ValueError()
        data = data[part]
    if not isinstance(data, list) or len(data) > MAX_RECORDS or not all(isinstance(item, dict) for item in data):
        raise ValueError()
    return data


def records_from_csv(body, profile):
    reader = csv.reader(io.StringIO(body, newline=''), delimiter=profile.delimiter, strict=True)
    header = next(reader, None)
    if header is None or tuple(text(h) for h in header) != profile.headers:
        raise ValueError()
    rows = []
    for row in reader:
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(header) or len(rows) >= MAX_RECORDS:
            raise ValueError()
        rows.append(dict(zip(profile.headers, row)))
    return rows


def normalise(records, binding, secret, profile):
    mapping = dict(profile.fields)
    if len(records) != profile.rows:
        raise ValueError()
    consent_values = dict(profile.consent_values)
    entries, seen = [], set()
    for index, record in enumerate(records, 1):
        if any(key not in record for key in mapping.values()):
            raise ValueError()
        values = {name: text(record[key]) for name, key in mapping.items()}
        if values['rank'] != str(index):
            raise ValueError()
        code = values['code']
        if not re.fullmatch(profile.code_pattern, code):
            raise ValueError()
        key = scoped_candidate_key(binding, code, secret)
        if key in seen:
            raise ValueError()
        seen.add(key)
        score = None
        if values.get('score', '') not in EMPTY:
            if not re.fullmatch(r'[0-9]{1,4}(?:[.,][0-9]{1,2})?', values['score']):
                raise ValueError()
            score = Decimal(values['score'].replace(',', '.'))
        consent = None
        if values.get('consent', '') not in EMPTY:
            lowered = values['consent'].casefold()
            if lowered not in consent_values:
                raise ValueError()
            consent = consent_values[lowered]
        priority = None
        if values.get('priority', '') not in EMPTY:
            if not re.fullmatch(r'[1-9][0-9]{0,3}', values['priority']):
                raise ValueError()
            priority = int(values['priority'])
        participation = 'unknown'
        status = values.get('status', '').casefold()
        if status not in EMPTY:
            if status in profile.enrolled_values:
                participation = 'enrolled'
            elif status in profile.withdrawn_values:
                participation = 'withdrawn'
            else:
                raise ValueError()
        entries.append(CandidateRow(candidate_key=key, row_ref=f'record/{index}', official_rank=index, score=score,
                                    consent=consent, priority=priority, participation=participation))
    warnings = ['no_source_timestamp']
    if any(row.consent is None for row in entries):
        warnings.append('unknown_consent')
    if any(row.priority is None for row in entries):
        warnings.append('unknown_priority')
    return ParsedList(source_id=binding.source_id, group_id=binding.group_id, year=profile.year, adapter_version=profile.version,
                      kind=profile.kind, complete=True, expected_rows=profile.rows, seats=profile.seats, entries=tuple(entries),
                      warnings=tuple(warnings))


def parse_structured(response, binding, secret, profile):
    try:
        if (binding.source_id, binding.group_id, binding.url, binding.year, binding.kind) != (profile.source_id, profile.group_id, profile.url, profile.year, profile.kind):
            raise AdapterError('invalid_binding')
        body = response.body.decode(response.charset or 'utf-8')
        records = records_from_json(body, profile) if profile.version == JSON_VERSION else records_from_csv(body, profile)
        return normalise(records, binding, secret, profile)
    except AdapterError:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, InvalidOperation, csv.Error, RecursionError):
        raise AdapterError('invalid_format') from None


def make_structured_adapter(secret, profiles, *, version, attested=True):
    """One adapter per format version; attested adapters require a proof for every profile."""
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError('source_identity_key_required')
    profiles = tuple(profiles)
    if not profiles or any(p.version != version for p in profiles) or len({p.url for p in profiles}) != len(profiles):
        raise ValueError('reviewed_profiles_required')
    if attested and any(p.proof is None or p.proof.adapter_version != version for p in profiles):
        raise ValueError('reviewed_profiles_required')
    by_url = {p.url: p for p in profiles}

    def decode(response, binding):
        profile = by_url.get(binding.url)
        if profile is None:
            raise AdapterError('invalid_binding')
        return parse_structured(response, binding, secret, profile)

    proofs = tuple(p.proof for p in profiles) if attested else ()
    return Adapter(version, frozenset(urlsplit(p.url).hostname for p in profiles), decode, attested=attested, attestations=proofs,
                   max_bytes=8*1024*1024)


# Reviewed official JSON/CSV lists. Empty until a source passes passport, original and independent check.
PROFILES: tuple[StructuredProfile, ...] = ()
