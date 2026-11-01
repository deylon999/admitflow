import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { InvalidResponseError, parseDetail, parseExport } from '../src/lib/contracts';

it('accepts the full export while detail remains bounded to 100 records', () => {
  const history = Array.from({ length: 150 }, (_, index) => ({ ...fixture.latest, id: `snapshot-${index}` }));
  const watch = { ...fixture, latest: history[0], history };
  const data = { formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T00:00:00Z', watches: [watch] };
  expect(parseExport(data).watches[0].history).toHaveLength(150);
  expect(() => parseDetail(watch)).toThrow(InvalidResponseError);
  expect(() => parseExport({ ...data, formatVersion: 'unknown' })).toThrow(InvalidResponseError);
  expect(() => parseExport({ ...data, watches: [watch, watch] })).toThrow(InvalidResponseError);
});
