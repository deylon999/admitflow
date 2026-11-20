"""Rehearse real reviewed programme import in an owned disposable PostgreSQL.

Requires original content-addressed HTML captured outside Git. Does not access
the working DATABASE_URL, applicant sources or production configuration.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from app.admissions import CompetitionGroup, Program
from app.catalog_import import import_reviewed
from app.migrations import upgrade_schema
from app.product_catalog import programs
from app.program_catalog_import import import_sources
from app.program_catalog_models import ProgramCatalogFact, ProgramCatalogPublication, ProgramCatalogRevision
from app.program_catalog_review import load_reviews
from app.sources.storage import RawStore
from pg_support import isolated_postgres
from postgres_runtime import disposable_postgres


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path, default=ROOT/'backend/var/research/program-catalog')
    parser.add_argument('--output', type=Path)
    args=parser.parse_args(argv)
    report=dict(environment='owned-disposable-postgresql', generatedAt=datetime.now(timezone.utc).isoformat(),
        sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        publicApiExpanded=False, pendingContractTask='T327')
    with disposable_postgres() as runtime, isolated_postgres(runtime.url()) as engine, tempfile.TemporaryDirectory(prefix='admitflow-program-proof-') as directory:
        upgrade_schema(engine)
        import_reviewed(engine)
        with Session(engine) as db:
            before={p.id:p.model_dump(mode='json') for p in programs(db)}
        store=RawStore(Path(directory)/'raw')
        first=import_sources(engine,args.raw_directory,store)
        if not first['allSourcesSucceeded']:
            raise RuntimeError(json.dumps(first))
        second=import_sources(engine,args.raw_directory,store)
        assert all(item['outcome']=='unchanged' for item in second['items']), second
        with Session(engine) as db:
            assert {p.id:p.model_dump(mode='json') for p in programs(db)}==before
            report.update(postgresVersion=db.scalar(text('SHOW server_version')), schemaRevision=db.scalar(text('SELECT version_num FROM alembic_version')),
                internalDocumentPublications=db.scalar(select(func.count()).select_from(ProgramCatalogPublication)),
                canonicalPrograms=db.scalar(select(func.count()).select_from(Program)),
                programmeFacts=db.scalar(select(func.count()).select_from(ProgramCatalogFact)),
                legacyCompetitionGroups=db.scalar(select(func.count()).select_from(CompetitionGroup)),
                existingPublicPrograms=len(before), target2027PublicPrograms=sum(p['year']==2027 for p in before.values()))
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
    body=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(body,encoding='utf-8')
    else:
        print(body)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
