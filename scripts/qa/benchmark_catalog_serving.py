"""Owned PG serving/write benchmark; synthetic fixtures, no production settings.

Measure real loopback HTTP separately from in-process TestClient contention.
One and four Uvicorn worker processes use the unchanged application/pool policy.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend'), str(ROOT / 'backend/tests')]

import httpx
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from app.catalog.product_catalog import ProgramPage, source_program_page
from app.catalog.catalog_import import import_reviewed
from app.config import Settings
from app.main import create_app
from app.migrations import upgrade_schema
from pg_support import isolated_postgres
from scripts.ops.postgres_runtime import disposable_postgres
from scripts.qa.benchmark_product_catalog import measure, percentile, seed
from scripts.qa.compare_catalog_read_models import load_test, pg_stats


def application():
    # Only the benchmark child receives this task-specific URL. The factory
    # never consumes a user's working DATABASE_URL or changes production config.
    return create_app(Settings(database_url=os.environ['ADMITFLOW_BENCH_DATABASE'], auto_create_schema=False))


@contextmanager
def server(engine, workers, log_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, ADMITFLOW_BENCH_DATABASE=engine.url.render_as_string(hide_password=False))
    env['PYTHONPATH'] = os.pathsep.join([str(ROOT), str(ROOT / 'backend')])
    with log_path.open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, '-m', 'uvicorn',
            'scripts.qa.benchmark_catalog_serving:application', '--factory',
            '--host', '127.0.0.1', '--port', str(port), '--workers', str(workers), '--no-access-log'],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            start_new_session=os.name != 'nt')
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False,
                    timeout=60, limits=httpx.Limits(max_connections=50, max_keepalive_connections=50)) as client:
                deadline = time.monotonic() + 60
                while True:
                    if proc.poll() is not None:
                        raise RuntimeError('owned Uvicorn exited; see serving log')
                    try:
                        if client.get('/api/v1/catalog/programs', params={'limit': 1}).status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError('owned Uvicorn readiness timeout')
                    time.sleep(.25)
                yield client
        finally:
            if proc.poll() is None:
                if os.name == 'nt':
                    # PID is the Popen-owned process; /T stops only its workers.
                    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                        check=True, stdout=subprocess.DEVNULL)
                else:
                    import signal
                    os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', nargs='+', type=int, choices=[1, 4], default=[1, 4])
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(sourceCommit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
        platform=platform.platform(), python=platform.python_version(), logicalCPUs=os.cpu_count(),
        synthetic=True, serving={}, facade={})
    def save():
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with disposable_postgres(shm_size='1g') as runtime, isolated_postgres(runtime.url()) as engine:
        upgrade_schema(engine)
        import_reviewed(engine)
        timings = []
        def before(conn, cursor, sql, params, context, many):
            context.benchmark_started = time.perf_counter()
        def after(conn, cursor, sql, params, context, many):
            timings.append(dict(sql=sql, seconds=time.perf_counter() - context.benchmark_started))
        event.listen(engine, 'before_cursor_execute', before)
        event.listen(engine, 'after_cursor_execute', after)
        try:
            started = time.perf_counter()
            report['fixture'] = seed(engine, target_year_per_campaign=100)
            report['seedSeconds'] = time.perf_counter() - started
        finally:
            event.remove(engine, 'before_cursor_execute', before)
            event.remove(engine, 'after_cursor_execute', after)
        report['seedStatements'] = timings
        print('Seed seconds', report['seedSeconds'], flush=True)
        with engine.connect() as db:
            report['postgresVersion'] = db.scalar(text('SHOW server_version'))
            report['settings'] = {key: db.scalar(text('SELECT current_setting(:key)'), {'key': key}) for key in
                ['work_mem', 'shared_buffers', 'max_parallel_workers_per_gather', 'max_connections', 'track_io_timing']}
            report['postgresHardware'] = runtime.command('sh', '-c', 'nproc; head -20 /proc/cpuinfo; cat /sys/fs/cgroup/memory.max',
                capture_output=True, text=True, check=True).stdout
            report['relationBytes'] = dict(db.execute(text("SELECT relname, pg_total_relation_size(oid) FROM pg_class WHERE relnamespace=current_schema()::regnamespace AND relkind='r' AND relname LIKE 'program_catalog%'")).all())
            document = db.scalar(text("SELECT d.id FROM program_catalog_documents d JOIN campaigns c ON c.id=d.campaign_id WHERE c.year=2027 ORDER BY d.id LIMIT 1"))
        # Fifty committed 100-program revision replacements. All facts preexist;
        # the last replacement restores v2, preserving the oracle fixture.
        writes = []
        for i in range(50):
            revision = hashlib.md5(f'{document}:rev:{1 if i % 2 == 0 else 2}'.encode()).hexdigest()
            started = time.perf_counter()
            with engine.begin() as db:
                db.execute(text('UPDATE program_catalog_publications SET revision_id=:revision WHERE document_id=:document'),
                    {'revision': revision, 'document': document})
            writes.append((time.perf_counter() - started) * 1000)
        report['incrementalPublicationMs'] = dict(samples=writes, p95=percentile(writes, .95))
        # Query planner statistics and visibility maps are left as obtained
        # after writes; do not VACUUM away the cost of recent publication.
        cases = dict(first={}, university={'university_id': report['fixture']['sampleUniversity'], 'year': 2027},
            code={'q': '09.03.04', 'year': 2027}, deep={'year': 2027, 'offset': 99988})
        oracle = {}
        for name, params in cases.items():
            with Session(engine) as db:
                value = source_program_page(db, **params)
            oracle[name] = hashlib.sha256(json.dumps(value.model_dump(mode='json'), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            report['facade'][name] = measure(engine, params, 50, 10000)
            assert report['facade'][name]['responseSha256'] == oracle[name]
        report['oracle'] = oracle
        save()
        for workers in args.workers:
            report['serving'][str(workers)] = {}
            with server(engine, workers, args.output.with_suffix(f'.workers-{workers}.log')) as client:
                for name, params in cases.items():
                    http_params = {('universityId' if k == 'university_id' else k): v for k, v in params.items()}
                    for _ in range(10):
                        response = client.get('/api/v1/catalog/programs', params=http_params)
                        response.raise_for_status()
                    value = ProgramPage.model_validate(response.json())
                    digest = hashlib.sha256(json.dumps(value.model_dump(mode='json'), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                    assert digest == oracle[name], (workers, name, 'HTTP/source mismatch')
                    print('HTTP workers', workers, name, flush=True)
                    report['serving'][str(workers)][name] = [load_test(client, http_params, n, engine, runtime, 10)
                        for n in (1, 10, 25, 50)]
                    save()
        report['finalPostgresStats'] = pg_stats(engine)
        save()


if __name__ == '__main__':
    main()
