from types import MappingProxyType
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.calculation import CalculationInput, calculate_versioned
from app.database import Snapshot
from test_api import create, start


def test_new_calculator_does_not_rewrite_saved_v1(client,application,monkeypatch):
    import app.calculation as calculation
    start(client);watch=create(client)
    def new_version(values):
        return calculation.calculate_manual_v1(values).model_copy(update={'place':999})
    monkeypatch.setattr(calculation,'MANUAL_CALCULATORS',MappingProxyType({**calculation.MANUAL_CALCULATORS,'manual-v2-test':new_version}))
    assert calculate_versioned(CalculationInput(**{'rank':120,'seats':90,'excluded':30,'no_consent':16}),'manual-v2-test').place==999
    result=client.get(f"/api/v1/watches/{watch['id']}/history").json()['items'][0]
    assert result==watch['latest'] and result['calculation']['place']==74
    with Session(application.state.engine) as db:
        saved=db.scalar(select(Snapshot));assert saved.model_version=='manual-v1' and saved.rank==120


def test_unknown_history_version_refuses_instead_of_silent_recalculation(client,application):
    start(client);watch=create(client)
    with Session(application.state.engine) as db:
        db.scalar(select(Snapshot)).model_version='unsupported-version';db.commit()
    result=client.get(f"/api/v1/watches/{watch['id']}/history")
    assert result.status_code==409 and 'не пересчитаны' in result.json()['detail']
    with Session(application.state.engine) as db:assert db.scalar(select(Snapshot)).model_version=='unsupported-version'
