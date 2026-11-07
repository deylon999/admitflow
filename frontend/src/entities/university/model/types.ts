export type University = {
  id: string;
  name: string;
  officialUrl: string | null;
  provenanceUrl: string;
  verifiedAt: string;
  coverage: 'manual';
  legalName?: string;
  region?: string;
  isBranch?: boolean;
  catalogOrigin?: 'operator' | 'monitoring';
};
export type Catalog = {
  items: University[];
  total: number;
  nextOffset: number | null;
  registryTotal?: number;
  registryEdition?: number;
};
