import type { CalculationResult, CalculationValues } from './calculator';

export type Snapshot = {
  id: string;
  capturedAt: string;
  sourceKind: 'manual';
  modelVersion: 'manual-v1';
  values: CalculationValues;
  calculation: CalculationResult;
};
export type Watch = {
  id: string;
  university: string;
  title: string;
  sourceUrl: string;
  createdAt: string;
  latest: Snapshot;
};
export type WatchDetail = Watch & { history: Snapshot[] };
export type WatchCreate = {
  university: string;
  title: string;
  sourceUrl: string;
  values: CalculationValues;
};

export type DataExport = {
  formatVersion: 'manual-export-v1';
  exportedAt: string;
  watches: WatchDetail[];
};
export type HistoryPage = { items: Snapshot[]; nextCursor: string | null; total: number | null };
export type ImportResult = { importedCount: number; snapshotCount: number; replayed: boolean };
