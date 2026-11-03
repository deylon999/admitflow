from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.admissions import Campaign,CompetitionGroup,University
from app.config import Settings
from app.main import create_app
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.storage import RawStore
from test_sgu_adapter import BINDING,KEY,response
from source_helpers import NOW


@pytest.fixture
def catalog_client(tmp_path,monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    app=create_app(Settings(database_url=f'sqlite:///{tmp_path}/catalog.db'))
    with TestClient(app) as client:
        register_sgu(app.state.engine,enable=True,registry=app.state.source_registry)
        yield client,app


def test_archive_catalog_exposes_metadata_without_candidate_rows(catalog_client,tmp_path):
    client,app=catalog_client
    before=client.get('/api/v1/groups').json()['items'][0]
    assert before['coverage']=='archive' and before['lookupAvailable'] is False and before['fetchedAt'] is None
    raw=response();parsed=app.state.source_registry.resolve(BINDING).parse(raw,BINDING)
    publish(app.state.engine,BINDING.source_id,parsed,raw,RawStore(tmp_path/'raw'),registry=app.state.source_registry)
    result=client.get('/api/v1/groups?q=ПРОГРАММНАЯ&year=2026&branchId=main').json()
    assert result['total']==1
    group=result['items'][0]
    assert group['lookupAvailable'] and group['coverage']=='archive' and group['dataKind']=='archive'
    assert group['rowCount']==573 and group['sourceUpdatedAt'] is None and group['assessmentAvailable'] is False
    assert not {'entries','candidateKey','payloadHash','raw'} & group.keys()


def test_branch_season_filters_and_stable_cursor(catalog_client):
    client,app=catalog_client
    with Session(app.state.engine) as db:
        db.add(University(id='test-branch',name='Тестовый филиал',parent_id='sgu-saratov',official_url='https://example.org',provenance_url='https://example.org',verified_at=NOW));db.flush()
        db.add(Campaign(id='branch-campaign',university_id='test-branch',year=2025,level='bachelor'));db.flush()
        db.add(CompetitionGroup(id='branch-group',campaign_id='branch-campaign',official_id='branch',title='Тестовое ручное направление',study_form='full-time',funding='budget',category='general',seats=None,coverage='manual'));db.commit()
    assert client.get('/api/v1/groups?universityId=sgu-saratov').json()['total']==2
    branch=client.get('/api/v1/groups?branchId=test-branch&year=2025').json()
    assert branch['total']==1 and branch['items'][0]['coverage']=='manual' and branch['items'][0]['seats'] is None
    assert branch['facets']['branches']==[{'id':'test-branch','name':'Тестовый филиал'}]
    first=client.get('/api/v1/groups?limit=1').json()
    second=client.get('/api/v1/groups',params={'limit':1,'after':first['nextCursor']}).json()
    assert len({first['items'][0]['id'],second['items'][0]['id']})==2 and second['nextCursor'] is None
    assert client.get('/api/v1/groups?universityId=unknown').json()['total']==0
    for params in ({'limit':51},{'year':2027.5},{'q':'x'*121},{'after':'x'*37}):
        assert client.get('/api/v1/groups',params=params).status_code==422
