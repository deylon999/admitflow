import { useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { assertArchiveOrder, sourceApi } from '@/entities/admission-source';

export function useArchiveHistory(id: string) {
  const [show, setShow] = useState(false);
  const [olderId, setOlderId] = useState('');
  const history = useInfiniteQuery({
    queryKey: ['archive-history', id],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam, signal }) => sourceApi.archiveHistory(id, pageParam, signal),
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    enabled: show,
    select: (data) => {
      const items = data.pages.flatMap((page) => page.items);
      assertArchiveOrder(items);
      return { ...data, items };
    },
  });
  const items = history.data?.items ?? [];

  return {
    show,
    toggleHistory: () => setShow((value) => !value),
    setOlderId,
    history,
    items,
    after: items[0],
    before: items.slice(1).find((item) => item.id === olderId) ?? items[1],
    retryHistory: () =>
      void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch()),
    loadMoreHistory: () => void history.fetchNextPage(),
  };
}
