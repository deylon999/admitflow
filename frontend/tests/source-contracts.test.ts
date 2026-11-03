import { describe, expect, it } from 'vitest';
import { parseGroupCatalog, parseSourceGroup, parseLookup, parseDirectionBudget, parseCandidate } from '../src/lib/source-contracts';

const group = { id: 'g', universityId: 'u', universityName: 'University', parentUniversityId: null, year: 2026, level: 'bachelor', title: 'Archive group', studyForm: 'full-time', funding: 'budget', category: 'general', seats: 16, coverage: 'archive', dataKind: 'archive', sourceId: 's', sourceUrl: 'https://example.org/list', sourceState: 'archived', snapshotId: 'snapshot', fetchedAt: '2026-11-03T17:00:00Z', sourceUpdatedAt: null, lastCheckedAt: '2026-11-03T17:00:00Z', rowCount: 573, lookupAvailable: true, assessmentAvailable: false };
describe('source catalog contracts', () => {
  it('keeps unknown source timestamp and readonly archive state', () => {
    expect(parseSourceGroup(group).sourceUpdatedAt).toBeNull();
    expect(parseGroupCatalog({ items: [group], total: 1, nextCursor: null, facets: { branches: [], years: [2026] } }).items).toHaveLength(1);
  });
  it.each([{ sourceUrl: 'javascript:alert(1)' }, { snapshotId: null }, { coverage: 'manual' }, { fetchedAt: 'not-a-date' }, { assessmentAvailable: true }, { seats: -1 }, { rowCount: true }])('refuses unsafe or inconsistent source DTO %s', changes => {
    expect(() => parseSourceGroup({ ...group, ...changes })).toThrow();
  });
});

it('refuses contradictory candidate and direction budgets', () => {
  const candidate = { rowRef: '1', officialRank: 1, score: '299.00', consent: null, priority: null, participation: 'unknown' };
  const result = { group, found: true, candidate, confirmationToken: 'token', expiresAt: '2026-11-03T17:05:00Z' };
  expect(parseLookup(result).candidate?.consent).toBeNull();
  for (const change of [{ found: false }, { confirmationToken: null }, { candidate: { ...candidate, officialRank: 574 } }]) expect(() => parseLookup({ ...result, ...change })).toThrow();
  for (const score of [300, 'NaN', '-1', '1001']) expect(() => parseCandidate({ ...candidate, score })).toThrow();
  expect(() => parseDirectionBudget({ limit: 20, total: 2, manualCount: 1, archiveCount: 0 })).toThrow();
});
