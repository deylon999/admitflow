import { expect, test } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { parseWatch } from '@/entities/manual-direction';
import { selectWatches } from '@/entities/manual-direction';

test('filters do not mutate stored watches; date ordering retains microseconds', () => {
  const a = parseWatch({
    ...fixture,
    id: 'a',
    university: 'Первый вуз',
    latest: { ...fixture.latest, capturedAt: '2026-11-01T00:00:00.000001Z' },
  });
  const b = parseWatch({
    ...fixture,
    id: 'b',
    university: 'Второй вуз',
    latest: { ...fixture.latest, capturedAt: '2026-11-01T00:00:00.000002Z' },
  });
  const list = [a, b];
  expect(selectWatches(list, 'ПЕРВЫЙ   тестовое', 'safe', 'updated')).toEqual([a]);
  expect(selectWatches(list, '', 'all', 'updated')).toEqual([b, a]);
  expect(selectWatches(list, '', 'out', 'updated')).toEqual([]);
  expect(list).toEqual([a, b]);
});
