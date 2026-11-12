import { useEffect, useState } from 'react';
import { request } from '../shared/api';
import { groups, lookup, saved, type Group } from '../shared/dto';
import { useResource } from '../shared/resource';
import { ResourceState } from '../shared/ResourceState';
import { Action, EmptyMessage, PageTitle, Surface } from '../shared/UI';
export function AddSource() {
    const [q, setQ] = useState(''), [cursor, setCursor] = useState(''), [group, setGroup] = useState<Group | null>(null), [code, setCode] = useState(''), [result, setResult] = useState<ReturnType<typeof lookup>>(), [busy, setBusy] = useState(false), [error, setError] = useState(''), [success, setSuccess] = useState('');
    const r = useResource('groups?' + new URLSearchParams({ q, after: cursor, limit: '20' }), groups);
    useEffect(() => {
        const clear = () => {
            setResult(undefined);
            setCode('');
            setSuccess('');
        };
        const storage = (e: StorageEvent) => {
            if (e.key === 'admitflow-session-change')
                clear();
        };
        window.addEventListener('admitflow-session-expired', clear);
        window.addEventListener('storage', storage);
        return () => {
            window.removeEventListener('admitflow-session-expired', clear);
            window.removeEventListener('storage', storage);
        };
    }, []);
    async function submit() {
        setBusy(true);
        setError('');
        setSuccess('');
        try {
            if (result) {
                const id = await request('subscriptions', saved, { method: 'POST', json: { confirmationToken: result.token } });
                setSuccess(id);
                setResult(undefined);
                setCode('');
            }
            else if (group?.sourceId) {
                setResult(await request(`sources/${encodeURIComponent(group.sourceId)}/lookup`, lookup, { method: 'POST', json: { publicCode: code } }));
            }
        }
        catch (e) {
            setError((e as Error).message);
        }
        finally {
            setBusy(false);
        }
    }
    return <><PageTitle kicker="API · ДОБАВЛЕНИЕ" title="Выбери конкурсный список" description="Подписка создаётся после поиска и подтверждения вашей записи. Прогноз поступления не рассчитывается."/><Surface><label className="af-field">Поиск конкурса<input value={q} disabled={busy} onChange={e => {
        setQ(e.target.value);
        setCursor('');
        setGroup(null);
        setResult(undefined);
        setSuccess('');
    }} maxLength={120}/></label></Surface><ResourceState {...r} hasData={!!r.data}>{r.data && <><Surface>{r.data.items.length ? r.data.items.map(g => <div className="af-info-row" key={g.id}><span>{g.universityName} · {g.title} · {g.year}</span><button className="af-action af-action--outline" disabled={busy || !g.lookupAvailable || !g.sourceId} onClick={() => {
        setGroup(g);
        setCode('');
        setResult(undefined);
        setError('');
        setSuccess('');
    }}>{g.lookupAvailable ? 'Выбрать' : 'Поиск не подключён'}</button></div>) : <EmptyMessage title="Конкурсы не найдены" description="Измените поиск. Подписка без проверенного источника не создаётся."/>}<button className="af-action af-action--outline" disabled={!cursor || busy} onClick={() => setCursor('')}>В начало</button><button className="af-action af-action--outline" disabled={!r.data.nextCursor || busy} onClick={() => setCursor(r.data!.nextCursor!)}>Далее</button></Surface>{group && <Surface title={group.title} description={`${group.universityName} · ${group.year}`}><form onSubmit={e => {
        e.preventDefault();
        void submit();
    }}><label className="af-field">Публичный код в списке<input value={code} disabled={busy || !!result} required maxLength={64} pattern="[A-Za-z0-9-]+" onChange={e => {
        setCode(e.target.value);
        setResult(undefined);
    }}/></label>{result && <p>Запись найдена: {result.title}, {result.year}. Номер в официальном списке: {result.rank}. Проверьте конкурс перед сохранением.</p>}{result === null && <p role="status">Запись не найдена. Проверьте код.</p>}{error && <p role="alert">{error}</p>}<button className="af-action af-action--primary" disabled={busy}>{busy ? 'Подождите…' : result ? 'Подтвердить и сохранить' : 'Найти запись'}</button>{result && <button className="af-action af-action--outline" type="button" disabled={busy} onClick={() => setResult(undefined)}>Изменить код</button>}</form></Surface>}{success && <Surface title="Направление сохранено"><p role="status">Сервер подтвердил сохранение подписки.</p><Action to={'/app/competitions/' + encodeURIComponent(success)}>Открыть направление ↗</Action></Surface>}</>}</ResourceState></>;
}
