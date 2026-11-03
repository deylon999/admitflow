from dataclasses import replace
from datetime import timedelta

import pytest
from sqlalchemy import func,select
from sqlalchemy.orm import Session

from app.admissions import CandidateEntry,PublishedSnapshot,SourceSnapshot
from app.sources.contracts import AdapterError
from app.sources.publishing import publish
from app.sources.registry import Registry
from app.sources.storage import RawStore
from app.sources.validation import Quarantined,validate_list
from sgu_helpers import seed_sgu
from test_sgu_adapter import BINDING,KEY,make_adapter,response


@pytest.mark.parametrize('problem,code',[
    ('incomplete','incomplete_list'),('wrong-group','identity_mismatch'),('duplicate','duplicate_candidate'),
    ('rank','invalid_official_order'),('count','row_count_mismatch'),('unknown-bool','invalid_schema'),
])
def test_real_sgu_invalid_normalization_retains_last_good(source_engine,tmp_path,problem,code):
    seed_sgu(source_engine)
    adapter=make_adapter(KEY);registry=Registry((adapter,));store=RawStore(tmp_path/'raw')
    raw=response();parsed=adapter.parse(raw,BINDING)
    first=publish(source_engine,BINDING.source_id,parsed,raw,store,registry=registry)
    values=list(parsed.entries)
    if problem=='incomplete':bad=parsed.model_copy(update={'complete':False})
    elif problem=='wrong-group':bad=parsed.model_copy(update={'group_id':'another-group'})
    elif problem=='count':bad=parsed.model_copy(update={'expected_rows':574})
    else:
        changes={'duplicate':{'candidate_key':values[0].candidate_key},'rank':{'official_rank':1},'unknown-bool':{'consent':'false'}}
        values[1]=values[1].model_copy(update=changes[problem]);bad=parsed.model_copy(update={'entries':tuple(values)})
    with pytest.raises(Quarantined,match=code):
        publish(source_engine,BINDING.source_id,bad,replace(raw,fetched_at=raw.fetched_at+timedelta(minutes=1)),store,registry=registry)
    with Session(source_engine) as db:
        assert db.get(PublishedSnapshot,BINDING.source_id).snapshot_id==first
        assert db.scalar(select(func.count()).select_from(SourceSnapshot))==1
        assert db.scalar(select(func.count()).select_from(CandidateEntry))==573


def test_real_sgu_unknown_fields_stay_null_in_normalized_hash():
    raw=response();parsed=make_adapter(KEY).parse(raw,BINDING)
    row=parsed.entries[0].model_copy(update={'consent':None,'priority':None,'score':None})
    value=parsed.model_copy(update={'entries':(row,*parsed.entries[1:])})
    normalized=validate_list(value,BINDING,raw.fetched_at)
    assert normalized.parsed.entries[0].consent is None
    assert normalized.parsed.entries[0].priority is None
    assert normalized.parsed.entries[0].score is None


def test_publication_cannot_bypass_declared_adapter_size(source_engine,tmp_path):
    from source_helpers import seed_source,parsed,raw,registry
    seed_source(source_engine)
    with pytest.raises(AdapterError,match='invalid_format'):
        publish(source_engine,'source-1',parsed(),raw(b'x'*(5*1024*1024+1)),RawStore(tmp_path/'raw'),registry=registry(),allow_unattested=True)
    assert not list((tmp_path/'raw').glob('[0-9a-f]'*64))
