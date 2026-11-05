import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('group_source_formats',Path(__file__).resolve().parents[2]/'scripts/group_source_formats.py')
groups=importlib.util.module_from_spec(spec);spec.loader.exec_module(groups)


def page(host,ident,columns):
    return dict(requestedUrl=f'https://{host}/list',registryIds=[ident],payloadHash='0'*64,
        listEvidence=[dict(columns=columns,headerCount=len(columns),cellCounts=[len(columns)],headerHash='1'*64,observedRows=3,paginationDetected=False)])


def test_multiple_scopes_on_one_host_do_not_prove_cross_institution_reuse():
    result=groups.group_pages([page('one.invalid','1',['rank','candidate-code','score']),page('one.invalid','2',['rank','candidate-code','score'])])
    assert len(result)==1 and result[0]['crossInstitutionCandidate'] is False
    assert result[0]['supported'] is False


def test_equal_role_layouts_are_only_candidates_and_incompatible_columns_stay_separate():
    result=groups.group_pages([page('one.invalid','1',['rank','candidate-code','score']),page('two.invalid','2',['rank','candidate-code','score']),page('three.invalid','3',['rank','snils','score'])])
    assert len(result)==2 and sum(g['crossInstitutionCandidate'] for g in result)==1
    assert all(not member['complete'] for g in result for member in g['members'])


def test_seed_cannot_move_to_an_unrelated_domain(tmp_path):
    from types import SimpleNamespace
    with pytest.raises(ValueError,match='official host'):
        groups.seeded_children(dict(registryId='1',url='https://unrelated.invalid/',childPathMarker='/competition/'),tmp_path,{'1':SimpleNamespace(official_url='https://official.invalid/')})


def test_repeated_group_headers_keep_varying_exam_columns_as_candidates_only():
    a=page('one.invalid','1',['rank','candidate-code','score','other'])
    b=page('two.invalid','2',['rank','candidate-code','score','other','other'])
    for value in (a,b):value['listEvidence'][0].update(hierarchicalHeader=True,primaryHeaderHash='f'*64,primaryColumns=['rank','candidate-code','score','other'])
    result=groups.group_pages([a,b])
    assert len(result)==1 and result[0]['crossInstitutionCandidate']
    assert result[0]['supported'] is False
