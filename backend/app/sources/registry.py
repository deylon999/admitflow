"""Closed code registry; production starts with zero attested adapters."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
import os
import re
from typing import Callable
from urllib.parse import urlsplit

from .contracts import AdapterError, ParsedList, SourceBinding
from .fetcher import DEFAULT_SOURCE_BYTES, MAX_SOURCE_BYTES, FetchResult, valid_domains


@dataclass(frozen=True)
class Attestation:
    """Code-reviewed evidence declaration; runtime never downloads evidence paths."""
    passport: str
    fixture: str
    fixture_sha256: str
    original_sha256: str
    source_url: str
    year: int
    kind: str
    sample_rows: int
    checked_rows: int
    verified_at: datetime
    adapter_version: str

    def __post_init__(self):
        def relative(value, suffix=None):
            return (isinstance(value, str) and bool(value) and value != '.' and '\\' not in value and not PurePosixPath(value).is_absolute()
                    and '..' not in PurePosixPath(value).parts and len(value) <= 300
                    and (suffix is None or value.endswith(suffix)))
        try:
            url = urlsplit(self.source_url)
            valid_url = (url.scheme == 'https' and valid_domains(frozenset({url.hostname})) and url.port in (None,443)
                         and not url.username and not url.password and not url.fragment
                         and not any(ord(c) < 33 or ord(c) == 127 for c in self.source_url))
            valid = (relative(self.passport, '.md') and relative(self.fixture)
                     and all(isinstance(value,str) and re.fullmatch(r'[a-f0-9]{64}',value) for value in (self.fixture_sha256,self.original_sha256))
                     and valid_url and type(self.year) is int and 2000 <= self.year <= 2100 and self.kind in ('archive','live')
                     and type(self.sample_rows) is int and 1 <= self.sample_rows <= 100_000
                     and type(self.checked_rows) is int and min(50,self.sample_rows) <= self.checked_rows <= self.sample_rows
                     and isinstance(self.verified_at,datetime) and self.verified_at.utcoffset() is not None
                     and isinstance(self.adapter_version,str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:+-]{0,79}', self.adapter_version)))
        except (ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise ValueError('invalid_adapter_attestation')


@dataclass(frozen=True)
class Adapter:
    version: str
    domains: frozenset[str]
    parse: Callable[[FetchResult, SourceBinding], ParsedList]
    attested: bool = False
    attestation: Attestation | None = None
    max_bytes: int = DEFAULT_SOURCE_BYTES
    attestations: tuple[Attestation, ...] = ()

    @property
    def proofs(self):
        return ((self.attestation,) if self.attestation is not None else ()) + self.attestations

    def __post_init__(self):
        if (not isinstance(self.version,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:+-]{0,79}',self.version)
                or not valid_domains(self.domains) or not callable(self.parse) or type(self.attested) is not bool
                or type(self.max_bytes) is not int or not 1 <= self.max_bytes <= MAX_SOURCE_BYTES):
            raise ValueError('invalid_adapter_declaration')
        if (not isinstance(self.attestations,tuple) or any(not isinstance(proof,Attestation) for proof in self.proofs)
                or (self.attested and not self.proofs)
                or any(proof.adapter_version != self.version or urlsplit(proof.source_url).hostname not in self.domains for proof in self.proofs)
                or len({(proof.source_url,proof.year,proof.kind) for proof in self.proofs}) != len(self.proofs)):
            raise ValueError('invalid_adapter_attestation')


class Registry:
    def __init__(self, adapters: tuple[Adapter, ...] = ()):
        self._adapters = {adapter.version: adapter for adapter in adapters}
        if len(self._adapters) != len(adapters):
            raise ValueError('duplicate_adapter_version')

    @property
    def attested_versions(self):
        return tuple(version for version,adapter in self._adapters.items() if adapter.attested)

    def resolve(self, binding: SourceBinding, *, allow_unattested=False) -> Adapter:
        if not binding.enabled:
            raise AdapterError('source_disabled')
        adapter = self._adapters.get(binding.adapter_version)
        if adapter is None:
            raise AdapterError('adapter_unavailable')
        if not adapter.attested and not allow_unattested:
            raise AdapterError('unattested_adapter')
        if adapter.attested and not any((binding.url,binding.year,binding.kind)==(proof.source_url,proof.year,proof.kind) for proof in adapter.proofs):
            raise AdapterError('invalid_binding')
        try:
            parsed = urlsplit(binding.url)
            valid = (len(binding.url) <= 4096 and not any(ord(c) < 32 or ord(c) == 127 for c in binding.url)
                     and parsed.scheme == 'https' and parsed.port in (None,443)
                     and not parsed.username and not parsed.password and not parsed.fragment
                     and parsed.hostname == binding.domain and binding.domain in adapter.domains)
        except ValueError:
            valid = False
        if not valid:
            raise AdapterError('invalid_binding') from None
        return adapter


PRODUCTION_REGISTRY = Registry()


def identity_key():
    value = os.getenv('SOURCE_IDENTITY_KEY')
    if value is None:
        return None
    if not re.fullmatch(r'(?:[a-fA-F0-9]{2}){32,64}',value):
        raise RuntimeError('SOURCE_IDENTITY_KEY must be32–64bytes encoded as hex')
    return bytes.fromhex(value)


def runtime_registry():
    """Opt in using an operator-owned stable key; never enable a Source row here."""
    key=identity_key()
    if key is None:return PRODUCTION_REGISTRY
    from .adapters.sgu2026 import make_adapter
    return Registry((make_adapter(key),))
