import { useEffect, useState } from 'react';
import { sessionChanged, sessionExpired } from '../../shared/api';
import { useResource } from '../../shared/resource';
import { ResourceState } from '../../shared/ResourceState';
import { EmptyMessage, PageTitle, Surface } from '../../shared/UI';
import { events } from './decode';

export function LiveEvents() {
    const [cursors, setCursors] = useState<string[]>([]);
    const cursor = cursors.at(-1);
    useEffect(() => {
        const clear = () => setCursors([]);
        window.addEventListener(sessionChanged, clear);
        window.addEventListener(sessionExpired, clear);
        return () => {
            window.removeEventListener(sessionChanged, clear);
            window.removeEventListener(sessionExpired, clear);
        };
    }, []);
    const r = useResource(`changes${cursor ? '?before=' + encodeURIComponent(cursor) : ''}`, events);
    return <><PageTitle kicker="API · СОБЫТИЯ" title="Изменения сохранённых списков"/><ResourceState {...r} hasData={!!r.data}>{r.data && <>{r.data.items.length ? r.data.items.map(e => <Surface key={e.id} title={e.title}><time dateTime={e.createdAt}>{e.createdAt}</time></Surface>) : <EmptyMessage title="Изменений пока нет" description="Здесь появятся события по вашим подпискам."/>}<button className="af-action af-action--outline" disabled={!cursors.length || r.loading} onClick={() => setCursors(s => s.slice(0, -1))}>Назад</button><button className="af-action af-action--outline" disabled={!r.data.nextCursor || r.loading} onClick={() => setCursors(s => [...s, r.data!.nextCursor!])}>Далее</button></>}</ResourceState></>;
}
