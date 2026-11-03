from app.scenario_explanations import explain
from test_scenarios import rows,run


def test_explanation_numbers_and_changes_follow_only_verified_facts():
    result=run(rows(True,None,False),seats=2)
    text=explain(result,[{'field':'consentYesAbove','before':0,'after':1}])
    assert 'между 2 и 3' in text.summary and 'Однозначного вывода нет' in text.summary
    assert text.changes==['Согласий выше: 0 → 1.']
    assert '1 + 1 = 2' in text.basis[1]
    assert all('%' not in s for s in [text.summary,*text.basis,*text.changes])
    assert any('Предполагается ваше согласие' in s for s in text.limitations)


def test_refusal_and_archive_absence_never_invent_a_result():
    paid=explain(run(rows(True,False),funding='contract'),[])
    assert 'платного конкурса' in paid.summary and paid.basis==[]
    missing=explain(run(rows(True,False),key='missing'),[])
    assert 'не подтверждает отзыв или отказ' in missing.summary
    no_capacity=explain(run(rows(False),seats=0),[])
    assert 'равно нулю' in no_capacity.summary and no_capacity.basis==[]
