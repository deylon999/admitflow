import json
import pytest
from app.national_catalog import DEFAULT_PATH,import_snapshot,load_catalog,parse_snapshot


def test_real_reference_catalog_preserves_known_identities_and_separates_branches():
    result=load_catalog()
    assert len(result.institutions)==1257
    assert sum(row.is_branch for row in result.institutions)==521
    by_id={row.registry_id:row for row in result.institutions}
    assert by_id['258'].id=='sgu-saratov'
    assert by_id['1715'].id=='sgups-novosibirsk'
    assert by_id['243'].id=='guap-spb'
    assert len({row.id for row in result.institutions})==1257
    assert by_id['10000950'].is_branch and by_id['10000950'].id!='guap-spb'


@pytest.mark.parametrize('damage',['duplicate','count','branch','url','timestamp','national','parent'])
def test_invalid_import_leaves_previous_artifact_unchanged(tmp_path,damage):
    data=json.loads(DEFAULT_PATH.read_bytes())
    if damage=='duplicate':data['institutions'][1]['registryId']=data['institutions'][0]['registryId']
    elif damage=='count':data['recordCount']-=1
    elif damage=='branch':data['branchCount']-=1
    elif damage=='url':data['institutions'][0]['officialUrl']='javascript:alert(1)'
    elif damage=='timestamp':data['capturedAt']='2026-11-05T00:00:00'
    elif damage=='national':data['nationalTotal']=1257
    elif damage=='parent':data['institutions'][0]['parentRegistryId']=data['institutions'][0]['registryId']
    source=tmp_path/'new.json';target=tmp_path/'catalog.json'
    source.write_text(json.dumps(data),encoding='utf-8');target.write_bytes(b'previous')
    with pytest.raises(ValueError):import_snapshot(source,target)
    assert target.read_bytes()==b'previous'


def test_repeat_import_has_identical_bytes_and_no_duplicate_records(tmp_path):
    target=tmp_path/'catalog.json'
    first=import_snapshot(DEFAULT_PATH,target)
    second=import_snapshot(DEFAULT_PATH,target)
    assert first.sha256==second.sha256
    assert target.read_bytes()==DEFAULT_PATH.read_bytes()
    assert len(second.institutions)==len({row.id for row in second.institutions})
