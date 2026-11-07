import { request, read, ensureSession } from '@/shared/api';
import { parseScenario, parseScenarioPage } from '../model/scenario-contracts';
import { parseChange, parseChanges } from '../model/change-contracts';

export const scenarioApi = {
  scenario: (id: string, signal?: AbortSignal) =>
    read(`/subscriptions/${encodeURIComponent(id)}/scenario`, parseScenario, signal),
  scenarioDetail: (id: string, assessment: string, signal?: AbortSignal) =>
    read(
      `/subscriptions/${encodeURIComponent(id)}/scenarios/${encodeURIComponent(assessment)}`,
      parseScenario,
      signal,
    ),
  scenarioHistory: (id: string, before: string | null, signal?: AbortSignal) =>
    read(
      `/subscriptions/${encodeURIComponent(id)}/scenario-history?limit=20${before ? `&before=${encodeURIComponent(before)}` : ''}`,
      parseScenarioPage,
      signal,
    ),
  changes: (before: string | null, signal?: AbortSignal) =>
    read(
      `/changes?limit=20${before ? `&before=${encodeURIComponent(before)}` : ''}`,
      parseChanges,
      signal,
    ),
  async seeChange(id: string) {
    await ensureSession();
    return parseChange(
      await request(`/changes/${encodeURIComponent(id)}/seen`, { method: 'POST' }),
    );
  },
};
