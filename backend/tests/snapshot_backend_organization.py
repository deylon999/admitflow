"""Capture all app DTOs and representative HTTP responses from a selected checkout."""

import argparse
import importlib
import json
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
from pydantic import BaseModel

from snapshot_backend_contract import write_snapshot


def import_application():
    for file in sorted(Path('app').rglob('*.py')):
        path = file.parent if file.name == '__init__.py' else file.with_suffix('')
        importlib.import_module('.'.join(path.parts))


def dto_contract():
    pending = [BaseModel]
    seen = {BaseModel}
    schemas = {}
    while pending:
        for model in pending.pop().__subclasses__():
            if model in seen:
                continue
            seen.add(model)
            pending.append(model)
            if not model.__module__.startswith('app.') or model.__pydantic_generic_metadata__['origin']:
                continue
            schemas.setdefault(model.__qualname__, []).append({
                mode: model.model_json_schema(mode=mode) for mode in ('validation', 'serialization')
            })
    return {name: sorted(items, key=lambda item: json.dumps(item, sort_keys=True)) for name, items in schemas.items()}


def http_contract():
    from app.config import Settings
    from app.main import create_app

    identifier = '00000000-0000-0000-0000-000000000000'
    requests = [
        ('GET', '/api/v1/catalog/universities?limit=2'),
        ('GET', '/api/v1/catalog/programs?limit=2'),
        ('GET', '/api/v1/groups?limit=2'),
        ('GET', '/api/v1/universities?q=несуществующий-вуз'),
        ('GET', f'/api/v1/competitions/{identifier}'),
        ('GET', f'/api/v1/competitions/{identifier}/rows'),
        ('GET', f'/api/v1/competitions/{identifier}/summary'),
        ('GET', f'/api/v1/sources/{identifier}/status'),
        ('GET', f'/api/v1/subscriptions/{identifier}/history'),
        ('GET', f'/api/v1/subscriptions/{identifier}/scenario'),
        ('GET', '/api/v1/session'),
        ('GET', '/api/v1/watches'),
        ('GET', '/api/v1/export'),
        ('POST', '/api/v1/watches'),
        ('DELETE', '/api/v1/session'),
    ]
    result = []
    with tempfile.TemporaryDirectory() as directory:
        app = create_app(Settings(database_url=f'sqlite:///{directory}/extended-snapshot.db'))
        with TestClient(app) as client:
            for method, path in requests:
                response = client.request(method, path, headers={'X-Requested-With': 'abiturient'})
                result.append({
                    'method': method, 'path': path, 'status': response.status_code,
                    'body': response.json() if response.content else None,
                    'headers': {key: response.headers[key] for key in (
                        'cache-control', 'set-cookie', 'retry-after', 'x-content-type-options',
                    ) if key in response.headers},
                })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    import_application()
    write_snapshot(args.output, 'all-dtos', dto_contract())
    write_snapshot(args.output, 'domain-responses', http_contract())


if __name__ == '__main__':
    main()
