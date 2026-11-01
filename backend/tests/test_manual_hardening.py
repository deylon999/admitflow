import pytest
from test_api import start, WATCH, HEADERS


@pytest.mark.parametrize('field',['university','title','sourceUrl'])
@pytest.mark.parametrize('control',['\x00','\n','\x7f'])
def test_control_characters_are_rejected_before_normalization(client,field,control):
    start(client)
    response=client.post('/api/v1/watches',json=WATCH|{field:WATCH[field]+control},headers=HEADERS)
    assert response.status_code==422
    assert client.get('/api/v1/watches').json()==[]
