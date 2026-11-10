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
    # These fields have no verified dataset yet. A schema deliberately forbids
    # returning inferred cutoffs, examination rules or model probabilities.
    historical_cutoff: None = None
    exam_requirements: None = None
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
