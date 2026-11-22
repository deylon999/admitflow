"""Compare exact counts and publication costs on the owned scale database."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from threading import Barrier
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'backend'), str(ROOT / 'backend/tests')]

from sqlalchemy import text
from scripts.qa.benchmark_product_catalog import percentile
from scripts.qa.profile_catalog_http import fixture_engine

COUNT = "SELECT count(*) FROM program_catalog_read_facts WHERE eligible AND year=2027 AND "
CODE = '09.03.04'


def measure(operation, runs=50, warm=10):
    for _ in range(warm):
        operation()
    times = []
    for _ in range(runs):
        start = perf_counter()
        operation()
        times.append((perf_counter() - start) * 1000)
    return dict(p50=percentile(times, .50), p95=percentile(times, .95), samples=times)


def publish(connection, document, revision):
    rid = hashlib.md5(f'{document}:rev:{revision}'.encode()).hexdigest()
    connection.execute(text('UPDATE program_catalog_publications SET revision_id=:r WHERE document_id=:d'),
                       {'r': rid, 'd': document})


def write_trials(engine, documents, verify):
    target = documents[0]
    sequence = iter([1, 2] * 30)

    def replace():
        version = next(sequence)
        with engine.begin() as db:
            publish(db, target, version)
    result = dict(incremental=measure(replace))
    verify()

    # Do and roll back a real batch of existing revision replacements. It
    # measures maintenance, plus rollback, on both eligible-on/off transitions.
    batch = text("""UPDATE program_catalog_publications SET revision_id=md5(document_id || ':rev:1')
        WHERE document_id=ANY(:documents)""")
    result['rolledBackBatch'] = []
    for _ in range(3):
        start = perf_counter()
        with engine.connect() as db:
            assert db.execute(batch, {'documents': documents}).rowcount == len(documents)
            db.rollback()
        result['rolledBackBatch'].append((perf_counter()-start)*1000)
        verify()

    # Two writers modify disjoint documents in overlapping transactions. They
    # take the existing projection epoch lock; both committed results are checked.
    result['concurrentWriters'] = []
    for version in (1, 2):
        barrier = Barrier(2)
        def replace_concurrently(doc):
            barrier.wait(timeout=10)
            start = perf_counter()
            with engine.begin() as db:
                publish(db, doc, version)
            return (perf_counter()-start)*1000
        with ThreadPoolExecutor(max_workers=2) as threads:
            result['concurrentWriters'].append(list(threads.map(replace_concurrently, documents[:2])))
        verify()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--counter', action='store_true', help='Compare the installed candidate migration after its backfill')
    parser.add_argument('--batch-documents', type=int, default=50)
    args = parser.parse_args()
    runtime, engine = fixture_engine(json.loads(args.fixture.read_text(encoding='utf-8')))
    report = dict(variants={})
    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')

    try:
        with engine.connect() as db:
            documents = list(db.scalars(text('''SELECT d.id FROM program_catalog_documents d JOIN campaigns c
                ON c.id=d.campaign_id WHERE c.year=2027 ORDER BY d.id LIMIT :limit'''), {'limit': args.batch_documents}))
            if len(documents) < 2:
                raise ValueError('need two documents for the writer trial')
            report['batchDocuments'] = len(documents)
            report['postgresVersion'] = db.scalar(text('SHOW server_version'))
            source_sql = text(COUNT + "search_text LIKE '%' || :code || '%'")
            expected = db.scalar(source_sql, {'code': CODE})
            report['count'] = expected

        def verify():
            if args.counter:
                with engine.connect() as db:
                    actual = db.scalar(text('''SELECT COALESCE(sum(program_count),0) FROM program_catalog_read_code_totals
                                              WHERE code=:code AND year=2027'''), {'code': CODE})
                    assert actual == db.scalar(source_sql, {'code': CODE}) == expected

        def compare(name, query):
            with engine.connect() as db:
                def read_count():
                    assert db.scalar(query, {'code': CODE}) == expected
                report['variants'][name] = measure(read_count)
                report['variants'][name]['plan'] = db.execute(text('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+query.text),
                                                               {'code': CODE}).scalar()
            report['variants'][name]['writes'] = write_trials(engine, documents, verify)
            save()
            print(name, report['variants'][name]['p95'], flush=True)

        if args.counter:
            compare('counter', text('''SELECT COALESCE(sum(program_count),0) FROM program_catalog_read_code_totals
                                     WHERE code=:code AND year=2027'''))
        else:
            compare('strpos', text(COUNT + 'strpos(search_text,:code)>0'))
            start = perf_counter()
            with engine.begin() as db:
                db.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public'))
                db.execute(text('''CREATE INDEX bench_catalog_trgm ON program_catalog_read_facts
                    USING gin(search_text public.gin_trgm_ops) WHERE eligible'''))
                report['trigramIndexBytes'] = db.scalar(text("SELECT pg_relation_size('bench_catalog_trgm')"))
            report['trigramBuildSeconds'] = perf_counter()-start
            try:
                compare('trigram', source_sql)
                with engine.connect() as db:
                    db.execute(text('SET LOCAL enable_seqscan=off'))
                    report['forcedTrigramPlan'] = db.execute(text('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+source_sql.text),
                                                              {'code': CODE}).scalar()
                save()
            finally:
                with engine.begin() as db:
                    db.execute(text('DROP INDEX bench_catalog_trgm'))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
