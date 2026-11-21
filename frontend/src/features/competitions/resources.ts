import { useUrlFilters } from '../../app/useUrlFilters';
import { useResource } from '../../shared/resource';
import { competition, competitionRows, competitionSummary } from './decode';

function useCompetition(id: string) {
  const base = `competitions/${encodeURIComponent(id)}`;
  return { base, info: useResource(base, competition) };
}

export function useCompetitionRows(id: string) {
  const { base, info } = useCompetition(id);
  const { params, update } = useUrlFilters();
  const consent = params.get('consent') ?? '';
  const priority = params.get('priority') ?? '';
  const offset = Number(params.get('offset') ?? 0);
  const rankFrom = params.get('rankFrom') ?? '';
  const query = new URLSearchParams({ offset: String(offset) });
  if (consent) query.set('consent', consent);
  if (priority) query.set('priority', priority);
  if (rankFrom) query.set('rankFrom', rankFrom);
  const rows = useResource(`${base}/rows?${query}`, competitionRows);
  return { info, consent, priority, offset, rankFrom, update, rows };
}

export function useCompetitionSummary(id: string) {
  const { base, info } = useCompetition(id);
  return { info, summary: useResource(`${base}/summary`, competitionSummary) };
}
