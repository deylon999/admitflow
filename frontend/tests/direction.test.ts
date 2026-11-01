import { expect, it } from 'vitest';
import { validateDirection } from '../src/lib/direction';

const valid = { university: 'Test', title: 'Group', sourceUrl: 'https://example.org/list', values: { rank: 120, seats: 90, excluded: 30, noConsent: 16 } };
it('points to the first metadata error before numeric errors', () => {
  expect(validateDirection({ ...valid, university: ' ' }).firstInvalidId).toBe('university');
  expect(validateDirection({ ...valid, title: ' ' }).firstInvalidId).toBe('direction-title');
  for (const sourceUrl of ['javascript:alert(1)', 'https://user:pass@example.org/list', 'not a url', 'https://example.org/' + 'x'.repeat(2048)]) expect(validateDirection({ ...valid, sourceUrl }).firstInvalidId).toBe('source-url');
  expect(validateDirection(valid).firstInvalidId).toBeUndefined();
});
it('identifies invalid groups and skips readonly metadata when updating numbers', () => {
  const result = validateDirection({ ...valid, values: { ...valid.values, noConsent: 90 } });
  expect(result.firstInvalidId).toBe('tracker-excluded');
  expect(result.calculation?.fields).toEqual(['excluded', 'noConsent']);
  expect(validateDirection({ ...valid, university: '', title: '', sourceUrl: '' }, true).firstInvalidId).toBeUndefined();
});
