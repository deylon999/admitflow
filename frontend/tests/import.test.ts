import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { importKey, parseImportText } from '../src/lib/import';
import { parseImportResult } from '../src/lib/contracts';

const bundle = { formatVersion: 'manual-export-v1', exportedAt: '2026-11-01T01:00:00Z', watches: [{ ...fixture, history: [fixture.latest] }] };

it('validates file contents and uses a stable key for an unchanged export', async () => {
  const parsed = parseImportText(JSON.stringify(bundle));
  expect(await importKey(parsed)).toBe(await importKey(parseImportText(JSON.stringify(bundle, null, 2))));
  expect(await importKey(parsed)).toMatch(/^import-v1-[a-f0-9]{64}$/);
  expect(() => parseImportText('{broken')).toThrow('корректную выгрузку');
  expect(() => parseImportText(JSON.stringify({ ...bundle, watches: [] }))).toThrow('нет сохранённых');
  expect(() => parseImportText(JSON.stringify({ ...bundle, formatVersion: 'automatic' }))).toThrow();
});

it('rejects impossible import result counts', () => {
  expect(parseImportResult({ importedCount: 1, snapshotCount: 500, replayed: true }).replayed).toBe(true);
  for (const row of [{ importedCount: 0, snapshotCount: 1, replayed: false }, { importedCount: 1, snapshotCount: 501, replayed: false }, { importedCount: 1, snapshotCount: 1, replayed: 'false' }]) expect(() => parseImportResult(row)).toThrow();
});
