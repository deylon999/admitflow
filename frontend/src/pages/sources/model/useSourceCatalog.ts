import { useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { sourceApi } from '@/entities/admission-source';

export type SourceFilters = { q: string; universityId: string; branchId: string; year: string };

export function useSourceCatalog() {
  const [filters, setFilters] = useState<SourceFilters>({
    q: '',
    universityId: '',
    branchId: '',
    year: '',
  });
  const [selected, setSelected] = useState<string | null>(null);
  const catalog = useInfiniteQuery({
    queryKey: ['group-catalog', filters],
    queryFn: ({ pageParam, signal }) => sourceApi.groups(filters, pageParam, signal),
    initialPageParam: null as string | null,
    getNextPageParam: (page) => page.nextCursor ?? undefined,
  });
  const items = [
    ...new Map(
      catalog.data?.pages.flatMap((page) => page.items).map((item) => [item.id, item]) ?? [],
    ).values(),
  ];

  return {
    filters,
    setFilters,
    selected,
    setSelected,
    catalog,
    items,
    facets: catalog.data?.pages[0].facets,
  };
}
