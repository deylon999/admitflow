import { request, read, ensureSession, InvalidResponseError } from '@/shared/api';
import {
  parseGroupCatalog,
  parseLookup,
  parseSubscriptionSaved,
  parseArchiveDirections,
  parseArchiveHistory,
  parseArchiveExport,
  parseSourceChecks,
  parseDirectionBudget,
} from '../model/contracts';
import { parseCoverage } from '../model/coverage';

export const sourceApi = {
  groups: async (
    filters: { q: string; universityId: string; branchId: string; year: string },
    after: string | null = null,
    signal?: AbortSignal,
  ) => {
    const params = new URLSearchParams(Object.entries(filters).filter(([, value]) => value !== ''));
    if (after) params.set('after', after);
    return parseGroupCatalog(await request(`/groups?${params}`, { signal }, 'public'));
  },
  async lookup(sourceId: string, publicCode: string) {
    await ensureSession();
    const value = parseLookup(
      await request(`/sources/${encodeURIComponent(sourceId)}/lookup`, {
        method: 'POST',
        body: JSON.stringify({ publicCode }),
      }),
    );
    if (value.group.sourceId !== sourceId) throw new InvalidResponseError();
    return value;
  },
  async subscribe(confirmationToken: string) {
    await ensureSession();
    return parseSubscriptionSaved(
      await request('/subscriptions', {
        method: 'POST',
        body: JSON.stringify({ confirmationToken }),
      }),
    );
  },
  subscriptions: (signal?: AbortSignal) => read('/subscriptions', parseArchiveDirections, signal),
  async removeSubscription(id: string) {
    await ensureSession();
    await request(`/subscriptions/${encodeURIComponent(id)}`, { method: 'DELETE' });
  },
  archiveHistory: (id: string, before: string | null, signal?: AbortSignal) =>
    read(
      `/subscriptions/${encodeURIComponent(id)}/history?limit=20${before ? `&before=${encodeURIComponent(before)}` : ''}`,
      parseArchiveHistory,
      signal,
    ),
  exportArchive: () => read('/archive-export', parseArchiveExport),
  sourceChecks: async (id: string, signal?: AbortSignal) =>
    parseSourceChecks(await request(`/sources/${encodeURIComponent(id)}/checks`, { signal })),
  directionBudget: (signal?: AbortSignal) =>
    read('/direction-budget', parseDirectionBudget, signal),
  coverage: async () => parseCoverage(await request('/coverage', {}, 'public')),
};
