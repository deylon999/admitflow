"""Time catalogue requests in Uvicorn on an explicitly owned test fixture.

The instrumentation lives in the benchmark workers. Production routes,
configuration and response schemas do not depend on it.
"""
import argparse
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic, perf_counter, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend'), str(ROOT / 'backend/tests')]

import fastapi.routing
import httpx
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.catalog import product_catalog as catalog
from app.catalog.catalog_import import import_reviewed
from app.core.database import make_engine
from app.operations.migrations import upgrade_schema
from pg_support import isolated_postgres
from scripts.ops.postgres_runtime import PostgresRuntime, disposable_postgres
from scripts.qa.benchmark_catalog_serving import application as serving_application, server
from scripts.qa.benchmark_product_catalog import percentile, seed
from scripts.qa.compare_catalog_read_models import load_test

PATH = '/api/v1/catalog/programs'
request_timings = ContextVar('catalog_benchmark_timings', default=None)


def add_elapsed(timings, name, start):
    timings[name] = timings.get(name, 0) + (perf_counter() - start) * 1000


def timed(function, name):
    @wraps(function)
    def measured(*args, **kwargs):
        timings = request_timings.get()
        if timings is None:
            return function(*args, **kwargs)
        start = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            add_elapsed(timings, name, start)
    return measured


class ProfileHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get('path') != PATH:
            return await self.app(scope, receive, send)
        timings = dict(workerPid=os.getpid(), sqlMs=0, sqlCalls=0, checkoutMs=0, poolQueueMs=0, dtoMs=0,
                       serializeMs=0, endpointMs=0)
        token = request_timings.set(timings)
        start = perf_counter()

        async def profiled_send(message):
            if message['type'] == 'http.response.start':
                add_elapsed(timings, 'appMs', start)
                payload = {key: round(value, 3) for key, value in timings.items()}
                message['headers'].append((b'x-admitflow-bench-profile', json.dumps(payload).encode()))
            await send(message)

        try:
            await self.app(scope, receive, profiled_send)
        finally:
            request_timings.reset(token)


def application():
    app = serving_application()
    if os.environ.get('ADMITFLOW_BENCH_PROFILE') != '1':
        return app
    engine = app.state.engine
    engine.pool.connect = timed(engine.pool.connect, 'checkoutMs')
    # QueuePool calls Queue.get before ping or creating a connection. Record
    # queue wait separately; checkoutMs includes those additional costs.
    engine.pool._pool.get = timed(engine.pool._pool.get, 'poolQueueMs')

    @event.listens_for(engine, 'before_cursor_execute')
    def before(conn, cursor, statement, parameters, context, executemany):
        context.bench_cursor_started = perf_counter()

    @event.listens_for(engine, 'after_cursor_execute')
    def after(conn, cursor, statement, parameters, context, executemany):
        timings = request_timings.get()
        if timings is not None:
            timings['sqlCalls'] += 1
            add_elapsed(timings, 'sqlMs', context.bench_cursor_started)

    for model in (catalog.ProgramPage, catalog.CatalogProgram, catalog.CatalogCompetitionGroup,
                  catalog.Provenance, catalog.ExamRequirements):
        model.__init__ = timed(model.__init__, 'dtoMs')
    catalog.program_page = timed(catalog.program_page, 'endpointMs')
    serialize = fastapi.routing.serialize_response

    @wraps(serialize)
    async def profiled_serialize(*args, **kwargs):
        start = perf_counter()
        try:
            return await serialize(*args, **kwargs)
        finally:
            if (timings := request_timings.get()) is not None:
                add_elapsed(timings, 'serializeMs', start)

    fastapi.routing.serialize_response = profiled_serialize
    return ProfileHeaders(app)


def fixture_engine(meta):
    """Reject working database URLs and operate only inside the owned schema."""
    name, schema = meta['name'], meta['schema']
    if not re.fullmatch(r'admitflow-test-[0-9a-f]{32}', name) or not re.fullmatch(r'admitflow_test_[0-9a-f]{32}', schema):
        raise ValueError('expected a disposable AdmitFlow fixture')
    ports = json.loads(subprocess.check_output(['docker', 'inspect', '--format', '{{json .NetworkSettings.Ports}}', name]))
    if {'HostIp': '127.0.0.1', 'HostPort': meta['port']} not in ports.get('5432/tcp', []):
        raise ValueError('disposable fixture port mismatch')
    runtime = PostgresRuntime(name, meta['port'])
    url = make_url(runtime.url()).update_query_dict({'options': f'-csearch_path={schema}'})
    engine = make_engine(url.render_as_string(hide_password=False))
    with engine.connect() as db:
        if db.scalar(text('SELECT current_schema()')) != schema:
            raise ValueError('disposable fixture schema mismatch')
    return runtime, engine


@contextmanager
def linux_server(engine, runtime, image, log_path):
    """Bridge only the disposable PG and Uvicorn containers for a Linux run."""
    name = f'admitflow-load-{uuid4().hex}'
    network = name + '-net'
    subprocess.run(['docker','network','create',network], check=True, capture_output=True)
    attached = started = False
    try:
        subprocess.run(['docker','network','connect',network,runtime.name], check=True, capture_output=True)
        attached = True
        url = engine.url.set(host=runtime.name, port=5432).render_as_string(hide_password=False)
        subprocess.run(['docker','run','-d','--pull','never','--name',name,'--network',network,
            '-p','127.0.0.1::8000','--mount',f'type=bind,source={ROOT},target=/bench,readonly',
            '--workdir','/bench/backend','--env','PYTHONPATH=/bench/backend',
            '--env',f'DATABASE_URL={url}','--env','ENVIRONMENT=development','--env','AUTO_CREATE_SCHEMA=false',
            '--entrypoint','python',image,'-m','uvicorn','app.main:create_app','--factory',
            '--host','0.0.0.0','--port','8000','--workers','4','--no-access-log'], check=True, capture_output=True)
        started = True
        ports = json.loads(subprocess.check_output(['docker','inspect','--format','{{json .NetworkSettings.Ports}}',name]))
        port = ports['8000/tcp'][0]['HostPort']
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', trust_env=False, timeout=10,
                          limits=httpx.Limits(max_connections=50, max_keepalive_connections=50)) as client:
            deadline = monotonic() + 60
            while True:
                try:
                    if client.get(PATH, params={'limit':1}).status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if monotonic() >= deadline:
                    raise RuntimeError('owned Linux Uvicorn readiness timeout')
                sleep(.25)
            yield client
    finally:
        if started:
            with log_path.open('wb') as log:
                subprocess.run(['docker','logs',name], stdout=log, stderr=subprocess.STDOUT, check=False)
            subprocess.run(['docker','rm','--force',name], check=True, capture_output=True)
        if attached:
            subprocess.run(['docker','network','disconnect',network,runtime.name], check=True, capture_output=True)
        subprocess.run(['docker','network','rm',network], check=True, capture_output=True)


def cases(meta):
    fixture = meta['fixture']
    return dict(first={}, university={'university_id': fixture['sampleUniversity'], 'year': 2027},
                code={'q': '09.03.04', 'year': 2027},
                deep={'year': 2027, 'offset': max(0, fixture['targetYearPrograms'] - 12)},
                middle={'year': 2027, 'offset': fixture['targetYearPrograms'] // 2})


def digest(model):
    payload = json.dumps(model.model_dump(mode='json'), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def initialize_fixture(path, *, small=False):
    """Hold a disposable fixture for independent baseline/candidate processes."""
    stop = path.with_suffix('.stop')
    if path.exists() or stop.exists():
        raise ValueError('choose an unused fixture path')
    path.parent.mkdir(parents=True, exist_ok=True)
    with disposable_postgres(shm_size='1g') as runtime, isolated_postgres(runtime.url()) as engine:
        upgrade_schema(engine)
        import_reviewed(engine)
        start = perf_counter()
        fixture = seed(engine, heads=4 if small else 785, branches=1 if small else 215,
                       per_campaign=2 if small else 25, target_year_per_campaign=4 if small else 100)
        with engine.connect() as db:
            schema = db.scalar(text('SELECT current_schema()'))
        path.write_text(json.dumps(dict(name=runtime.name, port=runtime.port, schema=schema,
                                       fixture=fixture, seedSeconds=perf_counter()-start)), encoding='utf-8')
        print(f'Fixture ready: {path}', flush=True)
        deadline = monotonic() + 7200
        while not stop.exists() and monotonic() < deadline:
            sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--initialize', action='store_true')
    parser.add_argument('--small', action='store_true', help='Initialize a small fixture for benchmark smoke checks only')
    parser.add_argument('--cases', nargs='+', choices=['first','university','code','deep','middle'],
                        default=['first','university'])
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--docker-image', help='Run uninstrumented Uvicorn in an existing local Linux image')
    args = parser.parse_args()
    if args.initialize:
        return initialize_fixture(args.fixture, small=args.small)
    if not args.output or args.small:
        parser.error('running a profile requires --output')
    if args.profile and args.docker_image:
        parser.error('timing hooks run in the host workers only')
    meta = json.loads(args.fixture.read_text(encoding='utf-8'))
    runtime, engine = fixture_engine(meta)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                  dirty=bool(subprocess.check_output(['git','status','--porcelain'], text=True)),
                  fixture=meta['fixture'], workers=4, concurrency=50, instrumented=args.profile,
                  servingRuntime='linux-docker' if args.docker_image else sys.platform, cases={})
    try:
        with engine.connect() as db:
            report['postgresVersion'] = db.scalar(text('SHOW server_version'))
            report['postgresSettings'] = {key: db.scalar(text('SELECT current_setting(:key)'), {'key': key})
                for key in ('work_mem','shared_buffers','max_parallel_workers_per_gather','max_connections',
                            'hash_mem_multiplier','track_io_timing')}
        worker_log = args.output.with_suffix('.workers.log')
        if args.docker_image:
            report['servingImage'] = subprocess.check_output(
                ['docker', 'image', 'inspect', '--format', '{{.Id}}', args.docker_image], text=True).strip()
            instance = linux_server(engine, runtime, args.docker_image, worker_log)
        else:
            instance = server(engine, 4, worker_log, factory='scripts.qa.profile_catalog_http:application',
                              environment={'ADMITFLOW_BENCH_PROFILE': str(int(args.profile))})
        with instance as client:
            for name in args.cases:
                params = cases(meta)[name]
                with Session(engine) as db:
                    expected = catalog.source_program_page(db, **params)
                http_params = {('universityId' if key == 'university_id' else key): value for key,value in params.items()}
                warmups = warmup_errors = 0
                while warmups < 10:
                    try:
                        response = client.get(PATH, params=http_params)
                    except httpx.TransportError:
                        warmup_errors += 1
                        if warmup_errors > 2:
                            raise
                        continue
                    response.raise_for_status()
                    assert digest(catalog.ProgramPage.model_validate(response.json())) == digest(expected), name
                    warmups += 1
                result = load_test(client, http_params, 50, engine, runtime, 10)
                result['responseSha256'] = digest(expected)
                result['warmupTransportErrors'] = warmup_errors
                if args.profile:
                    profiles = [row['profile'] for row in result['samples'] if 'profile' in row]
                    result['profile'] = {k: dict(p50=percentile([p[k] for p in profiles], .50),
                                                 p95=percentile([p[k] for p in profiles], .95))
                                         for k in profiles[0] if k != 'workerPid'}
                    worker_ids = sorted({p['workerPid'] for p in profiles})
                    result['requestsByWorker'] = {pid: sum(p['workerPid']==pid for p in profiles) for pid in worker_ids}
                report['cases'][name] = result
                args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                print(name, round(result['p95'], 1), result['failures'], result.get('profile', {}), flush=True)
                assert result['totals'] == [expected.total]
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
