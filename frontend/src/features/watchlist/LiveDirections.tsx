import { ResourceState } from '../../shared/ResourceState';
import { Action, EmptyMessage, PageTitle, Surface } from '../../shared/UI';
import { useSubscriptions } from './useSubscriptions';

export function LiveDirections({ id }: {
    id?: string;
}) {
    const { r, busy, message, error, remove } = useSubscriptions();
    const rows = id ? r.data?.filter(x => x.id === id) : r.data;
    return <><PageTitle kicker="API · ГОСТЕВОЙ ДОСТУП" title={id ? 'Сохранённый конкурс' : 'Мои направления'} description="Факты из сохранённых списков. Условные расчёты не гарантируют зачисление." action={<><Action to="/app/watchlist/add">Добавить направление ↗</Action><button className="af-action af-action--outline" disabled={r.loading} onClick={r.retry}>Обновить</button></>}/>{message && <p role="status">{message}</p>}{error && <p role="alert">{error}</p>}<ResourceState {...r} hasData={!!r.data}>{rows && (rows.length ? rows.map(s => <Surface key={s.id} title={s.group.title} description={s.group.universityName}><p>{s.group.year} · {s.group.dataKind === 'archive' ? 'Архив' : s.group.dataKind === 'live' ? 'Импорт списка' : 'Тип данных не подтверждён'} · Мест: {s.group.seats ?? 'Нет данных'}</p><Action to={'/app/watchlist/' + encodeURIComponent(s.id)}>Открыть конкурс ↗</Action><Action to={'/app/competitions/' + encodeURIComponent(s.group.id)} variant="outline">Конкурсный список ↗</Action>{s.group.sourceUrl && <a href={s.group.sourceUrl} target="_blank" rel="noreferrer">Официальный список ↗</a>}<button className="af-action af-action--outline" disabled={busy} onClick={() => void remove(s.id)}>{busy ? 'Удаляем…' : 'Удалить подписку'}</button></Surface>) : <EmptyMessage title={id ? 'Запись не найдена' : 'Направлений пока нет'} description="Демонстрационные записи не подставляются вместо данных." action={<Action to="/programs">Каталог ↗</Action>}/>)}</ResourceState></>;
}
