from datetime import timedelta
from sqlalchemy import delete,func,select
from sqlalchemy.orm import Session
from app.admissions import CandidateEntry
from app.database import BrowserSession
from test_api import HEADERS,start
from test_source_lookup import lookup_context
from test_sgu_adapter import BINDING


def test_guest_removed_during_lookup_never_returns_private_facts(lookup_context,monkeypatch):
    import app.source_api as source_api
    client,app=lookup_context;start(client);original=source_api.available_source
    def removed(db,*args,**kwargs):
        result=original(db,*args,**kwargs)
        with Session(app.state.engine) as cleanup:
            cleanup.execute(delete(BrowserSession));cleanup.commit()
        return result
    monkeypatch.setattr(source_api,'available_source',removed)
    result=client.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS)
    assert result.status_code==401 and 'officialRank' not in result.text and 'confirmationToken' not in result.text
    with Session(app.state.engine) as db:assert db.scalar(select(func.count()).select_from(CandidateEntry))==573


def test_guest_deadline_crossed_during_lookup_does_not_issue_expired_confirmation(lookup_context,monkeypatch):
    from app.main import utcnow
    client,_=lookup_context;start(client);now=utcnow();calls=[0]
    def clock():
        calls[0]+=1
        return now if calls[0]<3 else now+timedelta(days=31)
    monkeypatch.setattr('app.main.utcnow',clock)
    result=client.post(f'/api/v1/sources/{BINDING.source_id}/lookup',json={'publicCode':'FIXTURE-000001'},headers=HEADERS)
    assert result.status_code==401 and 'confirmationToken' not in result.text
