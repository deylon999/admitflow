#!/usr/bin/env python3
"""Serve anonymized SGU archive on disposable PostgreSQL; never fetch a website."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from postgres_runtime import disposable_postgres

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]
from app.database import make_engine
from app.migrations import upgrade_schema
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.registry import runtime_registry
from app.sources.storage import RawStore
from test_sgu_adapter import BINDING, KEY, response


def main():
    with tempfile.TemporaryDirectory(prefix='admitflow-source-e2e-') as folder, disposable_postgres() as runtime:
        os.environ['SOURCE_IDENTITY_KEY'] = KEY.hex()  # Deliberately synthetic fixture key.
        engine = make_engine(runtime.url())
        try:
            upgrade_schema(engine)
            registry = runtime_registry()
            register_sgu(engine, enable=True, registry=registry)
            raw = response()
            publish(engine, BINDING.source_id, registry.resolve(BINDING).parse(raw, BINDING), raw,
                    RawStore(Path(folder)/'raw'), registry=registry)
            if os.getenv('E2E_TWO_SOURCES')=='1':
                from app.sources.table_profiles import GUAP
                from app.sources.profile_registration import register_profile
                from test_table_family import fetch,binding
                from app.scenario_storage import enable_scenarios
                register_profile(engine,GUAP,enable=True,registry=registry)
                captured=fetch(GUAP)
                publish(engine,GUAP.source_id,registry.resolve(binding(GUAP)).parse(captured,binding(GUAP)),captured,RawStore(Path(folder)/'raw'),registry=registry)
                for source_id in (BINDING.source_id,GUAP.source_id):enable_scenarios(engine,source_id,registry=registry)
        finally:
            engine.dispose()
        control = os.getenv('E2E_SOURCE_CONTROL')
        if control:
            import json
            path=Path(control)
            if path.parent!=Path('/tmp'):raise ValueError('Fixture control must be under /tmp')
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'w') as stream:json.dump({'url':runtime.url(),'raw':str(Path(folder)/'raw'),'fixtureOnly':True},stream)
        env = {**os.environ, 'DATABASE_URL': runtime.url(), 'AUTO_CREATE_SCHEMA': 'false', 'RAW_STORE_PATH': str(Path(folder)/'raw')}
        child = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8013', '--no-access-log'], cwd=ROOT/'backend', env=env)
        def stop(*_):
            child.terminate()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            child.wait()
        finally:
            if control:Path(control).unlink(missing_ok=True)
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)


if __name__ == '__main__':
    main()
