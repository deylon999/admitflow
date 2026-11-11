"""Public product catalog DTOs; unknown admission facts remain null."""
from datetime import datetime
from typing import Literal

from .schema_base import CamelModel


class Provenance(CamelModel):
    url: str
    verified_at: datetime
    source_updated_at: datetime | None = None
    kind: Literal['monitoring', 'archive', 'accreditation']
    edition: int | None = None
    original_sha256: str | None = None


class Accreditation(CamelModel):
    """Active state accreditation of bachelor/specialist programmes in the Rosobrnadzor register."""
    status: Literal['active']
    ogrn: str
    inn: str | None
    certificate_number: str | None
    bachelor_programs: int
    specialist_programs: int
    branches_with_programs: int
    departmental: bool
    match_method: Literal['registry', 'name', 'domain', 'core-region', 'honorary-name-region', 'fuzzy-region']
    dataset_date: str
    source_url: str


class CatalogUniversity(CamelModel):
    id: str
    name: str
    legal_name: str
    region: str
    is_branch: bool
    official_url: str | None
    provenance: Provenance
    known_program_count: int
    years: list[int]
    # None: not matched to an active bachelor/specialist accreditation on the register date.
    accreditation: Accreditation | None = None


class ExamOption(CamelModel):
    subject: str
    title: str
    # None: the document does not state the minimum consistently or at all.
    min_score: int | None


class ExamTest(CamelModel):
    position: int
    options: list[ExamOption]


class ExamSource(CamelModel):
    url: str
    title: str
    document_date: str
    sha256: str
    checked_at: datetime
    cross_check_url: str | None


class ExamRequirements(CamelModel):
    """Entrance tests from the university's official document, reviewed and checked against its text."""
    tests: list[ExamTest]
    # Empty list: the document names no additional tests; None: not collected.
    additional_tests: list[ExamTest] | None
    # Special rights and quotas are not collected yet.
    benefits: None = None
    notes: list[str]
    source: ExamSource


class CatalogProgram(CamelModel):
    id: str
    university_id: str
    university_name: str
    region: str
    campaign_id: str
    year: int
    level: str
    code: str | None
    title: str
    study_form: str
    funding: str
    category: str
    seats: int | None
    # No verified dataset yet. The schema forbids inferred cutoffs and model probabilities.
    historical_cutoff: None = None
    # None unless reviewed rules exist for exactly this year, level, code and study form.
    exam_requirements: ExamRequirements | None = None
    forecast: None = None
    provenance: Provenance


class UniversityPage(CamelModel):
    items: list[CatalogUniversity]
    total: int
    next_offset: int | None
    regions: list[str]
    registry_edition: int
    accreditation_date: str


class ProgramPage(CamelModel):
    items: list[CatalogProgram]
    total: int
    next_offset: int | None
    years: list[int]
    subjects: list[str]
