import { expect, it } from 'vitest';
import { parseCoverage } from '../src/lib/contracts';

const base = { catalogUniversities: 2, automaticSources: 0, publishedGroups: 0, freshGroups: 0, archiveGroups: 0, nationalTotal: null, generatedAt: '2026-11-01T00:00:00Z' };
it('keeps catalog separate and refuses invented or inconsistent coverage', () => {
  expect(parseCoverage(base)).toEqual(base);
  for (const changes of [{ nationalTotal: 1000 }, { automaticSources: true }, { publishedGroups: 1 }, { freshGroups: 1 }, { catalogUniversities: -1 }]) expect(() => parseCoverage({ ...base, ...changes })).toThrow();
});
