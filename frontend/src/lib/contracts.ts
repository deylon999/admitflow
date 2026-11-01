import { calculatePlace } from './calculator';
import type { CalculationResult, CalculationValues } from './calculator';
import { instantMicros } from './time';

export type Snapshot = { id: string; capturedAt: string; sourceKind: 'manual'; modelVersion: 'manual-v1'; values: CalculationValues; calculation: CalculationResult };
export type Watch = { id: string; university: string; title: string; sourceUrl: string; createdAt: string; latest: Snapshot };
export type WatchDetail = Watch & { history: Snapshot[] };
export type WatchCreate = { university: string; title: string; sourceUrl: string; values: CalculationValues };
export type SessionInfo = { expiresAt: string };
export type University = { id: string; name: string; officialUrl: string; provenanceUrl: string; verifiedAt: string; coverage: 'manual' };
export type Catalog = { items: University[]; total: number };
export type DataExport = { formatVersion: 'manual-export-v1'; exportedAt: string; watches: WatchDetail[] };
export type HistoryPage = { items: Snapshot[]; nextCursor: string | null; total: number | null };
export type ImportResult = { importedCount: number; snapshotCount: number; replayed: boolean };
export type Coverage = { catalogUniversities: number; automaticSources: number; publishedGroups: number; freshGroups: number; archiveGroups: number; nationalTotal: null; generatedAt: string };

export class InvalidResponseError extends Error {
  constructor() { super('Сервер вернул некорректные данные. Расчёт не показан — попробуйте обновить страницу.'); }
}

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new InvalidResponseError();
  return value as Record<string, unknown>;
}
function text(value: unknown, max = 2048): string {
  if (typeof value !== 'string' || !value.trim() || value.length > max) throw new InvalidResponseError();
  return value;
}
function timestamp(value: unknown): string {
  const result = text(value, 50);
  try { instantMicros(result); } catch { throw new InvalidResponseError(); }
  return result;
}
function url(value: unknown): string {
  const result = text(value);
  try {
    const parsed = new URL(result);
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) throw new Error();
  } catch { throw new InvalidResponseError(); }
  return result;
}
function array<T>(value: unknown, parse: (item: unknown) => T, max: number): T[] {
  if (!Array.isArray(value) || value.length > max) throw new InvalidResponseError();
  return value.map(parse);
}

export function parseSnapshot(value: unknown): Snapshot {
  const row = object(value);
  if (row.sourceKind !== 'manual' || row.modelVersion !== 'manual-v1') throw new InvalidResponseError();
  const raw = object(row.values);
  const values = {} as CalculationValues;
  for (const key of ['rank', 'seats', 'excluded', 'noConsent'] as const) {
    if (typeof raw[key] !== 'number' || !Number.isSafeInteger(raw[key])) throw new InvalidResponseError();
    values[key] = raw[key];
  }
  const calculation = calculatePlace(values);
  if ('error' in calculation) throw new InvalidResponseError();
  const supplied = object(row.calculation);
  for (const key of ['place', 'worstPlace', 'seats', 'state'] as const) {
    if (supplied[key] !== calculation[key]) throw new InvalidResponseError();
  }
  text(supplied.status, 500);
  return { id: text(row.id, 100), capturedAt: timestamp(row.capturedAt), sourceKind: 'manual', modelVersion: 'manual-v1', values, calculation };
}

export function parseWatch(value: unknown): Watch {
  const row = object(value);
  const watch = { id: text(row.id, 100), university: text(row.university, 160), title: text(row.title, 200), sourceUrl: url(row.sourceUrl), createdAt: timestamp(row.createdAt), latest: parseSnapshot(row.latest) };
  if (instantMicros(watch.latest.capturedAt) < instantMicros(watch.createdAt)) throw new InvalidResponseError();
  return watch;
}
export function parseWatches(value: unknown): Watch[] {
  const rows = array(value, parseWatch, 20);
  if (new Set(rows.map(row => row.id)).size !== rows.length) throw new InvalidResponseError();
  return rows;
}
function parseHistory(value: unknown, maxRecords: number): WatchDetail {
  const row = object(value);
  const watch = parseWatch(row);
  const history = array(row.history, parseSnapshot, maxRecords);
  if (!history.length || JSON.stringify(history[0]) !== JSON.stringify(watch.latest)
    || new Set(history.map(item => item.id)).size !== history.length) throw new InvalidResponseError();
  assertSnapshotOrder(history);
  if (history.some(item => instantMicros(item.capturedAt) < instantMicros(watch.createdAt))) throw new InvalidResponseError();
  return { ...watch, history };
}
export function parseDetail(value: unknown): WatchDetail {
  return parseHistory(value, 100);
}
export function parseHistoryPage(value: unknown): HistoryPage {
  const row = object(value);
  const items = array(row.items, parseSnapshot, 100);
  const nextCursor = row.nextCursor === null ? null : text(row.nextCursor, 100);
  if (new Set(items.map(item => item.id)).size !== items.length
    || (nextCursor !== null && nextCursor !== items.at(-1)?.id)
    ) throw new InvalidResponseError();
  assertSnapshotOrder(items);
  const total = row.total === undefined ? null : row.total;
  if (total !== null && (typeof total !== 'number' || !Number.isInteger(total) || total < items.length || total < 1 || total > 500)) throw new InvalidResponseError();
  return { items, nextCursor, total };
}
export function parseExport(value: unknown): DataExport {
  const row = object(value);
  if (row.formatVersion !== 'manual-export-v1') throw new InvalidResponseError();
  const watches = array(row.watches, item => parseHistory(item, 500), 20);
  if (new Set(watches.map(item => item.id)).size !== watches.length) throw new InvalidResponseError();
  const exportedAt = timestamp(row.exportedAt);
  const snapshots = watches.flatMap(watch => watch.history);
  if (new Set(snapshots.map(item => item.id)).size !== snapshots.length
    || snapshots.some(item => instantMicros(item.capturedAt) > instantMicros(exportedAt))) throw new InvalidResponseError();
  return { formatVersion: 'manual-export-v1', exportedAt, watches };
}

export function assertSnapshotOrder(items: Snapshot[]): void {
  const seen = new Set<string>();
  let previous: Snapshot | undefined;
  for (const item of items) {
    const current = instantMicros(item.capturedAt);
    if (seen.has(item.id) || (previous && (current > instantMicros(previous.capturedAt)
      || (current === instantMicros(previous.capturedAt) && item.id >= previous.id)))) throw new InvalidResponseError();
    seen.add(item.id);
    previous = item;
  }
}
export function parseSession(value: unknown): SessionInfo {
  return { expiresAt: timestamp(object(value).expiresAt) };
}
export function parseImportResult(value: unknown): ImportResult {
  const row = object(value);
  const count = row.importedCount;
  const snapshots = row.snapshotCount;
  if (typeof count !== 'number' || !Number.isInteger(count) || count < 1 || count > 20
    || typeof snapshots !== 'number' || !Number.isInteger(snapshots) || snapshots < count || snapshots > count * 500
    || typeof row.replayed !== 'boolean') throw new InvalidResponseError();
  return { importedCount: count, snapshotCount: snapshots, replayed: row.replayed };
}
export function parseCoverage(value: unknown): Coverage {
  const row = object(value);
  const counts = ['catalogUniversities', 'automaticSources', 'publishedGroups', 'freshGroups', 'archiveGroups'] as const;
  for (const key of counts) if (typeof row[key] !== 'number' || !Number.isSafeInteger(row[key]) || row[key] < 0) throw new InvalidResponseError();
  const result = Object.fromEntries(counts.map(key => [key, row[key]])) as Pick<Coverage, typeof counts[number]>;
  if (result.publishedGroups > result.automaticSources || result.freshGroups + result.archiveGroups > result.publishedGroups || row.nationalTotal !== null) throw new InvalidResponseError();
  return { ...result, nationalTotal: null, generatedAt: timestamp(row.generatedAt) };
}
export function parseCatalog(value: unknown): Catalog {
  const row = object(value);
  const items = array(row.items, value => {
    const item = object(value);
    if (item.coverage !== 'manual') throw new InvalidResponseError();
    return { id: text(item.id, 80), name: text(item.name, 300), officialUrl: url(item.officialUrl), provenanceUrl: url(item.provenanceUrl), verifiedAt: timestamp(item.verifiedAt), coverage: 'manual' as const };
  }, 50);
  if (typeof row.total !== 'number' || !Number.isSafeInteger(row.total) || row.total < items.length
    || new Set(items.map(item => item.id)).size !== items.length) throw new InvalidResponseError();
  return { items, total: row.total };
}
