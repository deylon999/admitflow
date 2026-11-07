import { expect, it } from 'vitest';
import fixture from './fixtures/scenario.json' with { type: 'json' };
import { parseChanges } from '@/entities/admission-scenario';
const scenario = {
  ...fixture,
  previousId: 'before',
  changes: [{ field: 'currentLower', before: 1, after: 2 }],
};
const event = {
  id: 'event-z',
  title: 'Synthetic archive change',
  createdAt: '2026-11-04T00:00:00Z',
  seenAt: null,
  scenario,
};
it('validates owner feed shape and preserves immutable comparison target', () => {
  const page = parseChanges({ items: [event], total: 1, unreadCount: 1, nextCursor: null });
  expect(page.items[0].scenario.previousId).toBe('before');
});
it.each([
  { items: [event, event], total: 2, unreadCount: 2, nextCursor: null },
  { items: [event], total: 0, unreadCount: 0, nextCursor: null },
  { items: [event], total: 1, unreadCount: 2, nextCursor: null },
  { items: [event], total: 1, unreadCount: 1, nextCursor: 'foreign' },
  {
    items: [{ ...event, scenario: { ...scenario, previousId: null } }],
    total: 1,
    unreadCount: 1,
    nextCursor: null,
  },
])('refuses duplicate, inconsistent or unlinked changes', (value) =>
  expect(() => parseChanges(value)).toThrow(),
);
