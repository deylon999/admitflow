#!/usr/bin/env python3
"""Replay two reviewed archive formats twice in owned PostgreSQL;no HTTP."""
import argparse
from datetime import datetime,timezone
import json,os,sys,tempfile
from pathlib import Path
from postgres_runtime import disposable_postgres
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
from app.database import make_engine
from app.migrations import upgrade_schema
from replay_case import replay_case
from test_sgu_adapter import KEY


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();os.environ['SOURCE_IDENTITY_KEY']=KEY.hex()
    with tempfile.TemporaryDirectory(prefix='admitflow-replay-') as folder,disposable_postgres() as runtime:
        reports=[]
        for index in range(2):
            name='admitflow_test_native' if index==0 else 'admitflow_test_replay_two'
            if index:runtime.command('createdb','-U','admitflow',name,check=True,capture_output=True)
            engine=make_engine(runtime.url(name))
            try:upgrade_schema(engine);reports.append(replay_case(engine,Path(folder)/str(index)))
            finally:engine.dispose()
    if reports[0]!=reports[1]:raise RuntimeError('Semantic replay differs;no row/identifier details emitted')
    result={'recordedAt':datetime.now(timezone.utc).isoformat(),'success':True,'runs':2,'identicalSemanticOutcomes':True,'cleanup':True,**reports[0]}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'success':True,'runs':2,'steps':len(result['steps']),'identicalSemanticOutcomes':True,'externalHttpFetches':0,'cleanup':True}))


if __name__=='__main__':main()
