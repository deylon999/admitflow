from dataclasses import replace

from sqlalchemy.orm import Session

from app.admissions import CompetitionGroup, Source, SourceSnapshot
from app.coverage import coverage
from app.sources.publishing import publish
from app.sources.registry import Registry
from app.sources.storage import RawStore
from source_helpers import NOW, parsed, raw, registry, seed_source


def test_public_catalog_does_not_imply_automatic_coverage(client):
    response=client.get('/api/v1/coverage')
    assert response.status_code==200 and 'set-cookie' not in response.headers
    data=response.json()
    assert data['catalogUniversities']==2
    assert data['automaticSources']==data['publishedGroups']==data['freshGroups']==0
    assert data['nationalTotal'] is None


def test_only_attested_enabled_groups_with_rules_count_as_automatic(source_engine,tmp_path):
    seed_source(source_engine)
    from source_helpers import synthetic_attestation
    attested=Registry((replace(registry()._adapters['synthetic-v1'],attested=True,attestation=synthetic_attestation()),))
    published=publish(source_engine,'source-1',parsed(),raw(),RawStore(tmp_path/'raw'),registry=attested)
    with Session(source_engine) as db:
        assert coverage(db,registry=attested,now=NOW)['automaticSources']==0
        group=db.get(CompetitionGroup,'group-1')
        group.coverage='automatic'
        group.rules_version='synthetic-rules'
        db.commit()
        result=coverage(db,registry=attested,now=NOW)
        assert result['automaticSources']==result['publishedGroups']==result['archiveGroups']==1
        assert result['freshGroups']==0
        db.get(SourceSnapshot,published).complete=False
        db.commit()
        assert coverage(db,registry=attested,now=NOW)['publishedGroups']==0
        db.get(Source,'source-1').enabled=False
        db.commit()
        assert coverage(db,registry=attested,now=NOW)['automaticSources']==0
        assert coverage(db,now=NOW)['automaticSources']==0
