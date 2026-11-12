"""Explicit archive-fixture test server in an owned, isolated PostgreSQL database."""
import hashlib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0, '/app')

name = os.environ['KAN212_DATABASE_NAME']
assert re.fullmatch(r'admitflow_test_kan212_[a-f0-9]{12}', name)
os.environ['DATABASE_URL'] = 'postgresql+psycopg://admitflow:admitflow@db:5432/' + name
os.environ['SOURCE_IDENTITY_KEY'] = b'synthetic-test-only-source-key-0001'.hex()
from app.main import create_app
from app.config import Settings
from app.catalog import seed_catalog
from app.catalog_import import import_reviewed
from app.migrations import upgrade_schema
from app.sources.pilots import register_sgu
from app.sources.publishing import publish
from app.sources.storage import RawStore
from app.sources.contracts import SourceBinding
from app.sources.fetcher import FetchResult
from app.sources.adapters.sgu2026 import SOURCE_ID, GROUP_ID, URL, VERSION
import uvicorn

app = create_app(Settings(database_url=os.environ['DATABASE_URL'], auto_create_schema=False))
assert app.state.engine.dialect.name == 'postgresql'
upgrade_schema(app.state.engine)
seed_catalog(app.state.engine)
import_reviewed(app.state.engine)
register_sgu(app.state.engine, enable=True, registry=app.state.source_registry)
binding = SourceBinding(SOURCE_ID, GROUP_ID, 2026, URL, 'www.sgu.ru', VERSION, 'archive', True)
body = Path('/fixture.html').read_bytes()
raw = FetchResult(URL, body, 'text/html', hashlib.sha256(body).hexdigest(), datetime(2026, 11, 3, 10, tzinfo=timezone.utc), 'utf-8')
parsed = app.state.source_registry.resolve(binding).parse(raw, binding)
with TemporaryDirectory(prefix='kan212-raw-') as temporary:
    publish(app.state.engine, SOURCE_ID, parsed, raw, RawStore(Path(temporary)), registry=app.state.source_registry)
    print('ISOLATED POSTGRESQL ARCHIVE FIXTURE READY', flush=True)
    uvicorn.run(app, host='0.0.0.0', port=5303, log_level='warning', access_log=False)
