import { describe, expect, it } from 'vitest';
import {
  parseGroupCatalog,
  parseSourceGroup,
  parseLookup,
  parseDirectionBudget,
  parseCandidate,
} from '../src/lib/source-contracts';

const group = {
  id: 'g',
  universityId: 'u',
  universityName: 'University',
  parentUniversityId: null,
  year: 2026,
  level: 'bachelor',
  title: 'Archive group',
  studyForm: 'full-time',
  funding: 'budget',
  category: 'general',
  seats: 16,
  coverage: 'archive',
  dataKind: 'archive',
  sourceId: 's',
  sourceUrl: 'https://example.org/list',
  sourceState: 'archived',
  snapshotId: 'snapshot',
  fetchedAt: '2026-11-03T17:00:00Z',
  sourceUpdatedAt: null,
  lastCheckedAt: '2026-11-03T17:00:00Z',
  rowCount: 573,
  lookupAvailable: true,
  assessmentAvailable: false,
};
describe('source catalog contracts', () => {
  it('keeps unknown source timestamp and readonly archive state', () => {
    expect(parseSourceGroup(group).sourceUpdatedAt).toBeNull();
    expect(
      parseGroupCatalog({
        items: [group],
        total: 1,
        nextCursor: null,
        facets: { branches: [], years: [2026] },
      }).items,
    ).toHaveLength(1);
  });
  it.each([101, 20_000])(
    'accepts %i global branches independently of the filtered page',
    (count) => {
      const branches = Array.from({ length: count }, (_, index) => ({
        id: `branch-${index}`,
        name: `Synthetic branch ${index}`,
      }));
      const result = parseGroupCatalog({
        items: [group],
        total: 1,
        nextCursor: null,
        facets: { branches, years: [2026] },
      });
      expect(result.items).toHaveLength(1);
      expect(result.facets.branches).toHaveLength(count);
      expect(result.facets.branches[count - 1]).toEqual(branches[count - 1]);
    },
  );
  it('rejects branch facets beyond the supported source catalog capacity', () => {
    expect(() =>
      parseGroupCatalog({
        items: [],
        total: 0,
        nextCursor: null,
        facets: {
          branches: Array.from({ length: 20_001 }, (_, index) => ({
            id: `branch-${index}`,
            name: `Synthetic branch ${index}`,
          })),
          years: [],
        },
      }),
    ).toThrow();
  });
  it.each([
    { branches: null },
    { branches: {} },
    { branches: [null] },
    { branches: [{ id: '', name: 'Synthetic branch' }] },
    { branches: [{ id: 'branch', name: '' }] },
    { branches: [{ id: 'x'.repeat(81), name: 'Synthetic branch' }] },
    { branches: [{ id: 'branch', name: 'x'.repeat(301) }] },
  ])('still rejects malformed branch facets $branches', ({ branches }) => {
    expect(() =>
      parseGroupCatalog({
        items: [],
        total: 0,
        nextCursor: null,
        facets: { branches, years: [] },
      }),
    ).toThrow();
  });
  it.each([
    { sourceUrl: 'javascript:alert(1)' },
    { snapshotId: null },
    { coverage: 'manual' },
    { fetchedAt: 'not-a-date' },
    { assessmentAvailable: true },
    { seats: -1 },
    { rowCount: true },
  ])('refuses unsafe or inconsistent source DTO %s', (changes) => {
    expect(() => parseSourceGroup({ ...group, ...changes })).toThrow();
  });
});

it('validates archive version order, snapshot identity, presence and cursors', async () => {
  const { parseArchiveHistory, assertArchiveOrder } = await import('../src/lib/source-contracts');
  const base = {
    id: 'z',
    assessedAt: '2026-11-03T17:00:00Z',
    modelVersion: 'source-facts-v1',
    group: parseSourceGroup({ ...group, lookupAvailable: false }),
    candidate: null,
    present: false,
  };
  expect(parseArchiveHistory({ items: [base], total: 1, nextCursor: null }).items[0].present).toBe(
    false,
  );
  for (const changed of [
    { present: true },
    { group: { ...base.group, snapshotId: null } },
    { group },
  ])
    expect(() =>
      parseArchiveHistory({ items: [{ ...base, ...changed }], total: 1, nextCursor: null }),
    ).toThrow();
  expect(() => parseArchiveHistory({ items: [base], total: 1, nextCursor: 'other' })).toThrow();
  expect(() => assertArchiveOrder([base, base])).toThrow();
  expect(() => assertArchiveOrder([{ ...base, id: 'a' }, base])).toThrow();
  expect(() =>
    assertArchiveOrder([base, { ...base, id: 'a', group: { ...base.group, year: 2027 } }]),
  ).toThrow();
});

it('refuses contradictory candidate and direction budgets', () => {
  const candidate = {
    rowRef: '1',
    officialRank: 1,
    score: '299.00',
    consent: null,
    priority: null,
    participation: 'unknown',
  };
  const result = {
    group,
    found: true,
    candidate,
    confirmationToken: 'token',
    expiresAt: '2026-11-03T17:05:00Z',
  };
  expect(parseLookup(result).candidate?.consent).toBeNull();
  for (const change of [
    { found: false },
    { confirmationToken: null },
    { candidate: { ...candidate, officialRank: 574 } },
  ])
    expect(() => parseLookup({ ...result, ...change })).toThrow();
  for (const score of [300, 'NaN', '-1', '1001'])
    expect(() => parseCandidate({ ...candidate, score })).toThrow();
  expect(() =>
    parseDirectionBudget({ limit: 20, total: 2, manualCount: 1, archiveCount: 0 }),
  ).toThrow();
});
