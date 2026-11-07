import { useState } from 'react';
import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { assertScenarioOrder, scenarioApi } from '@/entities/admission-scenario';
import type { SourceGroup } from '@/entities/admission-source';
import { validateScenario } from './validateScenario';

export function useArchiveScenario(id: string, group: SourceGroup) {
  const [showHistory, setShowHistory] = useState(false);
  const client = useQueryClient();
  const current = useQuery({
    queryKey: ['scenario', id, group.snapshotId],
    queryFn: async ({ signal }) =>
      validateScenario(await scenarioApi.scenario(id, signal), id, group),
  });
  const history = useInfiniteQuery({
    queryKey: ['scenario-history', id, group.snapshotId],
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam, signal }) => {
      const page = await scenarioApi.scenarioHistory(id, pageParam, signal);
      page.items.forEach((item) => validateScenario(item, id, group));
      return page;
    },
    getNextPageParam: (page) => page.nextCursor ?? undefined,
    enabled: showHistory,
    select: (data) => {
      const items = data.pages.flatMap((page) => page.items);
      assertScenarioOrder(items);
      return { ...data, items };
    },
  });

  return {
    showHistory,
    toggleHistory: () => setShowHistory((show) => !show),
    current,
    history,
    refreshDirection: () => void client.invalidateQueries({ queryKey: ['archive-directions'] }),
    retryHistory: () =>
      void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch()),
    loadMoreHistory: () => void history.fetchNextPage(),
  };
}
