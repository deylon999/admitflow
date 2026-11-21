import { useUrlFilters } from '../../app/useUrlFilters';
import { RouteLink } from '../../app/RouteLink';
import { useResource } from '../../shared/resource';
import { ResourceState } from '../../shared/ResourceState';
import { Action, EmptyMessage, PageTitle } from '../../shared/UI';
import { competitionGroups } from './decode';
import { unknown } from './format';

export function CompetitionsIndex() {
  const { params, update } = useUrlFilters();
  const cursor = params.get('after') ?? '';
  const r = useResource('groups?' + new URLSearchParams({ limit: '50', after: cursor }), competitionGroups);
  const lists = r.data?.items.filter(g => g.coverage === 'archive' || g.coverage === 'automatic') ?? [];
  return <>
    <PageTitle kicker="КОНКУРСНЫЕ СПИСКИ" title="Импортированные конкурсные списки"
      description="Официальный порядок списка без кодов поступающих. Свою строку видно после подтверждения записи в «Мои направления»."
      action={<Action to="/app/watchlist" variant="outline">Мои направления ↗</Action>} />
    <ResourceState {...r} hasData={!!r.data}>
      {r.data && (lists.length ? <div className="af-program-grid">{lists.map(g => <article className="af-program-card af-catalog-card" key={g.id}>
        <div className="af-program-card__logo af-program-card__logo--blue">{g.universityName.slice(0, 2)}</div>
        <div className="af-program-card__main">
          <div className="af-program-card__university">{g.universityName}</div>
          <h3><RouteLink to={`/app/competitions/${encodeURIComponent(g.id)}`}>{g.title}</RouteLink></h3>
          <p>{g.year} · {g.coverage === 'archive' ? 'Архив' : 'Автоматическое обновление'} · Мест: {g.seats ?? unknown}</p>
        </div>
        <div className="af-program-card__actions"><RouteLink to={`/app/competitions/${encodeURIComponent(g.id)}`} className="af-small-link">Список ↗</RouteLink></div>
      </article>)}</div> : <EmptyMessage title="На этой странице списков нет" description="Здесь нет импортированных списков. Проверьте следующую страницу, если она доступна." />)}
      {r.data && <nav className="af-catalog-pagination" aria-label="Страницы конкурсов">
        <button type="button" className="af-action af-action--outline" disabled={!cursor || r.loading} onClick={() => update('after', '')}>В начало</button>
        <button type="button" className="af-action af-action--outline" disabled={!r.data.nextCursor || r.loading} onClick={() => update('after', r.data!.nextCursor!)}>Далее</button>
      </nav>}
    </ResourceState>
  </>;
}
