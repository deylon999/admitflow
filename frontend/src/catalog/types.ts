export type Provenance = {
  url: string;
  verifiedAt: string;
  sourceUpdatedAt: string | null;
  kind: 'monitoring' | 'archive';
  edition: number | null;
  originalSha256: string | null;
};

export type University = {
  id: string;
  name: string;
  legalName: string;
  region: string;
  isBranch: boolean;
  officialUrl: string | null;
  provenance: Provenance;
  knownProgramCount: number;
  years: number[];
};

export type CatalogProgram = {
  id: string;
  universityId: string;
  universityName: string;
  region: string;
  campaignId: string;
  year: number;
  level: string;
  code: string | null;
  title: string;
  studyForm: string;
  funding: string;
  category: string;
  seats: number | null;
  historicalCutoff: null;
  examRequirements: null;
  forecast: null;
  provenance: Provenance;
};

export type CatalogPage<T> = {
  items: T[];
  total: number;
  nextOffset: number | null;
};
export type UniversityResults = CatalogPage<University> & { regions: string[]; registryEdition: number };
export type ProgramResults = CatalogPage<CatalogProgram> & { years: number[]; subjects: string[] };
