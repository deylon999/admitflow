import importlib
import pickle
import subprocess
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.mark.parametrize('legacy_first', [True, False])
def test_auth_imports_share_modules_in_a_fresh_process(legacy_first):
    # conftest imports app.main, so either real import order needs a new process.
    subprocess.run([sys.executable, '-c', '''
import importlib
import sys

first, second = ('app', 'app.auth') if sys.argv[1] == 'True' else ('app.auth', 'app')
for name in ('accounts', 'account_security', 'account_mail', 'account_api'):
    module = importlib.import_module(f'{first}.{name}')
    assert importlib.import_module(f'{second}.{name}') is module
    assert getattr(importlib.import_module('app'), name) is module
    assert getattr(importlib.import_module('app.auth'), name) is module

from app import accounts
from app.database import Base
assert accounts.AccountUser.__table__ is Base.metadata.tables['account_users']
assert sum(mapper.class_ is accounts.AccountUser for mapper in Base.registry.mappers) == 1
''', str(legacy_first)], check=True, capture_output=True, text=True)


@pytest.mark.parametrize(('module', 'symbol'), [
    ('account_api', 'AuthProblem'),
    ('accounts', 'AccountUser'),
    ('account_security', 'PasswordCheck'),
    ('account_mail', 'MailDeliveryError'),
])
def test_pickle_global_refs_resolve_through_legacy_path(module, symbol):
    canonical = getattr(importlib.import_module(f'app.auth.{module}'), symbol)
    legacy_global = f'capp.{module}\n{symbol}\n.'.encode('ascii')
    assert pickle.loads(legacy_global) is canonical
    assert pickle.loads(pickle.dumps(canonical)) is canonical


def test_legacy_string_patch_reaches_registered_route(tmp_path):
    from app.auth.account_api import AuthProblem

    settings = Settings(database_url=f'sqlite:///{tmp_path / "auth.db"}',
                        auth_enabled=True, auth_rate_key='fixture' * 5)
    with TestClient(create_app(settings)) as client:
        with patch('app.account_api.current_account', side_effect=AuthProblem(401, 'patched', 'fixture')) as current:
            response = client.get('/api/v1/auth/session')
        assert response.status_code == 401
        assert response.json() == {'code': 'patched', 'detail': 'fixture'}
        current.assert_called_once()
