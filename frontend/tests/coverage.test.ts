import { expect, it } from 'vitest';
import { parseCoverage } from '@/entities/admission-source';

const base = {
  registeredSources: 0,
  reviewedSources: 0,
  importedSources: 0,
  importedGroups: 0,
  importedUniversities: 0,
  importedRows: 0,
  archiveImportedGroups: 0,
  conditionalGroups: 0,
  lastImportedAt: null,
  catalogUniversities: 2,
  automaticSources: 0,
  publishedGroups: 0,
  freshGroups: 0,
  archiveGroups: 0,
  nationalTotal: null,
  generatedAt: '2026-11-01T00:00:00Z',
};
it('keeps catalog separate and refuses invented or inconsistent coverage', () => {
  expect(parseCoverage(base)).toEqual(base);
  for (const changes of [
    { nationalTotal: 1000 },
    { automaticSources: true },
    { publishedGroups: 1 },
    { freshGroups: 1 },
    { catalogUniversities: -1 },
    { reviewedSources: 1 },
    { importedSources: 1 },
    { importedUniversities: 1 },
    { conditionalGroups: 1 },
    { lastImportedAt: base.generatedAt },
  ])
    expect(() => parseCoverage({ ...base, ...changes })).toThrow();
});
