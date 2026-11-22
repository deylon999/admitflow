"""Rehearse the batch CLI with real originals and an owned temporary PostgreSQL."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT/'backend'
sys.path[:0] = [str(BACKEND), str(BACKEND/'tests'), str(ROOT)]

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.catalog.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.operations.migrations import upgrade_schema
from app.catalog.national_coverage import national_coverage, with_checksum
from app.catalog.program_catalog_models import ProgramCatalogPublication
from pg_support import isolated_postgres
from scripts.ops.postgres_runtime import disposable_postgres


def run_cli(*args, database_url=None, expected_exit=0):
    env = dict(os.environ)
    if database_url is not None:
        env['DATABASE_URL'] = database_url
    result = subprocess.run([sys.executable, '-m', 'app.program_catalog_batch', *map(str, args)],
        cwd=BACKEND, env=env, stdout=subprocess.PIPE, text=True)
    body = json.loads(result.stdout)
    if result.returncode != expected_exit:
        raise RuntimeError(f'Unexpected CLI exit {result.returncode}: {body}')
    return {'exitCode': result.returncode, **body}


def proof(args):
    with disposable_postgres() as runtime, isolated_postgres(runtime.url()) as engine, TemporaryDirectory(prefix='admitflow-batch-proof-') as private_dir:
        upgrade_schema(engine)
        import_reviewed(engine)
        url = engine.url.render_as_string(hide_password=False)
        raw_store = Path(private_dir)/'published'
        offline = ['--reviewed-originals', args.originals.resolve(), '--raw-store', raw_store]
        captures = ['--captured', args.captured.resolve(), '--raw-store', raw_store]
        candidate_keys = ['--source','itmo-announcements-2027','--source','rudn-admission-2027','--source','sfu-admission-2027']
        before = run_cli('capture','--year',2027,'--work-dir',args.captured.resolve(),*candidate_keys)
        assert before['attemptedSources'] == 0 and all(x['reused'] for x in before['items'])
        before_post = run_cli('publish','--year',2027,*captures,*candidate_keys,database_url=url,expected_exit=1)
        assert all(x['outcome'] == 'review_required' for x in before_post['items'])
        hse = run_cli('publish','--year',2027,'--source','hse-design-2027',*candidate_keys,*offline,database_url=url,expected_exit=1)
        assert [x['outcome'] for x in hse['items']] == ['published']+['review_required']*3
        sgu = run_cli('publish','--year',2026,*offline,database_url=url)
        assert sgu['items'][0]['outcome'] == 'published'
        replay = run_cli('publish','--year',2027,'--source','hse-design-2027',*offline,database_url=url)
        assert replay['items'][0]['outcome'] == 'unchanged'
        assert replay['items'][0]['revisionId'] == hse['items'][0]['revisionId']
        app = create_app(Settings(database_url=url,auto_create_schema=False))
        with TestClient(app) as client:
            page = client.get('/api/v1/catalog/programs', params={'year':2027}).json()
            assert page['total'] == 2 and {p['universityId'] for p in page['items']} == {'miccedu-1766'}
            assert client.get('/api/v1/catalog/programs', params={'year':2026}).json()['total'] == 4
            assert client.get('/api/v1/catalog/programs/sgu-2026-4588').json()['seats'] == 16
        with Session(engine) as db:
            assert len(list(db.scalars(select(ProgramCatalogPublication.revision_id)))) == 2
            coverage = with_checksum(national_coverage(db))
        return dict(codeCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            generatedAt=datetime.now(timezone.utc).isoformat(), environment='isolated-disposable-postgresql',
            postgresVersion=engine.dialect.server_version_info, captureResume=before, candidatePublication=before_post,
            targetPublication=hse, archivePublication=sgu, repeat=replay, targetPublicPrograms=page['total'],
            coverage={k:coverage[k] for k in ('denominator','byYear','inputs')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',type=Path,default=BACKEND/'var/research/program-catalog')
    parser.add_argument('--captured',type=Path,default=BACKEND/'var/research/kan218-pr3')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=proof(args)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
