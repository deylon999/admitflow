import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';

export function ArchiveDirections() {
  const access = useQuery<SessionAccess>({ queryKey: sessionAccessKey, queryFn: async (): Promise<SessionAccess> => 'active', enabled: false, initialData: 'active' });
  const records = useQuery({ queryKey: ['archive-directions'], queryFn: ({ signal }) => api.subscriptions(signal), enabled: access.data === 'active' });
  if (access.data !== 'active') return null;
  if (records.isPending) return <p role="status">Загружаем архивные направления…</p>;
  if (!records.data?.length && !records.isError) return null;
  return <section className="archive-directions" aria-labelledby="archive-directions-title"><h2 id="archive-directions-title">Сохранённые записи источников</h2>
    <p className="small-copy">Здесь факты архивных списков. Ручной JSON и печатный отчёт ниже относятся только к ручным направлениям.</p>
    {records.isError && <p role="alert">Не удалось перечитать архивные направления. {records.data ? 'Показаны ранее загруженные датированные записи.' : ''}</p>}
    <button type="button" className="text-button" disabled={records.isFetching} onClick={() => void records.refetch()}>Перечитать сохранённые факты</button>
    <div className="source-catalog-list">{records.data?.map(item => <article className="surface source-catalog-card archive-direction-card" key={item.id}>
      <span className="tag">Архив · {item.group.year}</span><h3>{item.group.title}</h3><p>{item.group.universityName}</p>
      {item.candidate ? <><p>Строка официального списка: <strong>{item.candidate.officialRank}</strong> · баллы: {item.candidate.score ?? 'неизвестно'}</p><p>Согласие в источнике: {item.candidate.consent === null ? 'неизвестно' : item.candidate.consent ? 'да' : 'нет'} · приоритет: {item.candidate.priority ?? 'неизвестно'}</p></> : <p>{item.notice}</p>}
      <p>Снимок получен: {item.group.fetchedAt ? new Date(item.group.fetchedAt).toLocaleString('ru-RU') : 'неизвестно'}. Обновление самим источником: {item.group.sourceUpdatedAt ? new Date(item.group.sourceUpdatedAt).toLocaleString('ru-RU') : 'неизвестно'}.</p>
      <p className="small-copy">Архив не является текущей кампанией. Вероятность и официальный результат зачисления не рассчитываются.</p>
      {item.group.sourceUrl && <a href={item.group.sourceUrl} target="_blank" rel="noopener noreferrer">Официальный список ↗</a>}
    </article>)}</div>
  </section>;
}
