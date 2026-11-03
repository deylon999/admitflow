import { useRef, useState } from 'react';
import { DeleteConfirmation } from './DeleteConfirmation';
import { ArchiveHistory } from './ArchiveHistory';
import { SourceProvenance } from './SourceProvenance';
import { downloadJson } from '../lib/download';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';

export function ArchiveDirections() {
  const [deleting, setDeleting] = useState<string | null>(null);
  const client = useQueryClient();
  const refresh = useRef<HTMLButtonElement>(null);
  const focusAfterDelete = () => requestAnimationFrame(() => (refresh.current ?? document.querySelector<HTMLElement>('main h1'))?.focus());
  const download = useMutation({ mutationFn: api.exportArchive, onSuccess: value => downloadJson(value, `admitflow-archive-${value.exportedAt.slice(0,10)}.json`) });
  const remove = useMutation({ mutationFn: (id: string) => api.removeSubscription(id), onSuccess: async () => {
    setDeleting(null); client.removeQueries({ queryKey: ['archive-history'] }); await client.invalidateQueries({ queryKey: ['archive-directions'] }); await client.invalidateQueries({ queryKey: ['direction-budget'] }); focusAfterDelete();
  }, onError: async (_error, id) => {
    // DELETE may have committed before its response was lost. Reconcile by read;
    // do not automatically repeat a mutation with an unknown outcome.
    const current = await client.fetchQuery({ queryKey: ['archive-directions'], queryFn: ({ signal }) => api.subscriptions(signal), staleTime: 0 }).catch(() => null);
    if (current && !current.some(item => item.id === id)) {
      setDeleting(null); client.removeQueries({ queryKey: ['archive-history', id] });
      await client.invalidateQueries({ queryKey: ['direction-budget'] });
      focusAfterDelete();
    }
  } });
  const access = useQuery<SessionAccess>({ queryKey: sessionAccessKey, queryFn: async (): Promise<SessionAccess> => 'active', enabled: false, initialData: 'active' });
  const records = useQuery({ queryKey: ['archive-directions'], queryFn: ({ signal }) => api.subscriptions(signal), enabled: access.data === 'active' });
  if (access.data !== 'active') return null;
  if (records.isPending) return <p role="status">Загружаем архивные направления…</p>;
  if (!records.data?.length && !records.isError) return null;
  return <section className="archive-directions" aria-labelledby="archive-directions-title"><h2 id="archive-directions-title">Сохранённые записи источников</h2>
    <p className="small-copy">Здесь факты архивных списков. Ручной JSON и печатный отчёт ниже относятся только к ручным направлениям.</p>
    {records.isError && <p role="alert">Не удалось перечитать архивные направления. {records.data ? 'Показаны ранее загруженные датированные записи.' : ''}</p>}
    <button ref={refresh} type="button" className="text-button" disabled={records.isFetching} onClick={() => void records.refetch()}>Перечитать сохранённые факты</button>
    <button type="button" className="text-button" disabled={download.isPending || !records.data?.length} onClick={() => download.mutate()}>Скачать текущие архивные факты (JSON)</button>
    <p className="small-copy">Архивный файл содержит текущие датированные факты ваших записей. История доступна в карточках. Файл не восстанавливает гостевой доступ и не импортируется как ручной расчёт.</p>
    {download.isError && <p role="alert">{download.error.message}</p>}
    <div className="source-catalog-list">{records.data?.map(item => <article className="surface source-catalog-card archive-direction-card" key={item.id}>
      <span className="tag">Архив · {item.group.year}</span><h3>{item.group.title}</h3><p>{item.group.universityName}</p>
      {item.candidate ? <><p>Строка официального списка: <strong>{item.candidate.officialRank}</strong> · баллы: {item.candidate.score ?? 'неизвестно'}</p><p>Согласие в источнике: {item.candidate.consent === null ? 'неизвестно' : item.candidate.consent ? 'да' : 'нет'} · приоритет: {item.candidate.priority ?? 'неизвестно'}</p></> : <p>{item.notice}</p>}
      <SourceProvenance group={item.group} />
      <p className="small-copy">Архив не является текущей кампанией. Вероятность и официальный результат зачисления не рассчитываются.</p>
      <ArchiveHistory id={item.id} />
      <button id={`delete-archive-${item.id}`} type="button" className="text-button delete-link" disabled={remove.isPending} onClick={() => { remove.reset(); setDeleting(item.id); }}>Удалить архивную запись</button>
      {deleting === item.id && <DeleteConfirmation text="Удалить эту архивную запись и её личную историю? Общий снимок источника останется." label="Да, удалить архивную запись" disabled={remove.isPending} onCancel={() => { setDeleting(null); requestAnimationFrame(() => document.getElementById(`delete-archive-${item.id}`)?.focus()); }} onConfirm={() => remove.mutate(item.id)} />}
      {deleting === item.id && remove.isError && <p role="alert">{remove.error.message}</p>}
    </article>)}</div>
  </section>;
}
