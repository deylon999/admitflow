"""Verify 0010->0011 preserves every original column in a restored test DB.

Requires TEST_DATABASE_URL naming a disposable admitflow_test* PostgreSQL DB
already restored from an owned development backup. No dumps/values are output.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from sqlalchemy import MetaData,select,text
from sqlalchemy.engine import make_url
from app.database import make_engine
from app.migrations import upgrade_schema


def facts(connection,table,columns):
    rows=[json.dumps(list(row),ensure_ascii=True,sort_keys=True,default=str,separators=(',',':')) for row in connection.execute(select(*(table.c[name] for name in columns)))]
    return dict(rows=len(rows),sha256=hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/b16-migration-rehearsal.json');args=parser.parse_args()
    url=make_url(os.environ['TEST_DATABASE_URL'])
    if url.get_backend_name()!='postgresql' or not (url.database or '').startswith('admitflow_test'):
        raise ValueError('requires disposable PostgreSQL admitflow_test* database')
    engine=make_engine(url.render_as_string(hide_password=False));started=time.perf_counter()
    try:
        metadata=MetaData();metadata.reflect(bind=engine)
        with engine.connect() as db:
            assert db.scalar(text('SELECT version_num FROM alembic_version'))=='0010'
            columns={name:list(table.c.keys()) for name,table in metadata.tables.items() if name!='alembic_version'}
            before={name:facts(db,metadata.tables[name],names) for name,names in columns.items()}
        upgrade_schema(engine)
        after_metadata=MetaData();after_metadata.reflect(bind=engine)
        with engine.connect() as db:
            assert db.scalar(text('SELECT version_num FROM alembic_version'))=='0011'
            after={name:facts(db,after_metadata.tables[name],names) for name,names in columns.items()}
            assert before==after
            assert db.scalar(text('SELECT count(*) FROM universities WHERE search_name=\'\''))==0
            assert db.scalar(text('SELECT count(*) FROM competition_groups WHERE search_text=\'\''))==0
        result=dict(checkedAt=datetime.now(timezone.utc).isoformat(),fromRevision='0010',toRevision='0011',
            restoredDisposableCopy=True,allOriginalColumnsPreserved=True,tables=before,
            addedSearchColumnsPopulated=True,sourceSnapshots=before['source_snapshots']['rows'],
            candidateRows=before['candidate_entries']['rows'],seconds=round(time.perf_counter()-started,3),
            candidateValuesExported=False,userDatabaseChanged=False)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='tables'}))
    finally:engine.dispose()


if __name__=='__main__':main()
