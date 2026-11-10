import { useState } from 'react';
import { request } from '../shared/api';
import { subscriptions, events, coverage } from '../shared/dto';
import { useResource } from '../shared/resource';
import { ResourceState } from '../shared/ResourceState';
import { Action, EmptyMessage, PageTitle, Surface } from '../shared/UI';
import { RouteLink } from '../app/RouteLink';
export function LiveSources() {
    const r = useResource('coverage', coverage);
    return <><PageTitle kicker="API · ИСТОЧНИКИ" title="Источники и доступность данных" description="Каталог и свежий импорт — разные показатели. Архив не является текущей кампанией."/><ResourceState {...r} hasData={!!r.data}>{r.data && <Surface title="Подтверждённые сведения"><p>Вузов в каталоге: {r.data.catalogUniversities}</p><p>Зарегистрировано источников: {r.data.registeredSources}</p><p>Свежих групп: {r.data.freshGroups}</p><p>Архивных групп: {r.data.archiveGroups}</p><time dateTime={r.data.generatedAt}>{r.data.generatedAt}</time><p><RouteLink to="/app/coverage">Покрытие вузов России ↗</RouteLink></p></Surface>}</ResourceState></>;
}
export function LiveEvents() {
    const [cursors, setCursors] = useState<string[]>([]);
    const cursor = cursors.at(-1);
    const r = useResource(`changes${cursor ? '?before=' + encodeURIComponent(cursor) : ''}`, events);
    return <><PageTitle kicker="API · СОБЫТИЯ" title="Изменения сохранённых списков"/><ResourceState {...r} hasData={!!r.data}>{r.data && <>{r.data.items.length ? r.data.items.map(e => <Surface key={e.id} title={e.title}><time dateTime={e.createdAt}>{e.createdAt}</time></Surface>) : <EmptyMessage title="Изменений пока нет" description="Здесь появятся события по вашим подпискам."/>}<button className="af-action af-action--outline" disabled={!cursors.length || r.loading} onClick={() => setCursors(s => s.slice(0, -1))}>Назад</button><button className="af-action af-action--outline" disabled={!r.data.nextCursor || r.loading} onClick={() => setCursors(s => [...s, r.data!.nextCursor!])}>Далее</button></>}</ResourceState></>;
}
export function LiveDirections({ id }: {
    id?: string;
}) {
    const r = useResource('subscriptions', subscriptions);
    const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('');
    async function remove(key: string) {
        if (!confirm('Удалить подписку и её историю?'))
            return;
        setBusy(true);
        setError('');
        setMessage('');
        try {
            await request(`subscriptions/${encodeURIComponent(key)}`, () => null, { method: 'DELETE' });
            setMessage('Подписка удалена.');
            r.retry();
        }
        catch (e) {
            setError((e as Error).message);
        }
        finally {
            setBusy(false);
        }
    }
    const rows = id ? r.data?.filter(x => x.id === id) : r.data;
    return <><PageTitle kicker="API · ГОСТЕВОЙ ДОСТУП" title={id ? 'Сохранённый конкурс' : 'Мои направления'} description="Факты из сохранённых списков. Условные расчёты не гарантируют зачисление." action={<><Action to="/app/watchlist/add">Добавить направление ↗</Action><button className="af-action af-action--outline" disabled={r.loading} onClick={r.retry}>Обновить</button></>}/>{message && <p role="status">{message}</p>}{error && <p role="alert">{error}</p>}<ResourceState {...r} hasData={!!r.data}>{rows && (rows.length ? rows.map(s => <Surface key={s.id} title={s.group.title} description={s.group.universityName}><p>{s.group.year} · {s.group.dataKind === 'archive' ? 'Архив' : s.group.dataKind === 'live' ? 'Импорт списка' : 'Тип данных не подтверждён'} · Мест: {s.group.seats ?? 'Нет данных'}</p><Action to={'/app/competitions/' + encodeURIComponent(s.id)}>Открыть конкурс ↗</Action>{s.group.sourceUrl && <a href={s.group.sourceUrl} target="_blank" rel="noreferrer">Официальный список ↗</a>}<button className="af-action af-action--outline" disabled={busy} onClick={() => void remove(s.id)}>{busy ? 'Удаляем…' : 'Удалить подписку'}</button></Surface>) : <EmptyMessage title={id ? 'Запись не найдена' : 'Направлений пока нет'} description="Демонстрационные записи не подставляются вместо данных." action={<Action to="/programs">Каталог ↗</Action>}/>)}</ResourceState></>;
}
export { AddSource as LiveAdd } from './AddSource';
export function Unsupported({ children }: {
    children: React.ReactNode;
}) {
    const demo = new URLSearchParams(location.search).get('mode') === 'demo';
    return <><Surface tone="soft" title={demo ? 'Демонстрация интерфейса' : 'Функция пока не подключена'} description={demo ? 'Все цифры и действия ниже — примеры. Они не являются ответом API; данные не сохраняются на сервере.' : 'Для этой функции пока нет продуктового API. Реальные прогнозы и успешные операции не имитируются.'}><Action to={location.pathname + (demo ? '?mode=live' : '?mode=demo')}>{demo ? 'Выйти из демо' : 'Посмотреть демо интерфейса'}</Action><Action to="/programs" variant="outline">Реальный каталог ↗</Action></Surface>{demo && children}</>;
}
