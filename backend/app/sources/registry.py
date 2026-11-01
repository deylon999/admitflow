"""Closed code registry; production starts with zero attested adapters."""
from dataclasses import dataclass
import re
from typing import Callable
from urllib.parse import urlsplit

from .contracts import AdapterError, ParsedList, SourceBinding
from .fetcher import FetchResult, valid_domains


@dataclass(frozen=True)
class Adapter:
    version: str
    domains: frozenset[str]
    parse: Callable[[FetchResult, SourceBinding], ParsedList]
    attested: bool = False

    def __post_init__(self):
        if (not isinstance(self.version,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:+-]{0,79}',self.version)
                or not valid_domains(self.domains) or not callable(self.parse) or type(self.attested) is not bool):
            raise ValueError('invalid_adapter_declaration')


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
