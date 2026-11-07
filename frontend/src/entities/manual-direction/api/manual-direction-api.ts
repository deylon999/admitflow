import { request, read, ensureSession } from '@/shared/api';
import type { CalculationValues } from '../model/calculator';
import type { DataExport, WatchCreate } from '../model/types';
import {
  parseWatches,
  parseDetail,
  parseHistoryPage,
  parseWatch,
  parseSnapshot,
  parseExport,
  parseImportResult,
} from '../model/contracts';

export const manualDirectionApi = {
  list: (signal?: AbortSignal) => read('/watches', parseWatches, signal),
  detail: (id: string) => read(`/watches/${encodeURIComponent(id)}`, parseDetail),
  history: (id: string, before: string | null, signal?: AbortSignal) =>
    read(
      `/watches/${encodeURIComponent(id)}/history${before ? `?before=${encodeURIComponent(before)}` : ''}`,
      parseHistoryPage,
      signal,
    ),
  async create(body: WatchCreate, key?: string) {
    await ensureSession();
    return parseWatch(
      await request('/watches', {
        method: 'POST',
        body: JSON.stringify(body),
        headers: key ? { 'Idempotency-Key': key } : undefined,
      }),
    );
  },
  async update(id: string, values: CalculationValues, key?: string, expectedSnapshot?: string) {
    await ensureSession();
    return parseSnapshot(
      await request(`/watches/${encodeURIComponent(id)}/snapshots`, {
        method: 'POST',
        body: JSON.stringify(values),
        headers: {
          ...(key ? { 'Idempotency-Key': key } : {}),
          ...(expectedSnapshot ? { 'X-Expected-Snapshot': expectedSnapshot } : {}),
        },
      }),
    );
  },
  async remove(id: string) {
    await ensureSession();
    await request(`/watches/${encodeURIComponent(id)}`, { method: 'DELETE' });
  },
  exportData: () => read('/export', parseExport),
  async importData(bundle: DataExport, key: string) {
    await ensureSession();
    return parseImportResult(
      await request('/import', {
        method: 'POST',
        body: JSON.stringify({ bundle }),
        headers: { 'Idempotency-Key': key },
      }),
    );
  },
};
