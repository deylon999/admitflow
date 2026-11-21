import { Action, EmptyMessage, Metric, PageTitle, ProgramCard, Surface } from '../../shared/UI';
import { programs, reviews } from '../../data/demo';
import { RouteLink } from '../../app/RouteLink';
import { SectionHeader } from './SectionHeader';
import type { AppPageProps } from './types';

export function Dashboard({ tracked }: Pick<AppPageProps, 'tracked'>) {
  const saved = programs.filter(p => tracked.includes(p.id));
  return (
    <>
      <PageTitle kicker="КАМПАНИЯ 2027" title="Твои варианты поступления." description="Все направления, прогнозы и изменения — на одном экране." action={<Action to="/app/forecast">Новый прогноз ↗</Action>} />
      <div className="af-grid-metrics">
        <Metric label="Сохранено программ" value={saved.length} hint="в твоём списке" />
        <Metric label="Высокие шансы" value={saved.filter(p => p.chance >= 70).length} hint="из сохранённых направлений" tone="lime" />
        <Metric label="Обновлений за неделю" value="12" hint="условные события" />
        <Metric label="Приёмная кампания" value="2027" hint="год сценария" />
      </div>
      <div className="af-split-grid">
        <div>
          <SectionHeader action={<RouteLink to="/app/watchlist" className="af-text-link">Все направления ↗</RouteLink>}>Твои направления</SectionHeader>
          <div className="af-stack">
            {saved.length ? saved.slice(0, 3).map(item => <ProgramCard key={item.id} item={item} />) : <EmptyMessage title="Список пуст" description="Добавь первое направление, чтобы видеть его здесь." action={<Action to="/app/watchlist/add">Добавить ↗</Action>} />}
          </div>
        </div>
        <div>
          <SectionHeader>Последние события</SectionHeader>
          <Surface className="af-event-list">
            {reviews.map(event => <div className="af-event-list__item" key={event.at}><span className="af-event-list__dot" /><div><small>{event.at}</small><b>{event.title}</b><p>{event.detail}</p></div></div>)}
            <RouteLink to="/app/history" className="af-text-link">Вся история ↗</RouteLink>
          </Surface>
        </div>
      </div>

    </>
  );
}
