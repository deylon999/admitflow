from test_api import create, start, VALUES, HEADERS


def test_history_total_is_all_records_not_page_size_and_is_owner_scoped(client):
    start(client)
    watch=create(client)
    client.post(f"/api/v1/watches/{watch['id']}/snapshots",json=VALUES,headers=HEADERS).raise_for_status()
    page=client.get(f"/api/v1/watches/{watch['id']}/history?limit=1").json()
    assert len(page['items'])==1 and page['total']==2 and page['nextCursor']
    older=client.get(f"/api/v1/watches/{watch['id']}/history?before={page['nextCursor']}").json()
    assert older['total']==2 and len(older['items'])==1 and older['nextCursor'] is None
    client.cookies.clear()
    start(client)
    assert client.get(f"/api/v1/watches/{watch['id']}/history").status_code==404
