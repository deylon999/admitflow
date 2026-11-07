import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { instantMicros } from '@/shared/lib/time';
import { assertSnapshotOrder, parseExport, parseSnapshot } from '@/entities/manual-direction';

it('requires an offset-normalized timestamp within the Python UTC calendar', () => {
  for (const value of ['0001-01-01T00:00:00+00:01', '9999-12-31T23:59:59.999999-00:01'])
    expect(() => instantMicros(value)).toThrow();
  expect(instantMicros('0001-01-01T00:00:00Z')).toBe(-62135596800000000n);
  expect(instantMicros('9999-12-31T23:59:59.999999Z')).toBe(253402300799999999n);
  expect(instantMicros('0001-01-01T01:00:00+01:00')).toBe(instantMicros('0001-01-01T00:00:00Z'));
});

it('rejects rollover dates and preserves timezone and microseconds', () => {
  for (const date of [
    '2026-02-30T00:00:00Z',
    '2025-02-29T00:00:00Z',
    '2026-13-01T00:00:00Z',
    '2026-11-01T24:00:00Z',
    '2026-11-01T00:60:00Z',
    '2026-11-01T00:00:60Z',
    '2026-11-01T00:00:00',
    '2026-11-01T00:00:00+24:00',
  ]) {
    expect(() => parseSnapshot({ ...fixture.latest, capturedAt: date })).toThrow();
  }
  expect(instantMicros('2024-02-29T03:00:00.123456+03:00')).toBe(
    instantMicros('2024-02-29T00:00:00.123456Z'),
  );
  expect(
    instantMicros('2026-11-01T00:00:00.000002Z') - instantMicros('2026-11-01T00:00:00.000001Z'),
  ).toBe(1n);
});

it('rejects page overlap and orders sub-millisecond records before ID tiebreak', () => {
  const older = parseSnapshot({
    ...fixture.latest,
    id: 'z',
    capturedAt: '2026-11-01T00:00:00.000001Z',
  });
  const newer = parseSnapshot({
    ...fixture.latest,
    id: 'a',
    capturedAt: '2026-11-01T00:00:00.000002Z',
  });
  expect(() => assertSnapshotOrder([newer, older])).not.toThrow();
  expect(() => assertSnapshotOrder([older, newer])).toThrow();
  expect(() => assertSnapshotOrder([newer, older, older])).toThrow();
});

it('checks full export ordering, dates and cross-watch snapshot uniqueness', () => {
  const bundle = {
    formatVersion: 'manual-export-v1',
    exportedAt: '2026-11-01T01:00:00Z',
    watches: [{ ...fixture, history: [fixture.latest] }],
  };
  expect(() => parseExport(bundle)).not.toThrow();
  expect(() => parseExport({ ...bundle, exportedAt: '2026-10-01T00:00:00Z' })).toThrow();
  expect(() =>
    parseExport({
      ...bundle,
      watches: [...bundle.watches, { ...bundle.watches[0], id: 'another' }],
    }),
  ).toThrow();
});

it('uses Python code-point ID order and code-point length for Unicode exports', () => {
  const latest = { ...fixture.latest, id: '😀'.repeat(100) };
  const earlier = { ...fixture.latest, id: '\uffff' };
  const bundle = {
    formatVersion: 'manual-export-v1',
    exportedAt: '2026-11-01T01:00:00Z',
    watches: [{ ...fixture, latest, history: [latest, earlier] }],
  };
  expect(() => parseExport(bundle)).not.toThrow();
  expect(() =>
    parseExport({
      ...bundle,
      watches: [{ ...bundle.watches[0], latest: earlier, history: [earlier, latest] }],
    }),
  ).toThrow();
});
