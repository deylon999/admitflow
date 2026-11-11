"""KAN-221: separate coverage layers on one denominator, visible problems, reproducible report."""
import json

import pytest

from app.accreditation_registry import load_registry
from app.catalog_import import import_reviewed
from app.national_coverage import TARGET, main, national_coverage, with_checksum


@pytest.fixture
def imported(client, application):
    import_reviewed(application.state.engine)
    return client


def layers(report):
    return {item['id']: item for item in report['layers']}


def test_layers_are_measured_separately_against_the_register(imported):
    report = imported.get('/api/v1/coverage/national').json()
    registry = load_registry()
    denominator = report['denominator']
    assert denominator['total'] == registry.denominator == 785 and denominator['datasetDate'] == '2026-11-10'
    assert denominator['civil'] + denominator['departmental'] == denominator['total']
    by_id = layers(report)
    assert list(by_id) == ['registry', 'programs', 'examRequirements', 'competitionLists']
    assert all(item['total'] == registry.denominator for item in by_id.values())
    assert by_id['registry']['covered'] == registry.matched_catalog_heads and by_id['registry']['targetMet'] is True
    # Reviewed programmes exist for a handful of universities only; the report must say so.
    assert 0 < by_id['programs']['covered'] < 0.05 * registry.denominator and by_id['programs']['targetMet'] is False
    # Reviewed entrance tests exist for SGU programmes only.
    assert by_id['examRequirements']['covered'] == 1 and by_id['examRequirements']['targetMet'] is False
    assert report['target'] == TARGET == 0.6
    years = {row['year']: row for row in report['byYear']}
    assert years and years[2026]['examRequirements'] == 1
    assert sum(r['total'] for r in report['regions']) == registry.denominator
    assert report['gaps']['headsWithoutPrograms'] == registry.denominator - by_id['programs']['covered']


def test_branches_are_not_counted_as_head_organisations(imported, application):
    from sqlalchemy.orm import Session
    from app.national_catalog import load_catalog
    from app.product_catalog import programs
    branches = {r.id for r in load_catalog().institutions if r.is_branch}
    with Session(application.state.engine) as db:
        report = national_coverage(db)
        branch_programs = sum(p.university_id in branches for p in programs(db))
    assert report['gaps']['branchProgramsNotCounted'] == branch_programs


def test_report_is_reproducible_and_has_no_private_fields(imported, application, tmp_path):
    from sqlalchemy.orm import Session
    with Session(application.state.engine) as db:
        first = with_checksum(national_coverage(db))
        second = with_checksum(national_coverage(db))
    assert first['inputs']['checksum'] == second['inputs']['checksum']
    assert first['inputs']['registrySha256'] == load_registry().sha256
    text = json.dumps(first, ensure_ascii=False, default=str)
    for private in ('candidateKey', 'publicCode', 'ownerHash', 'session'):
        assert private not in text


def test_cli_writes_the_same_report(imported, application, tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', str(application.state.engine.url.render_as_string(hide_password=False)))
    output = tmp_path/'coverage.json'
    assert main(['--output', str(output)]) == 0
    written = json.loads(output.read_text(encoding='utf-8'))
    api = imported.get('/api/v1/coverage/national').json()
    assert written['inputs']['checksum'] == api['inputs']['checksum']
    assert written['layers'] == api['layers']


def test_problem_sources_are_listed(imported, application):
    report = imported.get('/api/v1/coverage/national').json()
    states = report['sources']['byState']
    problems = sum(states.get(s, 0) for s in ('source_error', 'quarantined', 'stale'))
    assert len(report['sources']['problems']) == problems
    assert set(report['operations']) >= {'worker', 'jobs', 'status'}


def test_failed_source_is_visible_as_a_problem(source_engine, tmp_path):
    from sqlalchemy.orm import Session
    from app.jobs import enqueue
    from app.sources.fetcher import FetchError
    from app.sources.storage import RawStore
    from app.worker import run_once
    from source_helpers import raw, registry, seed_source
    seed_source(source_engine)
    at = raw().fetched_at
    enqueue(source_engine, 'source-1', now=at)
    def broken(*_, **__):
        raise FetchError('timeout', retry_after=60)
    run_once(source_engine, RawStore(tmp_path/'raw'), registry=registry(), allow_unattested=True, now=lambda: at, fetch=broken)
    with Session(source_engine) as db:
        report = national_coverage(db, now=at, registry_rules=registry())
    assert report['sources']['total'] == 1
    problem = report['sources']['problems'][0]
    assert problem['sourceId'] == 'source-1' and problem['state'] in ('source_error', 'stale', 'quarantined')
    assert report['operations']['jobs']['byState']
