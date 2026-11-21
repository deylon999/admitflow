"""Rehearse real reviewed programme import in an owned disposable PostgreSQL.

Requires original content-addressed HTML captured outside Git. Does not access
the working DATABASE_URL, applicant sources or production configuration.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import uvicorn
from app.admissions import CompetitionGroup, Program
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema
from app.national_coverage import national_coverage, with_checksum
from app.program_catalog_import import import_sources
from app.program_catalog_models import ProgramCatalogFact, ProgramCatalogPublication, ProgramCatalogRevision
from app.program_catalog_review import load_reviews
from app.sources.storage import RawStore
from pg_support import isolated_postgres
from postgres_runtime import disposable_postgres


def verify_browser(app):
    """Serve the owned published catalogue only while the targeted E2E runs."""
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        target = f'http://127.0.0.1:{listener.getsockname()[1]}'
        server = uvicorn.Server(uvicorn.Config(app, log_level='warning'))
        worker = threading.Thread(target=server.run, kwargs={'sockets':[listener]})
        worker.start()
        try:
            subprocess.run(['node', 'scripts/test.mjs', '--', '--grep', 'published admissions programme'],
                cwd=ROOT/'frontend', env={**os.environ, 'QA_API_TARGET':target, 'CATALOG_REAL_REHEARSAL':'1'}, check=True)
        finally:
            server.should_exit = True
            worker.join(timeout=15)
        if worker.is_alive():
            raise RuntimeError('Rehearsal API did not stop')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path, default=ROOT/'backend/var/research/program-catalog')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--browser', action='store_true')
    args=parser.parse_args(argv)
    report=dict(environment='owned-disposable-postgresql', generatedAt=datetime.now(timezone.utc).isoformat(),
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        publicApiExpanded=True)
    with disposable_postgres() as runtime, isolated_postgres(runtime.url()) as engine, tempfile.TemporaryDirectory(prefix='admitflow-program-proof-') as directory:
        upgrade_schema(engine)
        import_reviewed(engine)
        app = create_app(Settings(database_url=engine.url.render_as_string(hide_password=False), auto_create_schema=False))
        path = '/api/v1/catalog/programs'
        with TestClient(app) as client:
            def request(url):
                response = client.get(url)
                response.raise_for_status()
                return response.json()
            before = {p['id']:p for p in request(path)['items']}
            assert set(before) == {'sgu-2026-4588', 'sgu-2026-4576'}
            assert request(path+'?year=2027')['total'] == 0
            store=RawStore(Path(directory)/'raw')
            first=import_sources(engine,args.raw_directory,store)
            if not first['allSourcesSucceeded']:
                raise RuntimeError(json.dumps(first))
            second=import_sources(engine,args.raw_directory,store)
            assert all(item['outcome']=='unchanged' for item in second['items']), second
            for identifier, expected in before.items():
                assert request(f'{path}/{identifier}') == expected
            target = request(path+'?year=2027&universityId=miccedu-1766')
            assert target['total'] == 2
            fashion = next(p for p in target['items'] if p['title'] == 'Мода')
            proposal = json.loads((ROOT/'docs/sources/program-catalog/response-proposal.json').read_text(encoding='utf-8'))
            assert fashion == proposal, fashion
            assert request(f'{path}/{fashion["id"]}') == fashion
            assert request(path+'?year=2026')['total'] == 4
            assert request('/api/v1/catalog/universities/miccedu-1766')['knownProgramCount'] == 2
            report['apiExamples'] = {'legacySgu':before['sgu-2026-4588'], 'target2027':target}
        with Session(engine) as db:
            coverage = with_checksum(national_coverage(db))
            report['coverage'] = {key:coverage[key] for key in ('generatedAt','denominator','byYear','inputs')}
            report.update(postgresVersion=db.scalar(text('SHOW server_version')), schemaRevision=db.scalar(text('SELECT version_num FROM alembic_version')),
                internalDocumentPublications=db.scalar(select(func.count()).select_from(ProgramCatalogPublication)),
                canonicalPrograms=db.scalar(select(func.count()).select_from(Program)),
                programmeFacts=db.scalar(select(func.count()).select_from(ProgramCatalogFact)),
                legacyCompetitionGroups=db.scalar(select(func.count()).select_from(CompetitionGroup)),
                existingPublicPrograms=len(before), target2027PublicPrograms=target['total'])
            sources=[]
            for review,result in zip(load_reviews(),first['items']):
                revision=db.get(ProgramCatalogRevision,result['revisionId'])
                facts=db.scalars(select(ProgramCatalogFact).where(ProgramCatalogFact.revision_id==revision.id).order_by(ProgramCatalogFact.source_key)).all()
                sources.append(dict(key=review['key'],universityId=review['university_id'],year=review['year'],url=review['url'],
                    originalSha256=revision.original_sha256,reviewSha256=revision.review_sha256,normalizedSha256=revision.normalized_sha256,
                    fetchedAt=revision.fetched_at.isoformat(),checkedAt=revision.checked_at.isoformat(),completeness=revision.completeness,
                    documentType=revision.document_type,verificationStatus=revision.verification_status,
                    groupCount=revision.group_count,programmes=[dict(programId=f.program_id,publicId=f.public_id,title=f.title,code=f.code,
                        studyForm=f.study_form,funding=f.funding,category=f.category,seats=f.seats,admissionTotals=f.admission_totals) for f in facts]))
            report['sources']=sources
        report.update(firstImport=first, repeatImport=second, legacyPublicResponsesPreserved=True)
        if args.browser:
            verify_browser(app)
            report['realSourceBrowserJourney'] = 'passed'
    body=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(body,encoding='utf-8')
    else:
        print(body)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
