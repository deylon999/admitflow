from dataclasses import replace
from datetime import timedelta

import pytest
from app.sources.fetcher import FetchError
from app.sources.page_cache import PageFetchCache
from source_helpers import BINDING,NOW,raw

DOMAINS=frozenset({'example.org'})


def test_scopes_share_transport_but_keep_actual_timestamp_and_expire_on_both_clocks():
    tick=[0.];now=[NOW];calls=[]
    def fetch(*args,**kwargs):calls.append(args);return raw(at=now[0])
    cache=PageFetchCache(fetch,monotonic=lambda:tick[0],clock=lambda:now[0])
    first=cache(BINDING,DOMAINS)
    assert cache(replace(BINDING,source_id='different',group_id='other'),DOMAINS) is first
    assert first.fetched_at==NOW and len(calls)==1 and cache.hits==1
    tick[0]=60
    assert cache(BINDING,DOMAINS) is not first and len(calls)==2
    now[0]+=timedelta(seconds=61)
    cache(BINDING,DOMAINS);assert len(calls)==3
    now[0]-=timedelta(seconds=1)
    cache(BINDING,DOMAINS);assert len(calls)==4


def test_allowlist_and_size_policies_are_distinct_cache_keys_and_always_validated():
    calls=[]
    def fetch(*a,**kw):calls.append(kw);return raw()
    cache=PageFetchCache(fetch,clock=lambda:NOW)
    cache(BINDING,DOMAINS)
    cache(BINDING,DOMAINS,max_bytes=100)
    cache(BINDING,DOMAINS|{'other.example.org'})
    assert len(calls)==3
    for kwargs in ({'max_bytes':0},{'timeout':0},{'timeout':float('nan')}):
        with pytest.raises(ValueError):cache(BINDING,DOMAINS,**kwargs)
    with pytest.raises(ValueError):cache(BINDING,frozenset())


def test_lru_and_total_byte_limits_bound_retained_originals():
    calls=[]
    def fetch(b,*a,**kw):calls.append(b.url);return replace(raw(b'1234'),url=b.url)
    cache=PageFetchCache(fetch,max_entries=2,max_bytes=8,clock=lambda:NOW)
    a,b,c=(replace(BINDING,url=f'https://example.org/{n}') for n in 'abc')
    cache(a,DOMAINS);cache(b,DOMAINS);cache(a,DOMAINS);cache(c,DOMAINS)
    assert cache.byte_count==8 and len(calls)==3
    cache(b,DOMAINS);assert len(calls)==4 and cache.byte_count==8
    cache=PageFetchCache(fetch,max_bytes=3,clock=lambda:NOW)
    cache(a,DOMAINS);cache(a,DOMAINS)
    assert cache.byte_count==0 and cache.hits==0


@pytest.mark.parametrize('damage',['old','future','hash','redirect','large'])
def test_unusable_transport_metadata_is_never_retained(damage):
    result=raw()
    if damage=='old':result=replace(result,fetched_at=NOW-timedelta(seconds=61))
    elif damage=='future':result=replace(result,fetched_at=NOW+timedelta(seconds=1))
    elif damage=='hash':result=replace(result,payload_hash='0'*64)
    elif damage=='redirect':result=replace(result,url='https://example.org/redirect')
    elif damage=='large':result=raw(b'x'*101)
    cache=PageFetchCache(lambda *a,**kw:result,clock=lambda:NOW)
    cache(BINDING,DOMAINS,max_bytes=100);cache(BINDING,DOMAINS,max_bytes=100)
    assert cache.hits==cache.byte_count==0


def test_network_errors_are_not_cached():
    calls=[]
    def fetch(*a,**kw):calls.append(True);raise FetchError('timeout',retry_after=60)
    cache=PageFetchCache(fetch)
    for _ in range(2):
        with pytest.raises(FetchError):cache(BINDING,DOMAINS)
    assert len(calls)==2 and cache.byte_count==0
