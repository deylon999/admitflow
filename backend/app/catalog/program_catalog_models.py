"""Versioned programme evidence extends admissions identities, never list snapshots."""
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.admissions import new_id
from app.core.database import Base


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
        CheckConstraint("verification_status IN ('verified', 'unverified', 'conflict')", name='program_revision_verification'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36))
    campaign_id: Mapped[str] = mapped_column(String(36))
    original_url: Mapped[str] = mapped_column(String(2048))
    final_url: Mapped[str] = mapped_column(String(2048))
    content_type: Mapped[str] = mapped_column(String(100))
    document_type: Mapped[str] = mapped_column(String(40))
    verification_status: Mapped[str] = mapped_column(String(16))
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


class ProgramCatalogReadScope(Base):
    """Policy fingerprint, not a cached response; pointer writes serialize here."""
    __tablename__ = 'program_catalog_read_scope'
    __table_args__ = (CheckConstraint('id = 1',name='program_read_scope_singleton'),)
    id: Mapped[int] = mapped_column(Integer,primary_key=True)
    scope_hash: Mapped[str] = mapped_column(String(64))
    known_ids: Mapped[list] = mapped_column(JSON)
    reserved_ids: Mapped[list] = mapped_column(JSON)
    epoch: Mapped[int] = mapped_column(BigInteger,default=0)


class ProgramCatalogReadFact(Base):
    """Synchronous derived index of current immutable facts. Never new identity."""
    __tablename__ = 'program_catalog_read_facts'
    __table_args__ = (
        ForeignKeyConstraint(['revision_id','program_id'],['program_catalog_facts.revision_id','program_catalog_facts.program_id'],name='fk_program_read_fact',ondelete='RESTRICT'),
        ForeignKeyConstraint(['document_id','revision_id'],['program_catalog_revisions.document_id','program_catalog_revisions.id'],name='fk_program_read_document',ondelete='RESTRICT'),
        Index('ix_program_read_public','public_id','revision_id','program_id'),
        Index('ix_program_read_scope','program_id','campaign_id'),
        Index('ix_program_read_document','document_id'),
        Index('uq_program_read_public','public_id',unique=True,postgresql_where=text('eligible'),sqlite_where=text('eligible')),
        Index('uq_program_read_scope','program_id','campaign_id',unique=True,postgresql_where=text('eligible'),sqlite_where=text('eligible')),
        Index('ix_program_read_order','sort_text','public_id',postgresql_include=['program_id','revision_id'],postgresql_where=text('eligible'),sqlite_where=text('eligible')),
        Index('ix_program_read_year_order','year','sort_text','public_id',postgresql_include=['program_id','revision_id'],postgresql_where=text('eligible'),sqlite_where=text('eligible')),
        Index('ix_program_read_university_order','university_id','year','sort_text','public_id',postgresql_include=['program_id','revision_id'],postgresql_where=text('eligible'),sqlite_where=text('eligible')),
        Index('ix_program_read_years','university_id','year',postgresql_where=text('eligible'),sqlite_where=text('eligible')),
    )
    revision_id: Mapped[str] = mapped_column(String(36),primary_key=True)
    program_id: Mapped[str] = mapped_column(String(36),primary_key=True)
    document_id: Mapped[str] = mapped_column(String(36))
    campaign_id: Mapped[str] = mapped_column(String(36))
    public_id: Mapped[str] = mapped_column(String(36))
    university_id: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer)
    sort_text: Mapped[str] = mapped_column(String(300))
    search_text: Mapped[str] = mapped_column(String(1500))
    in_scope: Mapped[bool] = mapped_column(Boolean)
    eligible: Mapped[bool] = mapped_column(Boolean)


class ProgramCatalogReadTotal(Base):
    """Exact eligible row counts, updated in the publication transaction."""
    __tablename__='program_catalog_read_totals'
    __table_args__=(CheckConstraint('program_count >= 0',name='program_read_total_nonnegative'),)
    university_id: Mapped[str] = mapped_column(ForeignKey('universities.id',ondelete='RESTRICT'),primary_key=True)
    year: Mapped[int] = mapped_column(Integer,primary_key=True)
    program_count: Mapped[int] = mapped_column(BigInteger)
