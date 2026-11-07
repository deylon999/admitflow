import type { Scenario } from '@/entities/admission-scenario';
import type { SourceGroup } from '@/entities/admission-source';
import { InvalidResponseError } from '@/shared/api';

export function validateScenario(
  item: Scenario,
  id: string,
  group: SourceGroup,
  assessmentId?: string,
) {
  if (
    item.subscriptionId !== id ||
    item.groupId !== group.id ||
    item.sourceId !== group.sourceId ||
    (assessmentId !== undefined && item.id !== assessmentId)
  ) {
    throw new InvalidResponseError();
  }
  return item;
}
