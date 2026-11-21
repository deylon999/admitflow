"""Write comparable PR 3 contracts from the backend selected by PYTHONPATH."""

import argparse
import hashlib
import inspect
import io
import json
from pathlib import Path
import tempfile

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateIndex, CreateTable


def write_snapshot(output, name, value):
    (output / f'{name}.json').write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8', newline='\n',
    )


def revision_graph(config):
    script = ScriptDirectory.from_config(config)
    return {
        'heads': script.get_heads(),
        'revisions': [
            {'revision': revision.revision, 'down_revision': revision.down_revision,
             'dependencies': revision.dependencies, 'branch_labels': sorted(revision.branch_labels),
             'sha256': hashlib.sha256(Path(revision.path).read_bytes()).hexdigest()}
            for revision in script.walk_revisions()
        ],
    }


def default_value(default):
    if default is None:
        return None
    value = default.arg
    if callable(value):
        return {'callable': inspect.unwrap(value).__qualname__}
    if default.is_clause_element:
        return {'sql': str(value)}
    return {'value': value}


def metadata_contract(base):
    dialects = {'postgresql': postgresql.dialect(), 'sqlite': sqlite.dialect()}
    tables = {}
    for name, table in sorted(base.metadata.tables.items()):
        tables[name] = {
            'columns': [
                {'name': column.name, 'key': column.key, 'nullable': column.nullable,
                 'default': default_value(column.default), 'onupdate': default_value(column.onupdate),
                 'types': {key: column.type.compile(dialect=dialect) for key, dialect in dialects.items()}}
                for column in table.columns
            ],
            # DDL includes server defaults, PKs, FK actions, checks, unique keys and names.
            'ddl': {key: str(CreateTable(table).compile(dialect=dialect)) for key, dialect in dialects.items()},
            'indexes': {
                key: sorted(str(CreateIndex(index).compile(dialect=dialect)) for index in table.indexes)
                for key, dialect in dialects.items()
            },
        }
    return {
        'tables': tables,
        'mappers': {
            mapper.class_.__qualname__: {
                'table': mapper.local_table.key,
                'attributes': sorted(mapper.attrs.keys()),
                'relationships': {
                    relation.key: {'target': relation.mapper.class_.__qualname__,
                                   'direction': relation.direction.name, 'join': str(relation.primaryjoin)}
                    for relation in mapper.relationships
                },
            }
            for mapper in base.registry.mappers
        },
    }


def dependency_contract(dependency):
    return {
        'call': getattr(dependency.call, '__qualname__', None),
        'name': dependency.name,
        'cache': dependency.use_cache,
        'dependencies': [dependency_contract(child) for child in dependency.dependencies],
    }


def routes_contract(app):
    for route in app.routes:
        if hasattr(route, 'effective_route_contexts'):
            # FastAPI can defer include_router expansion until it builds effective routes.
            for context in route.effective_route_contexts():
                yield route_contract(context)
        else:
            yield route_contract(route)


def route_contract(route):
    result = {'path': route.path, 'methods': sorted(route.methods or ()), 'name': route.name}
    if hasattr(route, 'dependant'):
        result.update(operation_id=route.operation_id, unique_id=route.unique_id,
                      dependencies=dependency_contract(route.dependant),
                      status_code=route.status_code, include_in_schema=route.include_in_schema)
    return result


def responses(app, *, enabled):
    headers = {'X-Requested-With': 'abiturient'}
    requests = [('GET', '/api/live', None, {}), ('GET', '/api/health', None, {}),
                ('GET', '/api/v1/auth/session', None, {}), ('GET', '/api/v1/auth/csrf', None, {}),
                ('POST', '/api/v1/auth/login', {}, {}),
                ('POST', '/api/v1/auth/login', {}, headers)]
    if enabled:
        requests.append(('POST', '/api/v1/auth/login', {'email': 'account@example.test', 'password': 'sample'}, headers))
    result = []
    with TestClient(app) as client:
        for method, path, body, request_headers in requests:
            response = client.request(method, path, json=body, headers=request_headers)
            result.append({
                'method': method, 'path': path, 'status': response.status_code, 'body': response.json(),
                'headers': {key: response.headers[key] for key in ('cache-control', 'retry-after', 'x-content-type-options')
                            if key in response.headers},
            })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Alembic loads its own models in a process that has not imported app.main.
    from app.database import Base

    config = Config('alembic.ini', output_buffer=io.StringIO())
    command.upgrade(config, 'head', sql=True)
    write_snapshot(args.output, 'alembic', revision_graph(config))
    write_snapshot(args.output, 'alembic-metadata', metadata_contract(Base))

    from app import account_dto
    from app.config import Settings
    from app.main import create_app

    write_snapshot(args.output, 'auth-dtos', {
        model.__name__: {mode: model.model_json_schema(mode=mode) for mode in ('validation', 'serialization')}
        for model in vars(account_dto).values()
        if isinstance(model, type) and issubclass(model, BaseModel) and model.__module__ == account_dto.__name__
    })
    for enabled in (False, True):
        mode = 'auth-on' if enabled else 'auth-off'
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(Settings(database_url=f'sqlite:///{directory}/snapshot.db',
                                      auth_enabled=enabled, auth_rate_key='fixture' * 5 if enabled else None))
            write_snapshot(args.output, f'{mode}-openapi', app.openapi())
            write_snapshot(args.output, f'{mode}-routes', list(routes_contract(app)))
            write_snapshot(args.output, f'{mode}-responses', responses(app, enabled=enabled))
    write_snapshot(args.output, 'app-metadata', metadata_contract(Base))


if __name__ == '__main__':
    main()
