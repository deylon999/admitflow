import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { parseHistoryPage } from '@/entities/manual-direction';

it('validates cursor, uniqueness and descending time before showing a page', () => {
  const item = fixture.latest;
  expect(parseHistoryPage({ items: [item], nextCursor: item.id }).items).toHaveLength(1);
  expect(parseHistoryPage({ items: [], nextCursor: null }).items).toEqual([]);
  for (const row of [
    { items: [item], nextCursor: 'other' },
    { items: [item, item], nextCursor: null },
    {
      items: [item, { ...item, id: 'later', capturedAt: '2026-11-02T00:00:00Z' }],
      nextCursor: null,
    },
  ])
    expect(() => parseHistoryPage(row)).toThrow();
});
