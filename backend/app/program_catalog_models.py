"""Versioned programme evidence extends admissions identities, never list snapshots."""
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .admissions import new_id
from .database import Base


class ProgramCatalogDocument(Base):
    __tablename__ = 'program_catalog_documents'
    __table_args__ = (
        UniqueConstraint('campaign_id', 'source_namespace', name='uq_program_document_scope'),
        UniqueConstraint('id', 'campaign_id', name='uq_program_document_campaign'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey('campaigns.id', ondelete='RESTRICT'))
    source_namespace: Mapped[str] = mapped_column(String(160))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(80))


class ProgramCatalogRevision(Base):
    __tablename__ = 'program_catalog_revisions'
    __table_args__ = (
        UniqueConstraint('document_id', 'original_sha256', 'extractor_version', 'review_sha256', name='uq_program_revision_content'),
        UniqueConstraint('document_id', 'id', name='uq_program_revision_document'),
        UniqueConstraint('id', 'campaign_id', name='uq_program_revision_campaign'),
        ForeignKeyConstraint(['document_id', 'campaign_id'], ['program_catalog_documents.id', 'program_catalog_documents.campaign_id'], name='fk_program_revision_scope', ondelete='RESTRICT'),
        CheckConstraint("completeness IN ('partial', 'complete')", name='program_revision_completeness'),
        CheckConstraint('program_count > 0 AND group_count >= 0', name='program_revision_counts'),
        CheckConstraint('fetched_at <= checked_at', name='program_revision_times'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36))
    campaign_id: Mapped[str] = mapped_column(String(36))
    original_url: Mapped[str] = mapped_column(String(2048))
    final_url: Mapped[str] = mapped_column(String(2048))
    content_type: Mapped[str] = mapped_column(String(100))
    publication_date: Mapped[date | None] = mapped_column(Date)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    original_sha256: Mapped[str] = mapped_column(String(64))
    extractor_version: Mapped[str] = mapped_column(String(80))
    review_sha256: Mapped[str] = mapped_column(String(64))
    normalized_sha256: Mapped[str] = mapped_column(String(64))
    completeness: Mapped[str] = mapped_column(String(16))
    program_count: Mapped[int] = mapped_column(Integer)
    group_count: Mapped[int] = mapped_column(Integer)
    university_name: Mapped[str] = mapped_column(String(300))


class ProgramCatalogFact(Base):
    __tablename__ = 'program_catalog_facts'
    __table_args__ = (
        UniqueConstraint('revision_id', 'public_id', name='uq_program_fact_public_id'),
        UniqueConstraint('revision_id', 'program_id', 'campaign_id', name='uq_program_fact_scope'),
        ForeignKeyConstraint(['revision_id', 'campaign_id'], ['program_catalog_revisions.id', 'program_catalog_revisions.campaign_id'], name='fk_program_fact_revision_scope', ondelete='RESTRICT'),
        ForeignKeyConstraint(['program_id', 'campaign_id'], ['campaign_programs.program_id', 'campaign_programs.campaign_id'], name='fk_program_fact_identity_scope', ondelete='RESTRICT'),
        CheckConstraint('seats IS NULL OR seats >= 0', name='program_fact_seats'),
    )
    revision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    program_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36))
    public_id: Mapped[str] = mapped_column(String(36), index=True)
    source_key: Mapped[str] = mapped_column(String(300))
    title: Mapped[str] = mapped_column(String(300))
    code: Mapped[str | None] = mapped_column(String(16))
    study_form: Mapped[str | None] = mapped_column(String(40))
    funding: Mapped[str | None] = mapped_column(String(40))
    category: Mapped[str | None] = mapped_column(String(80))
    seats: Mapped[int | None] = mapped_column(Integer)
    admission_totals: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    evidence: Mapped[dict] = mapped_column(JSON)
    search_text: Mapped[str] = mapped_column(String(1500))
    sort_text: Mapped[str] = mapped_column(String(300))


class ProgramCatalogGroupFact(Base):
    __tablename__ = 'program_catalog_group_facts'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id', 'program_id', 'campaign_id'], ['program_catalog_facts.revision_id', 'program_catalog_facts.program_id', 'program_catalog_facts.campaign_id'], name='fk_program_group_fact_scope', ondelete='RESTRICT'),
        ForeignKeyConstraint(['group_id', 'campaign_id'], ['competition_groups.id', 'competition_groups.campaign_id'], name='fk_program_group_fact_identity', ondelete='RESTRICT'),
        ForeignKeyConstraint(['group_id', 'program_id'], ['competition_group_programs.group_id', 'competition_group_programs.program_id'], name='fk_program_group_fact_link', ondelete='RESTRICT'),
    )
    revision_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    program_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    group_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36))
    facts: Mapped[dict] = mapped_column(JSON)


class ProgramCatalogPublication(Base):
    __tablename__ = 'program_catalog_publications'
    __table_args__ = (
        ForeignKeyConstraint(['document_id', 'revision_id'], ['program_catalog_revisions.document_id', 'program_catalog_revisions.id'], name='fk_program_publication_revision', ondelete='RESTRICT'),
    )
    document_id: Mapped[str] = mapped_column(ForeignKey('program_catalog_documents.id', ondelete='RESTRICT'), primary_key=True)
    revision_id: Mapped[str] = mapped_column(String(36))


class ProgramCatalogImportAttempt(Base):
    __tablename__ = 'program_catalog_import_attempts'
    __table_args__ = (
        CheckConstraint("stage IN ('validation', 'identity', 'publication')", name='program_attempt_stage'),
        CheckConstraint("outcome IN ('published', 'unchanged', 'rejected')", name='program_attempt_outcome'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    stage: Mapped[str] = mapped_column(String(24))
    outcome: Mapped[str] = mapped_column(String(24))
    error_code: Mapped[str | None] = mapped_column(String(80))
    original_sha256: Mapped[str | None] = mapped_column(String(64))
    revision_id: Mapped[str | None] = mapped_column(String(36), index=True)
