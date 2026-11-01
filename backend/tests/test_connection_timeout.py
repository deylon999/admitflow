import socket
import threading
import time

import pytest
from sqlalchemy.exc import OperationalError
from app.database import make_engine


def test_postgres_handshake_cannot_wait_indefinitely():
    listener=socket.socket()
    listener.bind(('127.0.0.1',0))
    listener.listen(1)
    listener.settimeout(8)
    accepted,release=threading.Event(),threading.Event()
    def stall():
        connection,_=listener.accept()
        try:
            accepted.set()
            release.wait(8)
        finally:
            connection.close()
    worker=threading.Thread(target=stall,daemon=True)
    worker.start()
    port=listener.getsockname()[1]
    engine=make_engine(f'postgresql+psycopg://test:test@127.0.0.1:{port}/admitflow_test?connect_timeout=1&sslmode=disable')
    started=time.monotonic()
    try:
        with pytest.raises(OperationalError): engine.connect()
        assert accepted.is_set() and time.monotonic()-started < 7
    finally:
        release.set()
        worker.join(2)
        listener.close()
        engine.dispose()


@pytest.mark.parametrize('value',['0','11','NaN'])
def test_invalid_connect_timeout_is_rejected_without_connecting(value):
    with pytest.raises(ValueError,match='connect_timeout'):
        make_engine(f'postgresql+psycopg://test:test@localhost/test?connect_timeout={value}')
