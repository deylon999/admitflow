import { ApiError } from '../../shared/api';
import { ResourceState } from '../../shared/ResourceState';
import { Action, EmptyMessage, PageTitle, Surface } from '../../shared/UI';
import { useSourceLookup } from './useSourceLookup';

export function AddSource() {
    const { q, setQ, cursor, setCursor, group, setGroup, code, setCode, result, setResult, busy, error, setError, success, setSuccess, r, submit } = useSourceLookup();
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
        setError(undefined);
        setSuccess('');
    }}>{g.lookupAvailable ? 'Выбрать' : 'Поиск не подключён'}</button></div>) : <EmptyMessage title="Конкурсы не найдены" description="Измените поиск. Подписка без проверенного источника не создаётся."/>}<button className="af-action af-action--outline" disabled={!cursor || busy} onClick={() => setCursor('')}>В начало</button><button className="af-action af-action--outline" disabled={!r.data.nextCursor || busy} onClick={() => setCursor(r.data!.nextCursor!)}>Далее</button></Surface>{group && <Surface title={group.title} description={`${group.universityName} · ${group.year}`}><form onSubmit={e => {
        e.preventDefault();
        void submit();
    }}><label className="af-field">Публичный код в списке<input value={code} disabled={busy || !!result} required maxLength={64} pattern="[A-Za-z0-9-]+" onChange={e => {
        setCode(e.target.value);
        setResult(undefined);
    }}/></label>{result && <p>Запись найдена: {result.title}, {result.year}. Номер в официальном списке: {result.rank}. Проверьте конкурс перед сохранением.</p>}{result === null && <p role="status">Запись не найдена. Проверьте код.</p>}{error && (error instanceof ApiError && error.status === 401 ? <ResourceState loading={false} error={error} retry={() => setError(undefined)}>{null}</ResourceState> : <p role="alert">{error.message}</p>)}<button className="af-action af-action--primary" disabled={busy}>{busy ? 'Подождите…' : result ? 'Подтвердить и сохранить' : 'Найти запись'}</button>{result && <button className="af-action af-action--outline" type="button" disabled={busy} onClick={() => setResult(undefined)}>Изменить код</button>}</form></Surface>}{success && <Surface title="Направление сохранено"><p role="status">Сервер подтвердил сохранение подписки.</p><Action to={'/app/watchlist/' + encodeURIComponent(success)}>Открыть направление ↗</Action></Surface>}</>}</ResourceState></>;
}
