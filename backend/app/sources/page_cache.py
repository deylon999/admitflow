"""Small process-local cache for sequential scopes sharing one verified page.

This is not a distributed fetch lock. Every worker keeps its own bounded cache;
database domain leases still control concurrent jobs. Hits preserve fetched_at.
"""
from collections import OrderedDict
from datetime import datetime,timezone
import hashlib
import math
import time
from urllib.parse import urlsplit

from .fetcher import DEFAULT_SOURCE_BYTES,FetchPolicy,FetchResult


class PageFetchCache:
    def __init__(self,fetch,*,ttl=60,max_bytes=32*1024*1024,max_entries=64,
                 monotonic=time.monotonic,clock=lambda:datetime.now(timezone.utc)):
        if (not callable(fetch) or type(ttl) not in (int,float) or not math.isfinite(ttl) or not 0<ttl<=60
            or type(max_bytes) is not int or not 1<=max_bytes<=256*1024*1024
            or type(max_entries) is not int or not 1<=max_entries<=4096):
            raise ValueError('invalid_page_cache_policy')
        self.fetch=fetch;self.ttl=ttl;self.max_bytes=max_bytes;self.max_entries=max_entries
        self.monotonic=monotonic;self.clock=clock;self._pages=OrderedDict();self.byte_count=0
        self.hits=0;self.misses=0

    def _recent(self,raw,saved,tick,now):
        try:
            return 0<=tick-saved<self.ttl and 0<=(now-raw.fetched_at).total_seconds()<self.ttl
        except (TypeError,AttributeError,OverflowError):return False

    def _remove(self,key):
        _,raw=self._pages.pop(key);self.byte_count-=len(raw.body)

    def __call__(self,binding,domains,*,timeout=50,max_bytes=DEFAULT_SOURCE_BYTES):
        FetchPolicy(domains=domains,max_bytes=max_bytes)
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:
            raise ValueError('invalid_fetch_timeout')
        tick=self.monotonic();now=self.clock()
        for key,(saved,raw) in tuple(self._pages.items()):
            if not self._recent(raw,saved,tick,now):self._remove(key)
        key=(binding.url,binding.domain,domains,max_bytes)
        if key in self._pages:
            self.hits+=1;self._pages.move_to_end(key)
            return self._pages[key][1]
        self.misses+=1
        raw=self.fetch(binding,domains,timeout=timeout,max_bytes=max_bytes)
        # Never retain failures, oversized bodies, changed redirect URLs, invalid
        # checksums, future timestamps or responses already older than the TTL.
        url=urlsplit(binding.url)
        if (isinstance(raw,FetchResult) and isinstance(raw.body,bytes) and raw.url==binding.url
            and url.scheme=='https' and url.hostname==binding.domain and binding.domain in domains
            and len(raw.body)<=min(max_bytes,self.max_bytes)
            and hashlib.sha256(raw.body).hexdigest()==raw.payload_hash
            and self._recent(raw,self.monotonic(),self.monotonic(),self.clock())):
            while self._pages and (len(self._pages)>=self.max_entries or self.byte_count+len(raw.body)>self.max_bytes):
                self._remove(next(iter(self._pages)))
            self._pages[key]=(self.monotonic(),raw);self.byte_count+=len(raw.body)
        return raw
