import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { assertChangeOrder, scenarioApi } from '@/entities/admission-scenario';
import { useSessionAccess } from '@/shared/api';

export function useChangeFeed() {
  const client = useQueryClient();
  const access = useSessionAccess();
  const feed = useInfiniteQuery({
    queryKey: ['changes'],
    initialPageParam: null as string | null,
    enabled: access.data === 'active',
    queryFn: ({ pageParam, signal }) => scenarioApi.changes(pageParam, signal),
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    select: (data) => {
      const items = data.pages.flatMap((page) => page.items);
      assertChangeOrder(items);
      return { ...data, items };
    },
  });
  const seen = useMutation({
    mutationFn: scenarioApi.seeChange,
    onSuccess: () => client.invalidateQueries({ queryKey: ['changes'] }),
  });

  return {
    access: access.data,
    feed,
    seen,
    refreshChanges: () => void feed.refetch(),
    loadMoreChanges: () => void feed.fetchNextPage(),
    markSeen: (id: string) => seen.mutate(id),
  };
}
