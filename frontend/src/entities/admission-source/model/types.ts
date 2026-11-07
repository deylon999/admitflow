export type SourceGroup = {
  id: string;
  universityId: string;
  universityName: string;
  parentUniversityId: string | null;
  year: number;
  level: string;
  title: string;
  studyForm: string;
  funding: string;
  category: string;
  seats: number | null;
  coverage: 'manual' | 'archive' | 'automatic' | 'unsupported';
  dataKind: 'archive' | 'live' | null;
  sourceId: string | null;
  sourceUrl: string | null;
  sourceState: string | null;
  snapshotId: string | null;
  fetchedAt: string | null;
  sourceUpdatedAt: string | null;
  lastCheckedAt: string | null;
  rowCount: number | null;
  lookupAvailable: boolean;
  lookupCodeHint?: string | null;
  assessmentAvailable: false;
  scenarioAvailable: boolean;
};
export type GroupCatalog = {
  items: SourceGroup[];
  total: number;
  nextCursor: string | null;
  facets: { branches: { id: string; name: string }[]; years: number[] };
};
export type CandidateFact = {
  rowRef: string;
  officialRank: number;
  score: string | null;
  consent: boolean | null;
  priority: number | null;
  participation: 'unknown' | 'active' | 'withdrawn' | 'enrolled';
};
export type LookupResult = {
  group: SourceGroup;
  found: boolean;
  candidate: CandidateFact | null;
  confirmationToken: string | null;
  expiresAt: string | null;
};
export type ArchiveDirection = {
  id: string;
  createdAt: string;
  group: SourceGroup;
  candidate: CandidateFact | null;
  confirmedSnapshotId: string | null;
  notice: string | null;
};
export type DirectionBudget = {
  limit: 20;
  total: number;
  manualCount: number;
  archiveCount: number;
};
export type ArchiveHistoryItem = {
  id: string;
  assessedAt: string;
  modelVersion: string;
  group: SourceGroup;
  candidate: CandidateFact | null;
  present: boolean;
};
export type ArchiveHistoryPage = {
  items: ArchiveHistoryItem[];
  total: number;
  nextCursor: string | null;
};
export type SourceCheck = {
  id: string;
  checkedAt: string;
  outcome: 'success' | 'failed';
  errorCode: string | null;
  snapshotId: string | null;
};
