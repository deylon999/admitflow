import os
from pathlib import Path
import subprocess
import sys

import pytest


def run_guard(tmp_path, source, url, required=True, extra=()):
    (tmp_path/'test_probe.py').write_text(source, encoding='utf-8')
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join([str(Path(__file__).parent), str(Path(__file__).parents[1])]), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    environment.pop('PYTEST_ADDOPTS', None)
    environment.pop('TEST_DATABASE_URL', None)
    if url is not None:
        environment['TEST_DATABASE_URL'] = url
    return subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'pg_guard', *( ['--require-postgres'] if required else []), *extra, str(tmp_path/'test_probe.py')], cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=15)


@pytest.mark.parametrize('url', [None, 'sqlite:///admitflow_test', 'postgresql://user:secret@localhost/production'])
def test_required_mode_rejects_missing_or_unsafe_configuration(tmp_path,url):
    result=run_guard(tmp_path,'def test_probe():\n    assert True\n',url)
    assert result.returncode==4
    assert 'secret' not in result.stdout+result.stderr


@pytest.mark.parametrize('source', [
    'def test_probe():\n    assert True\n',
    'import pytest\n@pytest.mark.postgres\ndef test_probe():\n    pytest.skip("unavailable")\n',
    'import pytest\n@pytest.fixture\ndef unavailable():\n    pytest.skip("unavailable")\n@pytest.mark.postgres\ndef test_probe(unavailable):\n    pass\n',
])
def test_required_mode_rejects_absent_and_skipped_cases(tmp_path,source):
    result=run_guard(tmp_path,source,'postgresql://user:secret@localhost/admitflow_test')
    assert result.returncode==1 and 'Required PostgreSQL checks' in result.stdout


def test_guard_accepts_completed_marker_and_local_optional_skip(tmp_path):
    # Synthetic marker case tests only plugin bookkeeping, never PG connectivity.
    result=run_guard(tmp_path,'import pytest\n@pytest.mark.postgres\ndef test_probe():\n    assert True\n','postgresql://user:secret@localhost/admitflow_test')
    assert result.returncode==0
    result=run_guard(tmp_path,'import pytest\n@pytest.mark.postgres\ndef test_probe():\n    pytest.skip("local only")\n',None,required=False)
    assert result.returncode==0 and '1 skipped' in result.stdout


def test_guard_refuses_filtered_native_case_and_teardown_skip(tmp_path):
    source='import pytest\n@pytest.mark.postgres\ndef test_first():\n    pass\n@pytest.mark.postgres\ndef test_second():\n    pass\n'
    result=run_guard(tmp_path,source,'postgresql://user:secret@localhost/admitflow_test',extra=('-k','first'))
    assert result.returncode==1 and 'Required PostgreSQL checks' in result.stdout
    source='import pytest\n@pytest.fixture\ndef skipped_teardown():\n    yield\n    pytest.skip("teardown unavailable")\n@pytest.mark.postgres\ndef test_probe(skipped_teardown):\n    pass\n'
    result=run_guard(tmp_path,source,'postgresql://user:secret@localhost/admitflow_test')
    assert result.returncode==1 and 'Required PostgreSQL checks' in result.stdout
