from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.database import Snapshot
from test_api import create, start


def test_twenty_watch_reads_use_bounded_selects_and_keep_tied_order(client,application):
    start(client)
    watches=[create(client) for _ in range(20)]
    watch=watches[0]
    with Session(application.state.engine) as db:
        db.add(Snapshot(id='ffffffff-ffff-ffff-ffff-ffffffffffff',watch_id=watch['id'],captured_at=datetime.fromisoformat(watch['latest']['capturedAt']),rank=130,seats=90,excluded=30,no_consent=16))
        db.commit()
    queries=[]
    def record(_,__,statement,*args):
        if statement.lstrip().upper().startswith('SELECT'): queries.append(statement)
    event.listen(application.state.engine,'before_cursor_execute',record)
    try:
        response=client.get('/api/v1/watches')
        assert response.status_code==200 and len(response.json())==20
        assert len(queries)<=3
        assert next(row for row in response.json() if row['id']==watch['id'])['latest']['calculation']['place']==84
        queries.clear()
        exported=client.get('/api/v1/export')
        assert exported.status_code==200 and len(queries)<=3
        item=next(row for row in exported.json()['watches'] if row['id']==watch['id'])
        assert len(item['history'])==2 and item['history'][0]['id'].startswith('ffffffff')
    finally:
        event.remove(application.state.engine,'before_cursor_execute',record)
