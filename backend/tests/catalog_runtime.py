"""Owned ephemeral real API for browser tests. Only audited public metadata."""
from pathlib import Path
import os
import sys
import threading
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn
from app.catalog import seed_catalog
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema


if __name__ == '__main__':
    with TemporaryDirectory(prefix='admitflow-catalog-') as temporary:
        app = create_app(Settings(database_url=f'sqlite:///{Path(temporary) / "catalog.db"}', auto_create_schema=False))
        upgrade_schema(app.state.engine)
        seed_catalog(app.state.engine)
        import_reviewed(app.state.engine)
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=5303, log_level='warning'))
        if os.getenv('CATALOG_CONTROL_STDIN') == '1':
            # The owned Node runner can stop this process gracefully on Windows,
            # without taskkill/WMI or an HTTP shutdown endpoint in product code.
            def control():
                sys.stdin.readline()
                server.should_exit = True
            threading.Thread(target=control, daemon=True).start()
        server.run()
