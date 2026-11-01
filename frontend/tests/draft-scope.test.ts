import { expect, it } from 'vitest';
import { parseSession } from '../src/lib/contracts';

it('requires a valid scope when present and supports an older API without recovery', () => {
  const info = { expiresAt: '2026-12-01T00:00:00Z' };
  expect(parseSession(info)).toEqual(info);
  expect(parseSession({ ...info, draftScope: 'a'.repeat(64) }).draftScope).toBe('a'.repeat(64));
  for (const draftScope of [null, '', 'token', 'A'.repeat(64), 'a'.repeat(65), 123]) expect(() => parseSession({ ...info, draftScope })).toThrow();
});
