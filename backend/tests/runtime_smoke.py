"""Check a running local API using new guest sessions; delete only those sessions."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx


def require(condition):
    if not condition:
        raise RuntimeError('Runtime smoke failed; inspect the report.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--output', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'docs/evidence/t103-docker-smoke.json',
                        help='Report path; use a new path to preserve historical evidence')
    args = parser.parse_args()
    target = urlsplit(args.base_url)
    if (target.scheme != 'http' or target.hostname not in ('127.0.0.1', 'localhost')
            or target.username or target.password or target.path not in ('', '/')
            or target.query or target.fragment):
        parser.error('--base-url must be a local HTTP origin')
    base = args.base_url.rstrip('/')
    report = dict(recordedAt=datetime.now(timezone.utc).isoformat(), baseUrl=base,
                  scope='isolated HTTP smoke; database engine, image SHA, schema revision and legacy upgrade not attested',
                  checks=[], success=False)
    clients = []
    watch_id = None

    def client():
        result = httpx.Client(base_url=base, timeout=10, trust_env=False,
                              headers={'X-Requested-With': 'abiturient'})
        clients.append(result)
        return result

    def check(connection, method, path, expected, **kwargs):
        response = connection.request(method, path, **kwargs)
        report['checks'].append(dict(method=method, path=path.replace(watch_id, '{watchId}') if watch_id else path,
                                     status=response.status_code, expected=expected))
        require(response.status_code == expected)
        return response

    try:
        owner = client()
        ready = check(owner, 'GET', '/api/ready', 200)
        require(ready.json()['status'] == 'ok')
        report['reverseProxy'] = ready.headers.get('server')
        check(owner, 'GET', '/api/openapi.json', 200)
        check(owner, 'POST', '/api/v1/session', 204)
        require(check(owner, 'GET', '/api/v1/watches', 200).json() == [])
        values = dict(rank=120, seats=90, excluded=30, noConsent=16)
        body = dict(university='Migration smoke (synthetic)', title='T103 isolated smoke',
                    sourceUrl='https://example.org/list', values=values)
        key = str(uuid4())
        created = check(owner, 'POST', '/api/v1/watches', 201, json=body,
                        headers={'Idempotency-Key': key}).json()
        watch_id = created['id']
        require(created['latest']['calculation']['place'] == 74)
        replay = check(owner, 'POST', '/api/v1/watches', 201, json=body,
                       headers={'Idempotency-Key': key}).json()
        require(replay['id'] == watch_id)
        updated = check(owner, 'POST', f'/api/v1/watches/{watch_id}/snapshots', 201,
                        json=values | {'noConsent': 0}, headers={'Idempotency-Key': str(uuid4())}).json()
        require(updated['calculation']['place'] == 90)
        with httpx.Client(base_url=base, cookies=owner.cookies, timeout=10, trust_env=False) as reconnect:
            detail = check(reconnect, 'GET', f'/api/v1/watches/{watch_id}', 200).json()
            require([s['calculation']['place'] for s in detail['history']] == [90, 74])
            require(detail['latest']['id'] == updated['id'])
            exported = check(reconnect, 'GET', '/api/v1/export', 200).json()
            require(len(exported['watches']) == 1 and len(exported['watches'][0]['history']) == 2)
        other = client()
        check(other, 'POST', '/api/v1/session', 204)
        check(other, 'GET', f'/api/v1/watches/{watch_id}', 404)
        check(other, 'POST', f'/api/v1/watches/{watch_id}/snapshots', 404, json=values)
        check(other, 'DELETE', f'/api/v1/watches/{watch_id}', 404)
        require(check(other, 'GET', '/api/v1/watches', 200).json() == [])
        require(len(check(owner, 'GET', '/api/v1/watches', 200).json()) == 1)
        report['success'] = True
    finally:
        cleanup = []
        for connection in clients:
            try:
                cleanup.append(connection.delete('/api/v1/session').status_code)
            except httpx.HTTPError:
                cleanup.append('network_error')
            finally:
                connection.close()
        report['cleanupStatuses'] = cleanup
        report['success'] = report['success'] and cleanup == [204, 204]
        evidence = args.output
        evidence.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(success=report['success'], checks=len(report['checks']), cleanupStatuses=cleanup)))
    require(report['success'])


if __name__ == '__main__':
    main()
