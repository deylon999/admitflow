import { useQuery } from '@tanstack/react-query';
import { scenarioApi } from '@/entities/admission-scenario';
import type { SourceGroup } from '@/entities/admission-source';
import { validateScenario } from './validateScenario';

export function useScenarioComparison(id: string, group: SourceGroup, target: string | null) {
  const detail = useQuery({
    queryKey: ['scenario-detail', id, target],
    enabled: !!target,
    queryFn: async ({ signal }) =>
      validateScenario(await scenarioApi.scenarioDetail(id, target!, signal), id, group, target!),
  });
  const previousId = detail.data?.previousId;
  const previous = useQuery({
    queryKey: ['scenario-detail', id, previousId],
    enabled: !!target && !!previousId,
    queryFn: async ({ signal }) =>
      validateScenario(
        await scenarioApi.scenarioDetail(id, previousId!, signal),
        id,
        group,
        previousId!,
      ),
  });

  return {
    detail,
    previous,
    previousId,
    retryComparison: () => {
      void detail.refetch();
      if (previousId) void previous.refetch();
    },
  };
}
