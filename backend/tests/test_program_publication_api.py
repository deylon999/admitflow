"""Native PostgreSQL public projection; synthetic sources are never real evidence."""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, insert, select
from sqlalchemy.orm import Session

from app.admissions import Campaign, CampaignProgram, CompetitionGroup, CompetitionGroupProgram, University
from app.catalog_identity import campaign_id
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.product_catalog import program_page
from app.program_catalog_import import import_document
from app.program_catalog_models import ProgramCatalogDocument as Document, ProgramCatalogRevision as Revision, ProgramCatalogFact as Fact, ProgramCatalogPublication as Publication
from app.program_catalog_review import EXTRACTORS
from native_support import postgres_engine  # noqa: F401
from test_program_catalog_import import source, store  # noqa: F401

pytestmark = pytest.mark.postgres
BASE = '/api/v1/catalog'


@pytest.fixture
def client(postgres_engine):
    app = create_app(Settings(database_url=postgres_engine.url.render_as_string(hide_password=False), auto_create_schema=False))
    with TestClient(app) as value:
        yield value


def publish(engine, store, kind='hse'):
    body, review = source(kind)
    result = import_document(engine, review, body, store)
    assert result['outcome'] == 'published', result
    return body, review, result


def test_published_programmes_keep_legacy_ids_and_null_unknowns(client, postgres_engine, store):
    assert client.get(BASE+'/programs').json()['total'] == 0
    import_reviewed(postgres_engine)
    old = client.get(BASE+'/programs').json()['items']
    assert {p['id'] for p in old} == {'sgu-2026-4588', 'sgu-2026-4576'}
    assert all(p['programId'] is None and p['competitionGroups'][0]['id'] == p['id'] for p in old)
    body, review, _ = publish(postgres_engine, store)
    publish(postgres_engine, store, 'sgu')
    assert import_document(postgres_engine, review, body, store)['outcome'] == 'unchanged'
    page = client.get(BASE+'/programs').json()
    assert page['total'] == 6 and page['years'] == [2027, 2026]
    assert len({p['id'] for p in page['items']}) == 6
    for row in old:
        assert client.get(BASE+'/programs/'+row['id']).json() == row
    current = client.get(BASE+'/programs?universityId=miccedu-1766&year=2027').json()
    assert current['total'] == 2 and current['years'] == [2027]
    for row in current['items']:
        assert row['programId'] and row['programId'] != row['id']
        assert row['competitionGroups'] == []
        assert all(row[k] is None for k in ('code','funding','studyForm','category','seats','examRequirements','forecast','historicalCutoff'))
        assert row['provenance']['kind'] == 'admissions'
        assert row['provenance']['url'] == review['url']
        assert row['provenance']['originalSha256'] == review['original_sha256']
        assert row['provenance']['sourceUpdatedAt'] is None
        assert client.get(BASE+'/programs/'+row['id']).json() == row
    hse = client.get(BASE+'/universities/miccedu-1766').json()
    assert (hse['knownProgramCount'], hse['years']) == (2, [2027])
    sgu = client.get(BASE+'/universities/sgu-saratov').json()
    assert (sgu['knownProgramCount'], sgu['years']) == (4, [2026])
    assert client.get(BASE+'/programs?year=2026&universityId=miccedu-1766').json()['total'] == 0


def test_sql_search_sort_total_and_pagination(client, postgres_engine, store):
    import_reviewed(postgres_engine)
    publish(postgres_engine, store)
    publish(postgres_engine, store, 'sgu')
    first = client.get(BASE+'/programs?limit=2').json()
    second = client.get(BASE+'/programs?limit=2&offset=2').json()
    last = client.get(BASE+'/programs?limit=2&offset=4').json()
    assert all(p['total'] == 6 for p in (first, second, last))
    assert [p['nextOffset'] for p in (first,second,last)] == [2,4,None]
    ids = [p['id'] for page in (first,second,last) for p in page['items']]
    assert len(ids) == len(set(ids)) == 6
    reverse = client.get(BASE+'/programs?sort=name-desc&limit=50').json()
    assert [p['id'] for p in reverse['items']] == ids[::-1]
    for term in ('EXAMPLE FASHION', '06.03.01', 'ПРОГРАММНАЯ'):
        assert client.get(BASE+'/programs', params={'q':term}).json()['total'] == 1
        assert client.get(BASE+'/universities', params={'q':term}).json()['total'] == 1
    for term in ('%', '_', "' OR 1=1", 'missing'):
        assert client.get(BASE+'/programs', params={'q':term}).json()['total'] == 0
    assert client.get(BASE+'/programs?offset=100000').json()['items'] == []
    assert client.get(BASE+'/programs?subject=math').json()['total'] == 0


@pytest.mark.parametrize('status', ['verified','unverified','conflict'])
def test_unpublished_revisions_and_raw_documents_are_not_public(client, postgres_engine, store, status):
    _, _, result = publish(postgres_engine, store)
    before = client.get(BASE+'/programs').json()
    with Session(postgres_engine) as db:
        revision = db.get(Revision, result['revisionId'])
        values = {c.name:getattr(revision,c.name) for c in Revision.__table__.columns}
        facts = [{c.name:getattr(f,c.name) for c in Fact.__table__.columns} for f in db.scalars(select(Fact))]
    with postgres_engine.begin() as db:
        db.execute(insert(Document).values(id='draft-doc',campaign_id=values['campaign_id'],source_namespace='synthetic-unpublished'))
        db.execute(insert(Revision).values(**(values | dict(id='draft-revision',document_id='draft-doc',verification_status=status))))
        db.execute(insert(Fact), [f | dict(revision_id='draft-revision', title='Secret unpublished title') for f in facts])
    assert client.get(BASE+'/programs').json() == before
    assert client.get(BASE+'/programs?q=Secret').json()['total'] == 0
    public = client.get(BASE+'/programs').text
    for private in ('draft-revision','Secret unpublished','admissionTotals','evidence','extractorVersion','normalizedSha256','<html','Example Fashion</a>'):
        assert private not in public
    for path in ('/documents/draft-doc','/revisions/draft-revision','/raw/'+values['original_sha256']):
        assert client.get(BASE+path).status_code == 404


def changed_source(body, review):
    changed = deepcopy(review)
    new_body = body.replace(b'Example Fashion', b'Reviewed updated title')
    changed['original_sha256'] = hashlib.sha256(new_body).hexdigest()
    changed['checked_at'] = (datetime.fromisoformat(review['checked_at'])+timedelta(seconds=1)).isoformat()
    changed['programs'][0]['title'] = 'Reviewed updated title'
    return new_body, changed


def test_replacement_and_rejected_source_keep_history_and_public_ids(client, postgres_engine, store):
    body, review, _ = publish(postgres_engine, store)
    before = client.get(BASE+'/programs?q=Fashion').json()['items'][0]
    new_body, changed = changed_source(body, review)
    assert import_document(postgres_engine, changed, new_body, store)['outcome'] == 'published'
    after = client.get(BASE+'/programs/'+before['id']).json()
    assert after['title'] == 'Reviewed updated title'
    assert after['programId'] == before['programId'] and after['id'] == before['id']
    assert client.get(BASE+'/programs?q=Fashion').json()['total'] == 0
    assert import_document(postgres_engine, review, body, store)['outcome'] == 'rejected'
    assert import_document(postgres_engine, changed, b'broken', store)['outcome'] == 'rejected'
    assert client.get(BASE+'/programs/'+before['id']).json() == after


def test_one_response_uses_one_postgresql_publication_snapshot(client, postgres_engine, store, monkeypatch):
    import app.product_catalog as facade
    body, review, _ = publish(postgres_engine, store)
    before = client.get(BASE+'/programs').json()
    original = facade.hydrate_programs
    new_body, changed = changed_source(body, review)
    fired = False
    def concurrent_publish(db, keys, legacy):
        nonlocal fired
        if not fired:
            fired = True
            assert db.connection().get_isolation_level() == 'REPEATABLE READ'
            assert import_document(postgres_engine, changed, new_body, store)['outcome'] == 'published'
        return original(db, keys, legacy)
    monkeypatch.setattr(facade, 'hydrate_programs', concurrent_publish)
    assert client.get(BASE+'/programs').json() == before
    assert client.get(BASE+'/programs?q=Reviewed').json()['total'] == 1


def test_shared_confirmed_contest_is_explicit_and_never_summed(client, postgres_engine, store, monkeypatch):
    body, review = source()
    group = dict(id='synthetic-shared',official_id='source-group-1',title='Synthetic combined competition',study_form='full-time',funding='budget',category='separate-quota',seats=0)
    cid = campaign_id(review['university_id'],review['year'],review['level'])
    with postgres_engine.begin() as db:
        db.execute(insert(University).values(id=review['university_id'],name=review['university_name'],official_url=review['university_url'],provenance_url=review['url'],verified_at=datetime.fromisoformat(review['checked_at'])))
        db.execute(insert(Campaign).values(id=cid,university_id=review['university_id'],year=review['year'],level=review['level']))
        db.execute(insert(CompetitionGroup).values(**group,campaign_id=cid,coverage='candidate'))
    extractor = EXTRACTORS[review['extractor_version']]
    def with_group(doc, scope):
        records = extractor(doc,scope)
        for r in records:
            r['groups'] = [group]
        return records
    monkeypatch.setitem(EXTRACTORS,review['extractor_version'],with_group)
    for r in review['programs']:
        r['groups'] = [group]
    assert import_document(postgres_engine,review,body,store)['outcome'] == 'published'
    rows = client.get(BASE+'/programs').json()['items']
    assert len(rows) == 2 and len({p['programId'] for p in rows}) == 2
    for p in rows:
        assert p['seats'] is None and p['funding'] is None and p['category'] is None
        g, = p['competitionGroups']
        assert (g['id'],g['campaignId'],g['category'],g['seats']) == ('synthetic-shared',cid,'separate-quota',0)
        assert g['provenance'] == p['provenance']


def test_conflicting_current_identity_is_quarantined(client, postgres_engine, store):
    import_reviewed(postgres_engine)
    _, _, result = publish(postgres_engine, store)
    with Session(postgres_engine) as db:
        revision = db.get(Revision,result['revisionId'])
        values = {c.name:getattr(revision,c.name) for c in Revision.__table__.columns}
        facts = [{c.name:getattr(f,c.name) for c in Fact.__table__.columns} for f in db.scalars(select(Fact))]
    with postgres_engine.begin() as db:
        db.execute(insert(Document).values(id='conflict-doc',campaign_id=values['campaign_id'],source_namespace='synthetic-conflict'))
        db.execute(insert(Revision).values(**(values | dict(id='conflict-revision',document_id='conflict-doc'))))
        db.execute(insert(Fact), [f | dict(revision_id='conflict-revision') for f in facts])
        db.execute(insert(Publication).values(document_id='conflict-doc',revision_id='conflict-revision'))
    page = client.get(BASE+'/programs').json()
    assert page['total'] == 2 and {p['id'] for p in page['items']} == {'sgu-2026-4588','sgu-2026-4576'}
    for f in facts:
        assert client.get(BASE+'/programs/'+f['public_id']).status_code == 404


def test_facets_survive_empty_filtered_and_deep_pages(client, postgres_engine, store):
    import_reviewed(postgres_engine)
    publish(postgres_engine,store)
    for params,total in [({'q':'missing'},0),({'subject':'math'},0),
                         ({'year':2025},0),({'offset':100000},4)]:
        response=client.get(BASE+'/programs',params=params)
        assert response.status_code==200
        page=response.json()
        assert page['items']==[] and page['total']==total and page['nextOffset'] is None
        assert page['years']==[2027,2026] and page['subjects']==[]
    page=client.get(BASE+'/programs',params={'universityId':'miccedu-1766','year':2026}).json()
    assert page['years']==[2027] and page['total']==0


def test_casefold_literal_search_and_university_token_aggregation(client,postgres_engine,store):
    body,review=source()
    title='Straße ΟΣ Ёж 100%_ /'
    body=body.replace(b'Example Fashion',title.encode())
    review['original_sha256']=hashlib.sha256(body).hexdigest()
    review['programs'][0]['title']=title
    assert import_document(postgres_engine,review,body,store)['outcome']=='published'
    for q in ['STRASSE','οσ','ЁЖ','100%_','%_','/']:
        response=client.get(BASE+'/programs',params={'q':q})
        assert response.status_code==200
        assert response.json()['total']==1
    # Tokens may match different confirmed programmes of the same university;
    # counts and years describe its whole published scope, not just the hits.
    result=client.get(BASE+'/universities',params={'q':'STRASSE Example Art'}).json()
    assert result['total']==1
    assert (result['items'][0]['knownProgramCount'],result['items'][0]['years'])==(2,[2027])


def test_fact_hydration_is_bounded_by_page_not_catalogue(postgres_engine,store,monkeypatch):
    body,review=source()
    records=[deepcopy(review['programs'][0])|dict(source_key=f'/synthetic/{i:04}',title=f'Synthetic scale {i:04}')
             for i in range(257)]
    review['programs']=records
    review['selection']=[dict(source_key=r['source_key']) for r in records]
    monkeypatch.setitem(EXTRACTORS,review['extractor_version'],lambda doc,scope:deepcopy(records))
    assert import_document(postgres_engine,review,body,store)['outcome']=='published'
    hydrated=[]
    def loaded(session,obj):
        if isinstance(obj,Fact):
            hydrated.append(obj.program_id)
    event.listen(Session,'loaded_as_persistent',loaded)
    try:
        for offset,expected in [(0,7),(252,5),(9999,0)]:
            hydrated.clear()
            with Session(postgres_engine) as db:
                page=program_page(db,offset=offset,limit=7)
                assert (page.total,len(page.items),page.years)==(257,expected,[2027])
                assert len(hydrated)<=expected
                assert page.next_offset==(7 if offset==0 else None)
    finally:
        event.remove(Session,'loaded_as_persistent',loaded)


@pytest.mark.parametrize('collision',['public-only','scope-only'])
def test_collisions_remain_global_when_request_filters_hide_the_rival(client,postgres_engine,store,collision):
    import_reviewed(postgres_engine)
    publish(postgres_engine,store)
    if collision=='public-only':
        publish(postgres_engine,store,'sgu')
    with Session(postgres_engine) as db:
        target=db.scalars(select(Fact).where(Fact.title=='Example Fashion')).one()
        rival=db.scalars(select(Fact).where(Fact.campaign_id!=target.campaign_id)).first() if collision=='public-only' else target
        revision=db.get(Revision,rival.revision_id)
        values={c.name:getattr(revision,c.name) for c in Revision.__table__.columns}
        fact={c.name:getattr(rival,c.name) for c in Fact.__table__.columns}
        target_id=target.public_id
        target_pid=target.program_id
    with postgres_engine.begin() as db:
        db.execute(insert(Document).values(id='filtered-rival',campaign_id=values['campaign_id'],source_namespace='synthetic-filtered-rival'))
        db.execute(insert(Revision).values(**(values|dict(id='filtered-rival-revision',document_id='filtered-rival',program_count=1))))
        db.execute(insert(Fact).values(**(fact|dict(revision_id='filtered-rival-revision',
            public_id=target_id if collision=='public-only' else 'different-public-id'))))
        db.execute(insert(Publication).values(document_id='filtered-rival',revision_id='filtered-rival-revision'))
    result=client.get(BASE+'/programs',params={'universityId':'miccedu-1766','year':2027,'q':'Fashion'}).json()
    assert result['items']==[] and result['total']==0
    assert client.get(BASE+'/programs/'+target_id).status_code==404
    rows=client.get(BASE+'/programs?limit=50').json()['items']
    assert all(r['programId']!=target_pid for r in rows)
    assert any(r['title']=='Example Art' for r in rows)


def test_explicit_programme_link_between_campaigns_is_not_a_duplicate(client,postgres_engine,store):
    publish(postgres_engine,store)
    with Session(postgres_engine) as db:
        fact=db.scalars(select(Fact).where(Fact.title=='Example Fashion')).one()
        revision=db.get(Revision,fact.revision_id)
        values={c.name:getattr(revision,c.name) for c in Revision.__table__.columns}
        item={c.name:getattr(fact,c.name) for c in Fact.__table__.columns}
        pid=fact.program_id
    cid=campaign_id('miccedu-1766',2026,'bachelor')
    with postgres_engine.begin() as db:
        db.execute(insert(Campaign).values(id=cid,university_id='miccedu-1766',year=2026,level='bachelor'))
        db.execute(insert(CampaignProgram).values(program_id=pid,campaign_id=cid,university_id='miccedu-1766',level='bachelor'))
        db.execute(insert(Document).values(id='explicit-continuity',campaign_id=cid,source_namespace='synthetic-continuity'))
        db.execute(insert(Revision).values(**(values|dict(id='continuity-revision',document_id='explicit-continuity',campaign_id=cid,program_count=1))))
        db.execute(insert(Fact).values(**(item|dict(revision_id='continuity-revision',campaign_id=cid,public_id='continuity-public-id'))))
        db.execute(insert(Publication).values(document_id='explicit-continuity',revision_id='continuity-revision'))
    page=client.get(BASE+'/programs',params={'q':'Fashion'}).json()
    assert page['total']==2 and page['years']==[2027,2026]
    assert {p['programId'] for p in page['items']}=={pid}
    assert {p['year'] for p in page['items']}=={2027,2026}
