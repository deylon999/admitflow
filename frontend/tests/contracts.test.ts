import { describe, expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { InvalidResponseError, parseCatalog, parseDetail, parseSnapshot, parseWatch, parseWatches } from '../src/lib/contracts';

describe('shared manual API contract', () => {
  it('accepts the exact response also checked against FastAPI', () => {
    expect(parseWatch(fixture)).toEqual(fixture);
    expect(parseDetail({ ...fixture, history: [fixture.latest] }).history).toHaveLength(1);
  });
  it.each([
    { ...fixture.latest, calculation: { ...fixture.latest.calculation, place: 1 } },
    { ...fixture.latest, calculation: { ...fixture.latest.calculation, state: 'out' } },
    { ...fixture.latest, values: { ...fixture.latest.values, rank: '120' } },
    { ...fixture.latest, values: { ...fixture.latest.values, excluded: 120 } },
    { ...fixture.latest, sourceKind: 'automatic' },
    { ...fixture.latest, modelVersion: 'unknown-v99' },
    { ...fixture.latest, capturedAt: 'yesterday' },
    { ...fixture.latest, capturedAt: '2026-11-01T12:00:00' },
  ])('rejects inconsistent or unknown snapshots %#', snapshot => {
    expect(() => parseSnapshot(snapshot)).toThrow(InvalidResponseError);
  });
  it.each(['javascript:alert(1)', 'https://user:password@example.org/list', 'file:///etc/passwd'])('rejects unsafe source %s', sourceUrl => {
    expect(() => parseWatch({ ...fixture, sourceUrl })).toThrow(InvalidResponseError);
  });
  it('rejects malformed lists and contradictory history', () => {
    expect(() => parseWatches({ items: [fixture] })).toThrow(InvalidResponseError);
    expect(() => parseWatches([fixture, fixture])).toThrow(InvalidResponseError);
    expect(() => parseDetail({ ...fixture, history: [] })).toThrow(InvalidResponseError);
    expect(() => parseDetail({ ...fixture, history: [{ ...fixture.latest, id: 'another-id' }] })).toThrow(InvalidResponseError);
  });
  it('does not accept an unsupported catalog integration as manual', () => {
    const item = { id: 'example', name: 'Test', officialUrl: 'https://example.org', provenanceUrl: 'https://example.org/list', verifiedAt: '2026-11-01T00:00:00Z', coverage: 'manual' };
    expect(parseCatalog({ items: [item], total: 1 }).items).toHaveLength(1);
    expect(() => parseCatalog({ items: [{ ...item, coverage: 'automatic' }], total: 1 })).toThrow(InvalidResponseError);
    expect(() => parseCatalog({ items: [item], total: 0 })).toThrow(InvalidResponseError);
  });
  it('accepts registry metadata without inventing a missing site and rejects bad pagination', () => {
    const item = { id: 'miccedu-123', name: 'University', legalName: 'Full legal name', region: 'Region', isBranch: true, officialUrl: null, provenanceUrl: 'https://monitoring.miccedu.ru/iam/2025/_vpo/inst.php?id=123', verifiedAt: '2026-11-05T00:00:00Z', coverage: 'manual', catalogOrigin: 'monitoring' };
    const data = parseCatalog({ items: [item], total: 51, nextOffset: 50, registryTotal: 1257, registryEdition: 2025 });
    expect(data.items[0].officialUrl).toBeNull();
    expect(data.items[0].isBranch).toBe(true);
    expect(data.nextOffset).toBe(50);
    for (const nextOffset of [-1, 0, 51, '50']) expect(() => parseCatalog({ items: [item], total: 51, nextOffset })).toThrow(InvalidResponseError);
  });
});
