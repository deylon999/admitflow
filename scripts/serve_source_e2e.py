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
        finally:
            engine.dispose()
        env = {**os.environ, 'DATABASE_URL': runtime.url(), 'AUTO_CREATE_SCHEMA': 'false', 'RAW_STORE_PATH': str(Path(folder)/'raw')}
        child = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8013', '--no-access-log'], cwd=ROOT/'backend', env=env)
        def stop(*_):
            child.terminate()
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            child.wait()
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)


if __name__ == '__main__':
    main()
