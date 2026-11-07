import { InvalidResponseError, object, timestamp } from '@/shared/api';

export type Coverage = {
  registeredSources: number;
  reviewedSources: number;
  importedSources: number;
  importedGroups: number;
  importedUniversities: number;
  importedRows: number;
  archiveImportedGroups: number;
  conditionalGroups: number;
  lastImportedAt: string | null;
  catalogUniversities: number;
  automaticSources: number;
  publishedGroups: number;
  freshGroups: number;
  archiveGroups: number;
  nationalTotal: null;
  generatedAt: string;
};

export function parseCoverage(value: unknown): Coverage {
  const row = object(value);
  const counts = [
    'catalogUniversities',
    'automaticSources',
    'publishedGroups',
    'freshGroups',
    'archiveGroups',
    'registeredSources',
    'reviewedSources',
    'importedSources',
    'importedGroups',
    'importedUniversities',
    'importedRows',
    'archiveImportedGroups',
    'conditionalGroups',
  ] as const;
  for (const key of counts)
    if (typeof row[key] !== 'number' || !Number.isSafeInteger(row[key]) || row[key] < 0)
      throw new InvalidResponseError();
  const result = Object.fromEntries(counts.map((key) => [key, row[key]])) as Pick<
    Coverage,
    (typeof counts)[number]
  >;
  if (
    result.publishedGroups > result.automaticSources ||
    result.freshGroups + result.archiveGroups > result.publishedGroups ||
    result.reviewedSources > result.registeredSources ||
    result.importedSources > result.reviewedSources ||
    result.importedGroups > result.importedSources ||
    result.importedUniversities > result.catalogUniversities ||
    result.importedUniversities > result.importedGroups ||
    result.archiveImportedGroups > result.importedGroups ||
    result.conditionalGroups > result.importedGroups ||
    row.nationalTotal !== null
  )
    throw new InvalidResponseError();
  if (
    (result.importedSources === 0 && row.lastImportedAt !== null) ||
    (result.importedSources > 0 && row.lastImportedAt === null)
  )
    throw new InvalidResponseError();
  return {
    ...result,
    lastImportedAt: row.lastImportedAt === null ? null : timestamp(row.lastImportedAt),
    nationalTotal: null,
    generatedAt: timestamp(row.generatedAt),
  };
}
