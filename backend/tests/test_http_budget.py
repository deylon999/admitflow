import asyncio

import pytest

from app.http import MAX_REQUEST_BYTES, RequestBudgetMiddleware


def run_budget(chunks, *, headers=(), limit=10, stall=False):
    sent = []
    called = []

    async def app(scope, receive, send):
        called.append((await receive())['body'])
        await send({'type':'http.response.start','status':200,'headers':[]})

    async def receive():
        if stall:
            await asyncio.sleep(10)
        return chunks.pop(0)

    async def send(message):
        sent.append(message)

    middleware=RequestBudgetMiddleware(app,max_bytes=limit,timeout=0.02)
    asyncio.run(middleware({'type':'http','headers':headers},receive,send))
    return sent[0]['status'] if sent else None,called


def test_actual_bytes_bound_with_and_without_length():
    chunk=lambda body,more=False:dict(type='http.request',body=body,more_body=more)
    assert run_budget([chunk(b'123456',True),chunk(b'78901')])[0]==413
    assert run_budget([chunk(b'123456',True),chunk(b'78901')],headers=[(b'content-length',b'1')])[0]==413
    assert run_budget([],headers=[(b'content-length',b'11')])==(413,[])
    assert run_budget([],headers=[(b'content-length',b'-1')])[0]==400
    assert run_budget([chunk(b'ok')])==(200,[b'ok'])


def test_body_timeout_and_disconnect_never_call_application():
    assert run_budget([],stall=True)==(408,[])
    assert run_budget([{'type':'http.disconnect'}])==(None,[])


def test_oversized_request_is_rejected_by_real_api(client):
    response=client.post('/api/v1/calculate',content=b' '* (MAX_REQUEST_BYTES+1),headers={'Content-Type':'application/json'})
    assert response.status_code==413
    assert response.headers['cache-control']=='no-store'
    assert client.post('/api/v1/calculate',json={'rank':10,'seats':5,'excluded':0,'noConsent':0}).status_code==200


def test_ordinary_routes_accept_much_less_than_the_import_route(client):
    from app.http import DEFAULT_REQUEST_BYTES
    body=b'['+b'1,'*(DEFAULT_REQUEST_BYTES)+b'1]'
    assert client.post('/api/v1/calculate',content=body,headers={'content-type':'application/json'}).status_code==413
    response=client.post('/api/v1/import',content=body,headers={'content-type':'application/json','X-Requested-With':'abiturient'})
    assert response.status_code!=413


def test_repeated_content_type_cannot_bypass_json_checks(client):
    duplicate=b'{"rank":1,"rank":2,"seats":1,"excluded":0,"noConsent":0}'
    response=client.post('/api/v1/calculate',content=duplicate,headers=[('content-type','application/json'),('content-type','text/plain')])
    assert response.status_code==400
