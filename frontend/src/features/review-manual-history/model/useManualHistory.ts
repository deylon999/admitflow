import { useInfiniteQuery } from '@tanstack/react-query';
import { assertSnapshotOrder, manualDirectionApi } from '@/entities/manual-direction';

export function useManualHistory(id: string, enabled: boolean, latestSnapshot: string) {
  return useInfiniteQuery({
    queryKey: ['history', id, latestSnapshot],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam, signal }) => manualDirectionApi.history(id, pageParam, signal),
    getNextPageParam: (page) => page.nextCursor,
    enabled,
    select: (data) => {
      const snapshots = data.pages.flatMap((page) => page.items);
      assertSnapshotOrder(snapshots);
      return { ...data, snapshots };
    },
  });
}
