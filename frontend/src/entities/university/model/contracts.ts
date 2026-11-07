import { InvalidResponseError, object, text, timestamp, url, array } from '@/shared/api';
import type { University, Catalog } from './types';

export function parseCatalog(value: unknown): Catalog {
  const row = object(value);
  const items = array(
    row.items,
    (value) => {
      const item = object(value);
      if (item.coverage !== 'manual') throw new InvalidResponseError();
      if (
        (item.isBranch != null && typeof item.isBranch !== 'boolean') ||
        (item.catalogOrigin != null &&
          !['operator', 'monitoring'].includes(String(item.catalogOrigin)))
      )
        throw new InvalidResponseError();
      return {
        id: text(item.id, 80),
        name: text(item.name, 300),
        officialUrl: item.officialUrl === null ? null : url(item.officialUrl),
        provenanceUrl: url(item.provenanceUrl),
        verifiedAt: timestamp(item.verifiedAt),
        coverage: 'manual' as const,
        legalName: item.legalName == null ? undefined : text(item.legalName, 1500),
        region: item.region == null ? undefined : text(item.region, 120),
        isBranch: item.isBranch == null ? undefined : (item.isBranch as boolean),
        catalogOrigin: item.catalogOrigin as University['catalogOrigin'],
      };
    },
    50,
  );
  if (
    typeof row.total !== 'number' ||
    !Number.isSafeInteger(row.total) ||
    row.total < items.length ||
    new Set(items.map((item) => item.id)).size !== items.length
  )
    throw new InvalidResponseError();
  const nextOffset = row.nextOffset ?? null;
  if (
    nextOffset !== null &&
    (typeof nextOffset !== 'number' ||
      !Number.isSafeInteger(nextOffset) ||
      nextOffset < items.length ||
      nextOffset < 1 ||
      nextOffset >= row.total ||
      !items.length)
  )
    throw new InvalidResponseError();
  for (const key of ['registryTotal', 'registryEdition'])
    if (
      row[key] != null &&
      (typeof row[key] !== 'number' || !Number.isSafeInteger(row[key]) || Number(row[key]) < 1)
    )
      throw new InvalidResponseError();
  return {
    items,
    total: row.total,
    nextOffset,
    ...(row.registryTotal != null ? { registryTotal: row.registryTotal as number } : {}),
    ...(row.registryEdition != null ? { registryEdition: row.registryEdition as number } : {}),
  };
}
