#!/usr/bin/env python3
"""API for scripts/load_profile.py with one synthetic adapter. Never used outside the load stand."""
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'scripts')]
import uvicorn
from load_support import load_registry
import app.main as api
import app.sources.registry as registry

registry.runtime_registry=load_registry
application=api.create_app()

if __name__=='__main__':
    uvicorn.run('load_server:application',app_dir=str(ROOT/'scripts'),host='127.0.0.1',port=int(os.environ['LOAD_PORT']),workers=int(os.environ.get('LOAD_WORKERS','1')),access_log=False,log_level='warning')
