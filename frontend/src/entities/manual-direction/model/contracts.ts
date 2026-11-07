import { InvalidResponseError, object, text, timestamp, url, array } from '@/shared/api';
import { compareOpaqueIds, instantMicros } from '@/shared/lib/time';
import { calculatePlace } from './calculator';
import type { CalculationValues } from './calculator';
import type { Snapshot, Watch, WatchDetail, HistoryPage, DataExport, ImportResult } from './types';

export function parseSnapshot(value: unknown): Snapshot {
  const row = object(value);
  if (row.sourceKind !== 'manual' || row.modelVersion !== 'manual-v1')
    throw new InvalidResponseError();
  const raw = object(row.values);
  const values = {} as CalculationValues;
  for (const key of ['rank', 'seats', 'excluded', 'noConsent'] as const) {
    if (typeof raw[key] !== 'number' || !Number.isSafeInteger(raw[key]))
      throw new InvalidResponseError();
    values[key] = raw[key];
  }
  const calculation = calculatePlace(values);
  if ('error' in calculation) throw new InvalidResponseError();
  const supplied = object(row.calculation);
  for (const key of ['place', 'worstPlace', 'seats', 'state'] as const) {
    if (supplied[key] !== calculation[key]) throw new InvalidResponseError();
  }
  text(supplied.status, 500);
  return {
    id: text(row.id, 100),
    capturedAt: timestamp(row.capturedAt),
    sourceKind: 'manual',
    modelVersion: 'manual-v1',
    values,
    calculation,
  };
}

export function parseWatch(value: unknown): Watch {
  const row = object(value);
  const watch = {
    id: text(row.id, 100),
    university: text(row.university, 160),
    title: text(row.title, 200),
    sourceUrl: url(row.sourceUrl),
    createdAt: timestamp(row.createdAt),
    latest: parseSnapshot(row.latest),
  };
  if (instantMicros(watch.latest.capturedAt) < instantMicros(watch.createdAt))
    throw new InvalidResponseError();
  return watch;
}
export function parseWatches(value: unknown): Watch[] {
  const rows = array(value, parseWatch, 20);
  if (new Set(rows.map((row) => row.id)).size !== rows.length) throw new InvalidResponseError();
  return rows;
}
function parseHistory(value: unknown, maxRecords: number): WatchDetail {
  const row = object(value);
  const watch = parseWatch(row);
  const history = array(row.history, parseSnapshot, maxRecords);
  if (
    !history.length ||
    JSON.stringify(history[0]) !== JSON.stringify(watch.latest) ||
    new Set(history.map((item) => item.id)).size !== history.length
  )
    throw new InvalidResponseError();
  assertSnapshotOrder(history);
  if (history.some((item) => instantMicros(item.capturedAt) < instantMicros(watch.createdAt)))
    throw new InvalidResponseError();
  return { ...watch, history };
}
export function parseDetail(value: unknown): WatchDetail {
  return parseHistory(value, 100);
}
export function parseHistoryPage(value: unknown): HistoryPage {
  const row = object(value);
  const items = array(row.items, parseSnapshot, 100);
  const nextCursor = row.nextCursor === null ? null : text(row.nextCursor, 100);
  if (
    new Set(items.map((item) => item.id)).size !== items.length ||
    (nextCursor !== null && nextCursor !== items.at(-1)?.id)
  )
    throw new InvalidResponseError();
  assertSnapshotOrder(items);
  const total = row.total === undefined ? null : row.total;
  if (
    total !== null &&
    (typeof total !== 'number' ||
      !Number.isInteger(total) ||
      total < items.length ||
      total < 1 ||
      total > 500)
  )
    throw new InvalidResponseError();
  return { items, nextCursor, total };
}
export function parseExport(value: unknown): DataExport {
  const row = object(value);
  if (row.formatVersion !== 'manual-export-v1') throw new InvalidResponseError();
  const watches = array(row.watches, (item) => parseHistory(item, 500), 20);
  if (new Set(watches.map((item) => item.id)).size !== watches.length)
    throw new InvalidResponseError();
  const exportedAt = timestamp(row.exportedAt);
  const snapshots = watches.flatMap((watch) => watch.history);
  if (
    new Set(snapshots.map((item) => item.id)).size !== snapshots.length ||
    snapshots.some((item) => instantMicros(item.capturedAt) > instantMicros(exportedAt))
  )
    throw new InvalidResponseError();
  return { formatVersion: 'manual-export-v1', exportedAt, watches };
}

export function assertSnapshotOrder(items: Snapshot[]): void {
  const seen = new Set<string>();
  let previous: Snapshot | undefined;
  for (const item of items) {
    const current = instantMicros(item.capturedAt);
    if (
      seen.has(item.id) ||
      (previous &&
        (current > instantMicros(previous.capturedAt) ||
          (current === instantMicros(previous.capturedAt) &&
            compareOpaqueIds(item.id, previous.id) >= 0)))
    )
      throw new InvalidResponseError();
    seen.add(item.id);
    previous = item;
  }
}

export function parseImportResult(value: unknown): ImportResult {
  const row = object(value);
  const count = row.importedCount;
  const snapshots = row.snapshotCount;
  if (
    typeof count !== 'number' ||
    !Number.isInteger(count) ||
    count < 1 ||
    count > 20 ||
    typeof snapshots !== 'number' ||
    !Number.isInteger(snapshots) ||
    snapshots < count ||
    snapshots > count * 500 ||
    typeof row.replayed !== 'boolean'
  )
    throw new InvalidResponseError();
  return { importedCount: count, snapshotCount: snapshots, replayed: row.replayed };
}
