import { InvalidResponseError } from './contracts';
import { compareOpaqueIds, instantMicros } from './time';

export type SourceGroup = { id: string; universityId: string; universityName: string; parentUniversityId: string | null; year: number; level: string; title: string; studyForm: string; funding: string; category: string; seats: number | null; coverage: 'manual' | 'archive' | 'automatic' | 'unsupported'; dataKind: 'archive' | 'live' | null; sourceId: string | null; sourceUrl: string | null; sourceState: string | null; snapshotId: string | null; fetchedAt: string | null; sourceUpdatedAt: string | null; lastCheckedAt: string | null; rowCount: number | null; lookupAvailable: boolean; assessmentAvailable: false; scenarioAvailable: boolean };
export type GroupCatalog = { items: SourceGroup[]; total: number; nextCursor: string | null; facets: { branches: { id: string; name: string }[]; years: number[] } };
export type CandidateFact = { rowRef: string; officialRank: number; score: string | null; consent: boolean | null; priority: number | null; participation: 'unknown' | 'active' | 'withdrawn' | 'enrolled' };
export type LookupResult = { group: SourceGroup; found: boolean; candidate: CandidateFact | null; confirmationToken: string | null; expiresAt: string | null };
export type ArchiveDirection = { id: string; createdAt: string; group: SourceGroup; candidate: CandidateFact | null; confirmedSnapshotId: string | null; notice: string | null };
export type DirectionBudget = { limit: 20; total: number; manualCount: number; archiveCount: number };
export type ArchiveHistoryItem = { id: string; assessedAt: string; modelVersion: string; group: SourceGroup; candidate: CandidateFact | null; present: boolean };
export type ArchiveHistoryPage = { items: ArchiveHistoryItem[]; total: number; nextCursor: string | null };
export type SourceCheck = { id: string; checkedAt: string; outcome: 'success' | 'failed'; errorCode: string | null; snapshotId: string | null };
export function parseSourceChecks(value: unknown): SourceCheck[] {
  if (!Array.isArray(value) || value.length > 20) throw new InvalidResponseError();
  return value.map(value => { const o = sourceObject(value); if (!['success', 'failed'].includes(String(o.outcome))) throw new InvalidResponseError();
    return { id: sourceText(o.id, 36), checkedAt: sourceTime(o.checkedAt), outcome: o.outcome as SourceCheck['outcome'], errorCode: nullableText(o.errorCode, 80), snapshotId: nullableText(o.snapshotId, 36) }; });
}
export function sourceObject(v: unknown): Record<string, unknown> { if (!v || typeof v !== 'object' || Array.isArray(v)) throw new InvalidResponseError(); return v as Record<string, unknown>; }
export function sourceText(v: unknown, max = 300): string { if (typeof v !== 'string' || !v.trim() || Array.from(v).length > max || /[\u0000-\u001f\u007f]/.test(v)) throw new InvalidResponseError(); return v; }
export function sourceInt(v: unknown, min = 0, max = 1_000_000): number { if (typeof v !== 'number' || !Number.isSafeInteger(v) || v < min || v > max) throw new InvalidResponseError(); return v; }
const nullableText = (v: unknown, max = 300) => v === null ? null : sourceText(v, max);
export function sourceTime(v: unknown): string { const s = sourceText(v, 50); try { instantMicros(s); } catch { throw new InvalidResponseError(); } return s; }
const nullableTime = (v: unknown) => v === null ? null : sourceTime(v);

export function parseSourceGroup(value: unknown): SourceGroup {
  const o = sourceObject(value);
  if (!['manual', 'archive', 'automatic', 'unsupported'].includes(String(o.coverage)) || typeof o.lookupAvailable !== 'boolean' || o.assessmentAvailable !== false) throw new InvalidResponseError();
  if (o.dataKind !== null && o.dataKind !== 'archive' && o.dataKind !== 'live') throw new InvalidResponseError();
  const sourceUrl = nullableText(o.sourceUrl, 2048);
  if (sourceUrl) { try { const url = new URL(sourceUrl); if (url.protocol !== 'https:' || url.username || url.password) throw new Error(); } catch { throw new InvalidResponseError(); } }
  const group: SourceGroup = {
    id: sourceText(o.id, 36), universityId: sourceText(o.universityId, 80), universityName: sourceText(o.universityName), parentUniversityId: nullableText(o.parentUniversityId, 80),
    year: sourceInt(o.year, 2000, 2100), level: sourceText(o.level, 24), title: sourceText(o.title), studyForm: sourceText(o.studyForm, 40), funding: sourceText(o.funding, 40), category: sourceText(o.category, 80), seats: o.seats === null ? null : sourceInt(o.seats),
    coverage: o.coverage as SourceGroup['coverage'], dataKind: o.dataKind, sourceId: nullableText(o.sourceId, 36), sourceUrl, sourceState: nullableText(o.sourceState, 40), snapshotId: nullableText(o.snapshotId, 36),
    fetchedAt: nullableTime(o.fetchedAt), sourceUpdatedAt: nullableTime(o.sourceUpdatedAt), lastCheckedAt: nullableTime(o.lastCheckedAt), rowCount: o.rowCount === null ? null : sourceInt(o.rowCount), lookupAvailable: o.lookupAvailable, assessmentAvailable: false, scenarioAvailable: o.scenarioAvailable === undefined ? false : (() => { if (typeof o.scenarioAvailable !== 'boolean') throw new InvalidResponseError(); return o.scenarioAvailable; })(),
  };
  if (group.lookupAvailable && (!group.sourceId || !group.snapshotId || !group.fetchedAt || group.coverage === 'unsupported' || group.coverage === 'manual')) throw new InvalidResponseError();
  if (group.scenarioAvailable && (!group.lookupAvailable || group.funding !== 'budget' || group.category !== 'general' || group.seats === null || group.seats <= 0)) throw new InvalidResponseError();
  return group;
}

export function parseGroupCatalog(value: unknown): GroupCatalog {
  const o = sourceObject(value), facets = sourceObject(o.facets);
  if (!Array.isArray(o.items) || o.items.length > 50 || !Array.isArray(facets.branches) || facets.branches.length > 100 || !Array.isArray(facets.years) || facets.years.length > 101) throw new InvalidResponseError();
  return { items: o.items.map(parseSourceGroup), total: sourceInt(o.total), nextCursor: nullableText(o.nextCursor, 36), facets: { branches: facets.branches.map(value => { const item = sourceObject(value); return { id: sourceText(item.id, 80), name: sourceText(item.name) }; }), years: facets.years.map(value => sourceInt(value, 2000, 2100)) } };
}

export function parseCandidate(value: unknown): CandidateFact {
  const o = sourceObject(value);
  if ((o.consent !== null && typeof o.consent !== 'boolean') || !['unknown', 'active', 'withdrawn', 'enrolled'].includes(String(o.participation))) throw new InvalidResponseError();
  const score = o.score === null ? null : sourceText(o.score, 10);
  if (score !== null && (!/^[0-9]{1,4}(?:\.[0-9]{1,2})?$/.test(score) || Number(score) > 1000)) throw new InvalidResponseError();
  return { rowRef: sourceText(o.rowRef, 100), officialRank: sourceInt(o.officialRank, 1), score, consent: o.consent as boolean | null, priority: o.priority === null ? null : sourceInt(o.priority, 1, 1000), participation: o.participation as CandidateFact['participation'] };
}
export function parseLookup(value: unknown): LookupResult {
  const o = sourceObject(value), group = parseSourceGroup(o.group);
  if (typeof o.found !== 'boolean') throw new InvalidResponseError();
  const candidate = o.candidate === null ? null : parseCandidate(o.candidate);
  const token = nullableText(o.confirmationToken, 2048), expiresAt = nullableTime(o.expiresAt);
  if (o.found !== Boolean(candidate && token && expiresAt) || (!o.found && (candidate || token || expiresAt)) || (candidate && group.rowCount !== null && candidate.officialRank > group.rowCount)) throw new InvalidResponseError();
  return { group, found: o.found, candidate, confirmationToken: token, expiresAt };
}
export function parseSubscriptionSaved(value: unknown) {
  const o = sourceObject(value);
  return { id: sourceText(o.id, 36), groupId: sourceText(o.groupId, 36), sourceId: sourceText(o.sourceId, 36), createdAt: sourceTime(o.createdAt) };
}
export function parseArchiveDirections(value: unknown): ArchiveDirection[] {
  if (!Array.isArray(value) || value.length > 20) throw new InvalidResponseError();
  return value.map(value => { const o = sourceObject(value); return { id: sourceText(o.id, 36), createdAt: sourceTime(o.createdAt), group: parseSourceGroup(o.group), candidate: o.candidate === null ? null : parseCandidate(o.candidate), confirmedSnapshotId: nullableText(o.confirmedSnapshotId, 36), notice: nullableText(o.notice, 500) }; });
}
export function parseDirectionBudget(value: unknown): DirectionBudget {
  const o = sourceObject(value), total = sourceInt(o.total), manualCount = sourceInt(o.manualCount), archiveCount = sourceInt(o.archiveCount);
  if (o.limit !== 20 || manualCount + archiveCount !== total) throw new InvalidResponseError();
  return { limit: 20, total, manualCount, archiveCount };
}

export function parseArchiveExport(value: unknown) {
  const o = sourceObject(value);
  if (o.formatVersion !== 'archive-facts-v1' || o.scope !== 'current-published-facts') throw new InvalidResponseError();
  return { formatVersion: 'archive-facts-v1' as const, scope: 'current-published-facts' as const, exportedAt: sourceTime(o.exportedAt), directions: parseArchiveDirections(o.directions) };
}

export function assertArchiveOrder(items: ArchiveHistoryItem[]) {
  const ids = new Set<string>();
  items.forEach((item, index) => {
    if (ids.has(item.id) || !item.group.fetchedAt) throw new InvalidResponseError();
    if (item.group.id !== items[0].group.id || item.group.sourceId !== items[0].group.sourceId || item.group.year !== items[0].group.year) throw new InvalidResponseError();
    ids.add(item.id);
    const previous = items[index-1];
    if (previous && (instantMicros(previous.group.fetchedAt!) < instantMicros(item.group.fetchedAt) ||
      (instantMicros(previous.group.fetchedAt!) === instantMicros(item.group.fetchedAt) && compareOpaqueIds(previous.id, item.id) <= 0))) throw new InvalidResponseError();
  });
}
export function parseArchiveHistory(value: unknown): ArchiveHistoryPage {
  const o = sourceObject(value);
  if (!Array.isArray(o.items) || o.items.length > 100) throw new InvalidResponseError();
  const items = o.items.map(value => {
    const item = sourceObject(value), candidate = item.candidate === null ? null : parseCandidate(item.candidate), group = parseSourceGroup(item.group);
    if (item.present !== Boolean(candidate) || !group.snapshotId || !group.fetchedAt || group.lookupAvailable) throw new InvalidResponseError();
    return { id: sourceText(item.id, 36), assessedAt: sourceTime(item.assessedAt), modelVersion: sourceText(item.modelVersion, 80), group, candidate, present: item.present as boolean };
  });
  assertArchiveOrder(items);
  const nextCursor = nullableText(o.nextCursor, 36), total = sourceInt(o.total);
  if (total < items.length || (nextCursor !== null && (!items.length || nextCursor !== items.at(-1)!.id))) throw new InvalidResponseError();
  return { items, total, nextCursor };
}
