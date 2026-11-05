from dataclasses import replace

from sqlalchemy.orm import Session

from app.admissions import CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot
from app.coverage import coverage
from app.sources.publishing import publish
from app.sources.registry import Registry
from app.sources.storage import RawStore
from source_helpers import NOW, parsed, raw, registry, seed_source


def test_public_catalog_does_not_imply_automatic_coverage(client):
    response=client.get('/api/v1/coverage')
    assert response.status_code==200 and 'set-cookie' not in response.headers
    data=response.json()
    assert data['catalogUniversities']==1257
    assert data['registryTotal']==1257 and data['registryEdition']==2025
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


def test_reviewed_imports_are_counted_from_published_scopes_without_fabricating_automation(source_engine,tmp_path):
    from app.sources.pilots import register_sgu
    from app.sources.profile_registration import register_profile
    from app.sources.table_profiles import GUAP
    from app.sources.registry import runtime_registry
    from app.scenario_storage import enable_scenarios
    from app.sources.publishing import utc
    from test_sgu_adapter import BINDING,KEY,response
    from test_table_family import fetch,binding
    import os
    from unittest.mock import patch
    with patch.dict(os.environ,{'SOURCE_IDENTITY_KEY':KEY.hex()}):reviewed=runtime_registry()
    register_sgu(source_engine,enable=True,registry=reviewed);register_profile(source_engine,GUAP,enable=True,registry=reviewed)
    with Session(source_engine) as db:
        before=coverage(db,registry=reviewed,now=NOW);assert before['registeredSources']==before['reviewedSources']==2 and before['importedSources']==0 and before['lastImportedAt'] is None
    for profile,raw_value,scope in ((None,response(),BINDING),(GUAP,fetch(GUAP),binding(GUAP))):
        publish(source_engine,scope.source_id,reviewed.resolve(scope).parse(raw_value,scope),raw_value,RawStore(tmp_path/'raw'),registry=reviewed)
        enable_scenarios(source_engine,scope.source_id,registry=reviewed)
    with Session(source_engine) as db:
        result=coverage(db,registry=reviewed,now=NOW)
        assert result['importedSources']==result['importedGroups']==result['importedUniversities']==result['archiveImportedGroups']==2
        assert result['importedRows']==1154 and result['conditionalGroups']==1
        assert result['automaticSources']==result['publishedGroups']==result['freshGroups']==0 and result['nationalTotal'] is None
        assert result['lastImportedAt']==max(response().fetched_at,fetch(GUAP).fetched_at)
        # Duplicate legacy/common proofs do not add scopes;held lastgood remains an archive.
        db.get(Source,BINDING.source_id).last_error_code='operator_quarantine';db.commit()
        assert coverage(db,registry=reviewed,now=NOW)==result
        db.get(Source,GUAP.source_id).enabled=False;db.commit()
        disabled=coverage(db,registry=reviewed,now=NOW);assert disabled['registeredSources']==2 and disabled['reviewedSources']==disabled['importedGroups']==1
        db.get(SourceSnapshot,db.get(PublishedSnapshot,BINDING.source_id).snapshot_id).complete=False;db.commit()
        assert coverage(db,registry=reviewed,now=NOW)['importedGroups']==0
