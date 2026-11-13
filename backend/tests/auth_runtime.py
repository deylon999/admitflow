"""Owned PostgreSQL browser runtime. Test-only mailbox and clock, never HTTP APIs."""
import json
import os
from pathlib import Path
import sys
import threading
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from app import account_api
from app.catalog import seed_catalog
from app.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema
from pg_support import isolated_postgres


def main():
    directory = Path(os.environ['AUTH_TEST_DIRECTORY']).resolve()
    if not directory.name.startswith('admitflow-auth-') or not directory.is_dir():
        raise RuntimeError('An owned private test directory is required.')
    mailbox = directory / 'mailbox.jsonl'
    mailbox.touch(mode=0o600, exist_ok=False)
    clock_file = directory / 'clock.json'
    clock_file.write_text('0')

    class TestClock:
        @staticmethod
        def now(_zone):
            return datetime.now(timezone.utc) + timedelta(seconds=int(clock_file.read_text()))
    account_api.datetime = TestClock

    class FileMailer:
        available = True
        lock = threading.Lock()

        def deliver(self, email, token, purpose):
            with self.lock:
                with mailbox.open('a') as output:
                    output.write(json.dumps(dict(email=email, token=token, purpose=purpose)) + '\n')
        def deliver_registration(self, email, token): self.deliver(email, token, 'verify')
        def deliver_verification(self, email, token): self.deliver(email, token, 'verify')
        def deliver_recovery(self, email, token): self.deliver(email, token, 'reset')

    with isolated_postgres(os.environ['TEST_DATABASE_URL']) as engine:
        upgrade_schema(engine)
        seed_catalog(engine)
        import_reviewed(engine)
        app = create_app(Settings(database_url=engine.url.render_as_string(hide_password=False),
                                  auto_create_schema=False, auth_enabled=True,
                                  auth_rate_key='isolated-browser-test-key-with-32-bytes',
                                  public_origin='http://127.0.0.1:5301'), registration_mailer=FileMailer())
        server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=5303, log_level='warning'))
        def control():
            sys.stdin.readline()
            server.should_exit = True
        threading.Thread(target=control, daemon=True).start()
        server.run()


if __name__ == '__main__':
    main()
