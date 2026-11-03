import { InvalidResponseError } from './contracts';
import { instantMicros } from './time';

export type SourceGroup = { id: string; universityId: string; universityName: string; parentUniversityId: string | null; year: number; level: string; title: string; studyForm: string; funding: string; category: string; seats: number | null; coverage: 'manual' | 'archive' | 'automatic' | 'unsupported'; dataKind: 'archive' | 'live' | null; sourceId: string | null; sourceUrl: string | null; sourceState: string | null; snapshotId: string | null; fetchedAt: string | null; sourceUpdatedAt: string | null; lastCheckedAt: string | null; rowCount: number | null; lookupAvailable: boolean; assessmentAvailable: false };
export type GroupCatalog = { items: SourceGroup[]; total: number; nextCursor: string | null; facets: { branches: { id: string; name: string }[]; years: number[] } };
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
    fetchedAt: nullableTime(o.fetchedAt), sourceUpdatedAt: nullableTime(o.sourceUpdatedAt), lastCheckedAt: nullableTime(o.lastCheckedAt), rowCount: o.rowCount === null ? null : sourceInt(o.rowCount), lookupAvailable: o.lookupAvailable, assessmentAvailable: false,
  };
  if (group.lookupAvailable && (!group.sourceId || !group.snapshotId || !group.fetchedAt || group.coverage === 'unsupported' || group.coverage === 'manual')) throw new InvalidResponseError();
  return group;
}

export function parseGroupCatalog(value: unknown): GroupCatalog {
  const o = sourceObject(value), facets = sourceObject(o.facets);
  if (!Array.isArray(o.items) || o.items.length > 50 || !Array.isArray(facets.branches) || facets.branches.length > 100 || !Array.isArray(facets.years) || facets.years.length > 101) throw new InvalidResponseError();
  return { items: o.items.map(parseSourceGroup), total: sourceInt(o.total), nextCursor: nullableText(o.nextCursor, 36), facets: { branches: facets.branches.map(value => { const item = sourceObject(value); return { id: sourceText(item.id, 80), name: sourceText(item.name) }; }), years: facets.years.map(value => sourceInt(value, 2000, 2100)) } };
}
