"""Start the real local Compose stack, back up PostgreSQL and check persistence.

Python 3.10+ and running Docker Compose v2 are the only host dependencies.
Never runs down, deletes volumes, downgrades migrations or restores over a DB.
"""
import argparse
import hashlib
from http.cookiejar import CookieJar
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler, Request
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ['docker', 'compose', '-p', 'admitflow', '-f', str(ROOT / 'compose.yaml')]
PROTECTED = ('watches', 'snapshots', 'subscriptions', 'assessments',
             'source_snapshots', 'candidate_entries', 'published_snapshots',
             'change_events', 'operation_records', 'source_operations')


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, *, timeout=600, output=None):
    result = subprocess.run(command, cwd=ROOT, stdout=output or subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, check=False)
    # Do not echo command/env/database dumps, cookies or private response bodies.
    diagnostics = result.stderr
    if ('up' in command or 'alembic' in command) and result.returncode != 0:
        diagnostics += result.stdout or b''  # Build failures can be printed to stdout.
    require(result.returncode == 0,
            'Command failed: ' + ' '.join(arg if len(arg) < 80 else '<script/path>' for arg in command) +
            '\n' + diagnostics.decode('utf-8', errors='replace')[-4000:])
    return result.stdout or b''


def compose(*args, **kwargs):
    return run(COMPOSE + list(args), **kwargs)


def mounts(service):
    identifiers = compose('ps', '-a', '-q', service).decode().split()
    if not identifiers:
        return []
    containers = json.loads(run(['docker', 'inspect', *identifiers]))
    # `compose run` test/maintenance containers share the service label.
    regular = [c for c in containers if
               c['Config']['Labels'].get('com.docker.compose.oneoff', 'false').lower() == 'false']
    require(len(regular) == 1, 'Expected one regular container for ' + service)
    details = regular[0]
    return sorted((v['Name'], v['Destination']) for v in details['Mounts']
                  if v['Type'] == 'volume')


def pg(sql, db):
    return compose('exec', '-T', 'db', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
                   '-U', db['POSTGRES_USER'], '-d', db['POSTGRES_DB'], '-Atc', sql)


def history(db, columns=None):
    """Hash old columns only, including every old history row; no raw data report."""
    if columns is None:
        columns = {}
        for table in PROTECTED:
            names = pg("SELECT column_name FROM information_schema.columns "
                       "WHERE table_schema='public' AND table_name='" + table +
                       "' ORDER BY ordinal_position", db).decode().splitlines()
            if names:
                require(all(re.fullmatch(r'[a-z_]+', c) for c in names), 'Unexpected column')
                columns[table] = names
    result = {}
    for table, names in columns.items():
        fields = ','.join('"' + name + '"' for name in names)
        # COPY text is streamed through psql; only a digest and row count survive here.
        rows = pg('COPY (SELECT row_to_json(t)::text FROM (SELECT ' + fields +
                  ' FROM "' + table + '") t ORDER BY row_to_json(t)::text) TO STDOUT', db)
        result[table] = {'rows': int(pg('SELECT count(*) FROM "' + table + '"', db)),
                         'sha256': hashlib.sha256(rows).hexdigest()}
    return columns, result


def http(opener, base, method, path, expected=200, body=None):
    headers = {'X-Requested-With': 'abiturient', 'Origin': base}
    payload = None if body is None else json.dumps(body).encode()
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    request = Request(base + path, data=payload, headers=headers, method=method)
    try:
        response = opener.open(request, timeout=20)
    except HTTPError as error:
        response = error
    with response:
        require(response.status == expected, f'{method} {path.split("?")[0]}: unexpected HTTP status {response.status}')
        data = response.read()
        if not data:
            return None
        return json.loads(data) if 'application/json' in response.headers.get('Content-Type', '') else data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'test-results/local-start')
    parser.add_argument('--no-build', action='store_true', help='Reuse already built images')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid4().hex[:8]
    report = {'recordedAt': stamp, 'project': 'admitflow', 'success': False, 'checks': []}
    owner = None
    created = False
    base = ''
    try:
        run(['docker', 'info', '--format', '{{.ServerVersion}}'], timeout=30)
        config = json.loads(compose('config', '--format', 'json'))
        services = config['services']
        db = services['db']['environment']
        require(services['backend']['environment']['DATABASE_URL'].startswith('postgresql+psycopg://'),
                'Compose backend must use real PostgreSQL')
        require(services['backend']['environment']['AUTO_CREATE_SCHEMA'] == 'false', 'Explicit migrations required')
        port = services['frontend']['ports'][0]
        require(port['host_ip'] == '127.0.0.1', 'Local stack must bind only to loopback')
        base = 'http://127.0.0.1:' + str(port['published'])
        compose('up', '-d', '--wait', '--wait-timeout', '120', 'db')
        before_mounts = {'db': mounts('db'), 'backend': mounts('backend')}
        backup = output / (stamp + '-before-upgrade.dump')
        with backup.open('xb') as stream:
            compose('exec', '-T', 'db', 'pg_dump', '-U', db['POSTGRES_USER'], '-d', db['POSTGRES_DB'], '-Fc', output=stream)
        require(backup.stat().st_size > 0, 'Empty backup')
        # pg_restore --list reads the archive without modifying the database.
        with backup.open('rb') as stream:
            checked = subprocess.run(COMPOSE + ['exec', '-T', 'db', 'pg_restore', '--list'],
                                     cwd=ROOT, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        require(checked.returncode == 0, 'Backup archive could not be read')
        report['backup'] = str(backup)
        columns, baseline = history(db)
        report['historyBefore'] = baseline
        print('Backup verified; starting backend/frontend with existing volumes.', flush=True)
        up = ['up', '-d', '--wait', '--wait-timeout', '180']
        if not args.no_build:
            up.append('--build')
        compose(*up, 'backend', 'frontend', timeout=1200)
        for command in ('current', 'heads', 'check'):
            compose('exec', '-T', 'backend', 'python', '-m', 'alembic', command)
        schema = json.loads(compose('exec', '-T', 'backend', 'python', '-c', '''
import json
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from app.config import Settings
from app.database import make_engine
engine=make_engine(Settings.from_env().database_url)
assert engine.dialect.name=='postgresql'
with engine.connect() as connection:
 print(json.dumps(dict(dialect=engine.dialect.name,serverVersion=connection.dialect.server_version_info,
 current=list(MigrationContext.configure(connection).get_current_heads()),
 heads=ScriptDirectory.from_config(Config('alembic.ini')).get_heads())))
engine.dispose()
'''))
        require(schema['current'] == schema['heads'] and bool(schema['heads']), 'Migrations current != head')
        report['schema'] = schema
        compose('exec', '-T', 'backend', 'python', '-m', 'app.catalog_import')
        catalog_counts = pg('SELECT (SELECT count(*) FROM universities), (SELECT count(*) FROM campaigns), '
                            '(SELECT count(*) FROM competition_groups)', db)
        compose('exec', '-T', 'backend', 'python', '-m', 'app.catalog_import')
        require(catalog_counts == pg('SELECT (SELECT count(*) FROM universities), (SELECT count(*) FROM campaigns), '
                                     '(SELECT count(*) FROM competition_groups)', db), 'Catalog import not repeatable')
        require(history(db, columns)[1] == baseline, 'Existing history changed during migration/import')
        report['checks'].extend(['postgresql-current-equals-head', 'alembic-model-check', 'import-repeatable', 'old-history-preserved'])
        public = build_opener(ProxyHandler({}))
        require(http(public, base, 'GET', '/api/ready')['status'] == 'ok', 'API not ready')
        html = http(public, base, 'GET', '/')
        require(b'id="root"' in html, 'Frontend HTML missing React root')
        for asset in re.findall(rb'(?:src|href)="(/assets/[^\"]+)"', html):
            require(http(public, base, 'GET', asset.decode()), 'Empty frontend asset')
        for route in ('/universities', '/programs', '/app/watchlist'):
            require(b'id="root"' in http(public, base, 'GET', route), 'SPA route not served')
        universities = http(public, base, 'GET', '/api/v1/catalog/universities?limit=1')
        programs = http(public, base, 'GET', '/api/v1/catalog/programs?limit=2')
        require(universities['total'] > 0 and programs['total'] >= 2, 'Imported catalog is empty')
        for kind, page in [('universities', universities), ('programs', programs)]:
            for item in page['items']:
                detail = http(public, base, 'GET', '/api/v1/catalog/' + kind + '/' + item['id'])
                require(detail['id'] == item['id'], 'Catalog ID mismatch')
        http(public, base, 'GET', '/api/v1/catalog/programs/local-smoke-missing-' + uuid4().hex, 404)
        http(public, base, 'GET', '/api/v1/catalog/programs?year=-1', 422)
        report['catalog'] = {'universities': universities['total'], 'programs': programs['total']}
        report['checks'].append('frontend-assets-spa-and-catalog-api')
        # A fresh isolated guest owns this synthetic legacy history, never a real applicant.
        owner = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))
        http(owner, base, 'POST', '/api/v1/session', 204)
        created = True
        values = {'rank': 10, 'seats': 20, 'excluded': 0, 'noConsent': 0}
        watch = http(owner, base, 'POST', '/api/v1/watches', 201,
                     {'university': 'Local smoke (synthetic)', 'title': 'Private persistence check',
                      'sourceUrl': 'https://example.org/local-smoke', 'values': values})
        ident = watch['id']
        http(owner, base, 'POST', '/api/v1/watches/' + ident + '/snapshots', 201, dict(values, rank=11))
        detail_before = http(owner, base, 'GET', '/api/v1/watches/' + ident)
        require(len(detail_before['history']) == 2, 'Synthetic history was not written')
        persisted_mounts = {'db': mounts('db'), 'backend': mounts('backend')}
        for service, previous in before_mounts.items():
            require(not previous or persisted_mounts[service] == previous, 'Persistent volume replaced')
        print('PostgreSQL/import/API verified; recreating containers to check persistence.', flush=True)
        compose('up', '-d', '--no-build', '--force-recreate', '--wait', '--wait-timeout', '180', 'db', 'backend', 'frontend')
        require(persisted_mounts == {'db': mounts('db'), 'backend': mounts('backend')}, 'Volume identity changed on recreate')
        require(detail_before == http(owner, base, 'GET', '/api/v1/watches/' + ident), 'History changed across recreate')
        report['mounts'] = persisted_mounts
        report['checks'].append('two-snapshot-history-survives-container-recreate')
        http(owner, base, 'DELETE', '/api/v1/session', 204)
        created = False
        require(history(db, columns)[1] == baseline, 'Pre-existing history changed after smoke cleanup')
        report['historyAfter'] = history(db, columns)[1]
        report['checks'].append('only-smoke-guest-cleaned-existing-history-identical')
        report['url'] = base
        report['success'] = True
        print('PASS: full PostgreSQL stack running at ' + base, flush=True)
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        report['error'] = str(error)
        print('FAIL: ' + str(error), file=sys.stderr)
    finally:
        if created and owner:
            try:
                http(owner, base, 'DELETE', '/api/v1/session', 204)
                report['smokeGuestCleanup'] = True
            except Exception:
                report['smokeGuestCleanup'] = False
        path = output / (stamp + '.json')
        path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
        print('Report: ' + str(path), flush=True)
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
