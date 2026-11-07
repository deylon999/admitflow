import { useDeferredValue } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { universityApi } from '../api/university-api';

export function useUniversityCatalog(search: string, enabled = true) {
  const query = useDeferredValue(search);
  const catalog = useInfiniteQuery({
    queryKey: ['universities', query],
    initialPageParam: 0,
    queryFn: ({ signal, pageParam }) => universityApi.universities(query, signal, pageParam),
    getNextPageParam: (page) => page.nextOffset ?? undefined,
    enabled,
    staleTime: 300_000,
  });

  return { catalog, query };
}
