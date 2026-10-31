from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.admissions import Assessment, Campaign, CandidateEntry, CompetitionGroup, PublishedSnapshot, Source, SourceSnapshot, Subscription, University
from app.database import BrowserSession

NOW = datetime.now(timezone.utc)


def seed_group(db, *, year=2026, university_id='test-main'):
    if db.get(University, university_id) is None:
        db.add(University(id=university_id, name='Синтетический вуз', official_url='https://example.org', provenance_url='https://example.org', verified_at=NOW))
        db.flush()
    campaign = Campaign(university_id=university_id, year=year, level='bachelor')
    db.add(campaign)
    db.flush()
    group = CompetitionGroup(campaign_id=campaign.id, official_id='42', title='Синтетическая группа', study_form='full_time', funding='budget', category='general', seats=None)
    db.add(group)
    db.flush()
    return group


def snapshot(db, group, *, hash='a' * 64):
    source = Source(group_id=group.id, url='https://example.org/list', domain='example.org')
    db.add(source)
    db.flush()
    result = SourceSnapshot(source_id=source.id, group_id=group.id, payload_hash=hash, fetched_at=NOW, kind='archive', row_count=1)
    db.add(result)
    db.flush()
    return result


def test_same_official_group_id_does_not_merge_seasons_or_branches(client, application):
    with Session(application.state.engine) as db:
        groups = [seed_group(db), seed_group(db, year=2027), seed_group(db, university_id='test-branch')]
        db.commit()
        assert len({group.id for group in groups}) == 3


def test_unknown_seats_and_consent_are_not_zero_or_false(client, application):
    with Session(application.state.engine) as db:
        group = seed_group(db)
        snap = snapshot(db, group)
        db.add(CandidateEntry(snapshot_id=snap.id, candidate_key='synthetic-1', official_rank=1))
        db.commit()
        entry = db.get(CandidateEntry, (snap.id, 'synthetic-1'))
        assert group.seats is None and entry.consent is None and entry.priority is None
        assert entry.participation == 'unknown'


def test_duplicate_rank_rejects_entire_import_transaction(client, application):
    with Session(application.state.engine) as db:
        group = seed_group(db)
        snap = snapshot(db, group)
        db.add_all([CandidateEntry(snapshot_id=snap.id, candidate_key=key, official_rank=1) for key in ('synthetic-1', 'synthetic-2')])
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert db.get(SourceSnapshot, snap.id) is None


def test_published_pointer_cannot_reference_another_source(client, application):
    with Session(application.state.engine) as db:
        group = seed_group(db)
        first, second = snapshot(db, group), snapshot(db, group, hash='b' * 64)
        db.add(PublishedSnapshot(source_id=first.source_id, snapshot_id=second.id))
        with pytest.raises(IntegrityError):
            db.commit()


def test_automatic_coverage_requires_a_rules_version(client, application):
    with Session(application.state.engine) as db:
        group = seed_group(db)
        group.coverage = 'automatic'
        with pytest.raises(IntegrityError):
            db.commit()


def test_snapshot_cannot_be_moved_to_another_campaign(client, application):
    with Session(application.state.engine) as db:
        first, second = seed_group(db), seed_group(db, year=2027)
        snap = snapshot(db, first)
        snap.group_id = second.id
        with pytest.raises(IntegrityError):
            db.commit()


def test_assessment_cannot_mix_subscription_and_snapshot_groups(client, application):
    with Session(application.state.engine) as db:
        first, second = seed_group(db), seed_group(db, year=2027)
        snap = snapshot(db, first)
        db.add(BrowserSession(token_hash='c' * 64, expires_at=NOW))
        db.flush()
        sub = Subscription(owner_hash='c' * 64, group_id=second.id, candidate_key='synthetic-1', created_at=NOW)
        db.add(sub)
        db.flush()
        db.add(Assessment(subscription_id=sub.id, group_id=second.id, snapshot_id=snap.id, rules_version='test-v1', assessed_at=NOW, state='unsupported', facts={}, assumptions=[]))
        with pytest.raises(IntegrityError):
            db.commit()
