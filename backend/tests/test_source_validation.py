from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.sources.contracts import CandidateRow, ParsedList, SourceBinding
from app.sources.validation import QualityPolicy, Quarantined, validate_list

NOW = datetime(2026,11,1,tzinfo=timezone.utc)
BINDING = SourceBinding('source-1','group-1',2026,'https://example.org/list','example.org','synthetic-v1','archive',True)


def parsed(count=3, **changes):
    rows = tuple(CandidateRow(candidate_key=f'{i:064x}',row_ref=f'row/{i}',official_rank=i,score=Decimal('200')) for i in range(1,count+1))
    return ParsedList(source_id=BINDING.source_id,group_id=BINDING.group_id,year=2026,adapter_version='synthetic-v1',kind='archive',complete=True,expected_rows=count,seats=10,entries=rows,**changes)


def test_equal_scores_preserve_order_and_unknown_fields():
    original = parsed()
    checked = validate_list(original,BINDING,NOW)
    assert checked.parsed == original
    assert checked.parsed.entries[0].consent is None
    assert checked.normalized_hash == validate_list(original,BINDING,NOW+timedelta(hours=1)).normalized_hash
    assert checked.normalized_hash != validate_list(original.model_copy(update={'seats':11}),BINDING,NOW).normalized_hash


@pytest.mark.parametrize(('changes','code'),[
    ({'year':2027},'identity_mismatch'),
    ({'group_id':'other'},'identity_mismatch'),
    ({'kind':'live'},'identity_mismatch'),
    ({'complete':False},'incomplete_list'),
    ({'expected_rows':4},'row_count_mismatch'),
    ({'source_updated_at':NOW+timedelta(hours=1)},'future_source_time'),
    ({'seats':-1},'invalid_schema'),
])
def test_invalid_lists_are_quarantined_without_values(changes,code):
    with pytest.raises(Quarantined,match=f'^{code}$'):
        validate_list(parsed().model_copy(update=changes),BINDING,NOW)


def test_duplicates_order_and_empty_list():
    original=parsed()
    first=original.entries[0]
    for rows,code in [((first,first),'duplicate_candidate'),((first,first.model_copy(update={'candidate_key':'f'*64})),'duplicate_reference'),(tuple(reversed(original.entries)),'invalid_official_order')]:
        with pytest.raises(Quarantined,match=code):
            validate_list(original.model_copy(update={'entries':rows,'expected_rows':len(rows)}),BINDING,NOW)
    assert validate_list(parsed(0),BINDING,NOW).parsed.entries == ()
    with pytest.raises(Quarantined,match='unconfirmed_empty'):
        validate_list(parsed(0).model_copy(update={'expected_rows':None}),BINDING,NOW)


def test_sudden_drop_and_regressed_timestamp_require_review():
    with pytest.raises(Quarantined,match='row_count_drop'):
        validate_list(parsed(3),BINDING,NOW,previous=parsed(10))
    with pytest.raises(Quarantined,match='capacity_drop'):
        validate_list(parsed().model_copy(update={'seats':0}),BINDING,NOW,previous=parsed())
    with pytest.raises(Quarantined,match='source_time_regressed'):
        validate_list(parsed(source_updated_at=NOW-timedelta(days=2)),BINDING,NOW,previous=parsed(source_updated_at=NOW-timedelta(days=1)))
    assert validate_list(parsed().model_copy(update={'seats':None}),BINDING,NOW).parsed.seats is None
    with pytest.raises(ValueError):
        QualityPolicy(max_drop_fraction=1)
