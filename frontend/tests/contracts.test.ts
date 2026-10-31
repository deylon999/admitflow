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
});
