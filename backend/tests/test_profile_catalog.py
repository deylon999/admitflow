import copy
import hashlib
import json
from pathlib import Path
import pytest
from app.sources.profile_catalog import publish_profile_data,read_profile_data
from app.sources.table_profiles import PROFILES,load_profiles

ROOT=Path(__file__).resolve().parents[2]
LEGACY=ROOT/'backend/app/sources/profiles/reviewed.json'


def data():return json.loads(LEGACY.read_text(encoding='utf-8'))['profiles']


def synthetic(number):
    value=copy.deepcopy(data()['sgu-2026-4588']);name=f'synthetic-{number:05d}'
    value.update(source_id=name,group_id=name,url=f'https://fixtures.invalid/scope-{number}')
    value['proof'].update(source_url=value['url'],passport='backend/tests/fixtures/synthetic-passport.md')
    return name,value


def test_legacy_profiles_and_history_proofs_survive_sharding_exactly(tmp_path):
    legacy=load_profiles(LEGACY)
    manifest=publish_profile_data(data(),tmp_path)
    assert manifest['profileCount']==3 and len(manifest['shards'])==2
    assert load_profiles(tmp_path/'catalog.json')==legacy==PROFILES
    first=(tmp_path/'catalog.json').read_bytes()
    publish_profile_data(data(),tmp_path)
    assert (tmp_path/'catalog.json').read_bytes()==first


def test_more_than_one_thousand_test_scopes_load_without_creating_real_coverage(tmp_path):
    values=dict(synthetic(i) for i in range(1001))
    manifest=publish_profile_data(values,tmp_path)
    result=load_profiles(tmp_path/'catalog.json')
    assert len(result)==1001 and len(manifest['shards'])==11
    assert all(p.url.startswith('https://fixtures.invalid/') for p in result.values())
    assert all(p.proof.passport=='backend/tests/fixtures/synthetic-passport.md' for p in result.values())


@pytest.mark.parametrize('damage',['hash','count','escape','absolute','duplicate-file','profile-count','json-list'])
def test_corrupt_manifest_fails_closed(tmp_path,damage):
    manifest=publish_profile_data(data(),tmp_path);first=manifest['shards'][0]
    if damage=='hash':first['sha256']='0'*64
    elif damage=='count':first['count']+=1
    elif damage=='escape':first['file']='../outside.json'
    elif damage=='absolute':first['file']='/outside.json'
    elif damage=='duplicate-file':manifest['shards'].append(copy.deepcopy(first))
    elif damage=='profile-count':manifest['profileCount']+=1
    elif damage=='json-list':manifest=[]
    (tmp_path/'catalog.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError):load_profiles(tmp_path/'catalog.json')


def test_bad_new_profile_cannot_replace_manifest_or_lose_old_versions(tmp_path):
    original=data();manifest=publish_profile_data(original,tmp_path)
    snapshot=(tmp_path/'catalog.json').read_bytes();old_files={s['file'] for s in manifest['shards']}
    for modified in ({k:v for k,v in original.items() if k!='sgu-2026-4588'},
                     {**original,'sgu-2026-4588':{**original['sgu-2026-4588'],'seats':999}}):
        with pytest.raises(ValueError):publish_profile_data(modified,tmp_path)
        assert (tmp_path/'catalog.json').read_bytes()==snapshot
    updated={**original,**dict([synthetic(1)])};publish_profile_data(updated,tmp_path)
    assert len(load_profiles(tmp_path/'catalog.json'))==4
    assert all((tmp_path/name).is_file() for name in old_files)


def test_duplicate_profile_keys_and_corrupted_shard_bytes_are_refused(tmp_path):
    manifest=publish_profile_data(data(),tmp_path);shard=tmp_path/manifest['shards'][0]['file']
    shard.write_bytes(shard.read_bytes()+b' ')
    with pytest.raises(ValueError):load_profiles(tmp_path/'catalog.json')
    legacy=tmp_path/'legacy.json';legacy.write_text('{"format":"reviewed-table-profiles-v1","profiles":{},"profiles":{}}')
    with pytest.raises(ValueError):read_profile_data(legacy)


@pytest.mark.parametrize('damage',['missing-proof','wrong-group','wrong-source','duplicate-url'])
def test_unreviewed_or_conflicting_profiles_never_replace_a_valid_manifest(tmp_path,damage):
    original=data();publish_profile_data(original,tmp_path);before=(tmp_path/'catalog.json').read_bytes()
    name,value=synthetic(19)
    if damage=='missing-proof':value['proof']=None
    elif damage=='wrong-group':value['group_id']='x'*37
    elif damage=='wrong-source':value['source_id']='another-id'
    elif damage=='duplicate-url':
        value['url']=original['sgu-2026-4588']['url'];value['proof']['source_url']=value['url']
    with pytest.raises(ValueError):publish_profile_data({**original,name:value},tmp_path)
    assert (tmp_path/'catalog.json').read_bytes()==before
