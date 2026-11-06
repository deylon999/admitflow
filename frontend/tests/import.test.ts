import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import {
  decodeImportBytes,
  importKey,
  MAX_IMPORT_FILE_BYTES,
  parseImportText,
} from '../src/lib/import';
import { parseImportResult } from '../src/lib/contracts';

const bundle = {
  formatVersion: 'manual-export-v1',
  exportedAt: '2026-11-01T01:00:00Z',
  watches: [{ ...fixture, history: [fixture.latest] }],
};

it('decodes valid UTF-8 and BOM without silently repairing broken bytes', () => {
  const text = JSON.stringify(bundle);
  expect(
    parseImportText(decodeImportBytes(new TextEncoder().encode('\ufeff' + text).buffer)),
  ).toEqual(parseImportText(text));
  for (const bytes of [
    [0xc3, 0x28],
    [0xf0, 0x9f],
    [0xed, 0xa0, 0x80],
  ])
    expect(() => decodeImportBytes(new Uint8Array(bytes).buffer)).toThrow('UTF-8');
});

it('validates file contents and uses a stable key for an unchanged export', async () => {
  const parsed = parseImportText(JSON.stringify(bundle));
  expect(await importKey(parsed)).toBe(
    await importKey(parseImportText(JSON.stringify(bundle, null, 2))),
  );
  expect(await importKey(parsed)).toMatch(/^import-v1-[a-f0-9]{64}$/);
  expect(() => parseImportText('{broken')).toThrow('корректную выгрузку');
  expect(() => parseImportText(JSON.stringify({ ...bundle, watches: [] }))).toThrow(
    'нет сохранённых',
  );
  expect(() =>
    parseImportText(JSON.stringify({ ...bundle, formatVersion: 'automatic' })),
  ).toThrow();
});

it('rejects impossible import result counts', () => {
  expect(parseImportResult({ importedCount: 1, snapshotCount: 500, replayed: true }).replayed).toBe(
    true,
  );
  for (const row of [
    { importedCount: 0, snapshotCount: 1, replayed: false },
    { importedCount: 1, snapshotCount: 501, replayed: false },
    { importedCount: 1, snapshotCount: 1, replayed: 'false' },
  ])
    expect(() => parseImportResult(row)).toThrow();
});

it('matches server date limits before confirming an import', () => {
  const now = Date.parse('2026-11-01T01:00:00Z');
  expect(() =>
    parseImportText(JSON.stringify({ ...bundle, exportedAt: '2026-11-01T01:05:00Z' }), now),
  ).not.toThrow();
  expect(() =>
    parseImportText(JSON.stringify({ ...bundle, exportedAt: '2026-11-01T01:05:00.000001Z' }), now),
  ).toThrow('Даты файла');
  expect(() =>
    parseImportText(
      JSON.stringify({
        ...bundle,
        watches: [{ ...bundle.watches[0], createdAt: '1999-12-31T23:59:59Z' }],
      }),
      now,
    ),
  ).toThrow('Даты файла');
});

it('accepts its own maximum-count pretty export with full-length IDs and numbers', () => {
  const watches = Array.from({ length: 20 }, (_, watch) => {
    const history = Array.from({ length: 500 }, (_, snapshot) => ({
      ...fixture.latest,
      id: `${String(watch).padStart(8, '0')}-0000-0000-0000-${String(500 - snapshot).padStart(12, '0')}`,
      capturedAt: '2026-11-01T00:00:00.123456+00:00',
      values: { rank: 1_000_000, seats: 1_000_000, excluded: 0, noConsent: 0 },
      calculation: {
        ...fixture.latest.calculation,
        place: 1_000_000,
        worstPlace: 1_000_000,
        seats: 1_000_000,
      },
    }));
    return { ...fixture, id: `watch-${watch}`, latest: history[0], history };
  });
  const text = JSON.stringify({ ...bundle, watches }, null, 2);
  const size = new TextEncoder().encode(text).byteLength;
  expect(size).toBeGreaterThan(6 * 1024 * 1024);
  expect(size).toBeLessThan(MAX_IMPORT_FILE_BYTES);
  expect(parseImportText(text).watches).toHaveLength(20);
});
