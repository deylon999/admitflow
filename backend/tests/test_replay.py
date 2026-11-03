import pytest
from native_support import postgres_engine
from replay_case import replay_case
from test_sgu_adapter import KEY
pytestmark=pytest.mark.postgres


def test_both_real_formats_replay_changes_failures_and_explicit_absence(postgres_engine,tmp_path,monkeypatch):
    monkeypatch.setenv('SOURCE_IDENTITY_KEY',KEY.hex())
    report=replay_case(postgres_engine,tmp_path)
    assert len(report['steps'])==6 and report['externalHttpFetches']==0
    assert report['steps'][-1]['sources']['sgu-2026-4588']['result']['numbers'] is None
    assert report['steps'][-1]['sources']['guap-2026-math-contract']['result']['state']=='unsupported'
