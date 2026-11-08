import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router';
import { api } from '../lib/api';
import type { LookupResult, SourceGroup } from '../lib/source-contracts';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';
import { SourceProvenance } from './SourceProvenance';

export function SourceLookup({ group, onClose }: { group: SourceGroup; onClose: () => void }) {
  const [code, setCode] = useState(''), [preview, setPreview] = useState<LookupResult | null>(null), [acknowledged, setAcknowledged] = useState(false), [attempted, setAttempted] = useState(false), [expired, setExpired] = useState(false), [saved, setSaved] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null), queryClient = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const savedLink = useRef<HTMLAnchorElement>(null);
  useEffect(() => { input.current?.focus(); }, []);
  useLayoutEffect(() => { if (preview) heading.current?.focus(); }, [preview]);
  const access = useQuery<SessionAccess>({ queryKey: sessionAccessKey, queryFn: async (): Promise<SessionAccess> => 'active', enabled: false, initialData: 'active' });
  const lookup = useMutation({ mutationFn: async () => {
    const value = await api.lookup(group.sourceId!, code.trim());
    if (value.group.id !== group.id || value.group.year !== group.year || value.group.universityId !== group.universityId) throw new Error('Ответ относится к другой группе. Повторите поиск в каталоге.');
    return value;
  }, onSuccess: value => { setPreview(value); setAcknowledged(false); setAttempted(false); setExpired(false); } });
  const save = useMutation({ mutationFn: () => api.subscribe(preview!.confirmationToken!), onSuccess: async () => {
    setCode(''); setPreview(null); setSaved(true);
    await queryClient.invalidateQueries({ queryKey: ['archive-directions'] });
    await queryClient.invalidateQueries({ queryKey: ['direction-budget'] });
    requestAnimationFrame(() => savedLink.current?.focus());
  } });
  useEffect(() => { if (access.data !== 'active') { setCode(''); setPreview(null); setAcknowledged(false); } }, [access.data]);
  useEffect(() => {
    if (!preview?.expiresAt) return;
    const timer = setTimeout(() => setExpired(true), Math.max(0, Date.parse(preview.expiresAt) - Date.now()));
    return () => clearTimeout(timer);
  }, [preview]);
  const busy = lookup.isPending || save.isPending;
  if (access.data !== 'active') return <div role="alert"><p>Доступ изменился или закончился. Старое подтверждение скрыто.</p><Link data-router-link to="/tracker">Управление гостевым доступом</Link></div>;
  return <div className="source-lookup">
    <h3>Найти запись в этой группе</h3><p className="small-copy">Введите публичный код из выбранного списка. ФИО, паспорт и СНИЛС не нужны. Код не сохраняется в браузере или в карточке направления.</p>
    <form onSubmit={event => { event.preventDefault(); if (!busy && /^[A-Za-z0-9-]{1,64}$/.test(code.trim())) { setSaved(false); setPreview(null); lookup.mutate(); } }}>
      <label>Код поступающего<input ref={input} autoComplete="off" spellCheck={false} maxLength={64} disabled={busy} value={code} onChange={event => { setCode(event.target.value); setPreview(null); setAcknowledged(false); save.reset(); }} /></label>
      <div className="direction-actions"><button className="button button-primary" type="submit" disabled={busy || !/^[A-Za-z0-9-]{1,64}$/.test(code.trim())}>{lookup.isPending ? 'Ищем…' : 'Найти запись'}</button><button className="text-button" type="button" disabled={busy} onClick={onClose}>Закрыть поиск</button></div>
    </form>
    {lookup.isError && <p role="alert">{lookup.error.message}</p>}
    {preview && <div className="source-candidate-preview surface">
      <h3 ref={heading} tabIndex={-1}>{preview.found ? 'Проверьте выбранную запись' : 'Запись не найдена в выбранном снимке'}</h3>
      <p>{preview.group.universityName} · {preview.group.title} · сезон {preview.group.year}</p>
      <p>Архив. Это не текущая кампания и не гарантия зачисления.</p>
      {preview.candidate && <>
        <p>Строка официального списка: <strong>{preview.candidate.officialRank}</strong>. Баллы: {preview.candidate.score ?? 'неизвестно'}.</p>
        <p>Согласие в источнике: {preview.candidate.consent === null ? 'неизвестно' : preview.candidate.consent ? 'да' : 'нет'}. Приоритет: {preview.candidate.priority ?? 'неизвестно'}.</p>
        <p>Статус в снимке: {preview.candidate.participation === 'enrolled' ? 'источник отмечает зачисление' : preview.candidate.participation === 'unknown' ? 'не подтверждён' : preview.candidate.participation}.</p>
        <SourceProvenance group={preview.group} />
        <label className="source-ack"><input type="checkbox" checked={acknowledged} disabled={busy} onChange={event => setAcknowledged(event.target.checked)} />Подтверждаю: выбраны нужные мне группа и запись</label>
        <p className="small-copy">Подтверждение сохраняет направление для просмотра. Оно не подаёт согласие на зачисление и не меняет данные вуза.</p>
        {expired && <p role="status">Срок подтверждения истёк. {attempted ? 'Если ответ сохранения потерян, можно безопасно повторить ту же попытку.' : 'Найдите запись снова перед сохранением.'}</p>}
        <button type="button" className="button button-primary" disabled={!acknowledged || busy || (expired && !attempted)} onClick={() => {
          if (!attempted && (!preview.expiresAt || Date.now() >= Date.parse(preview.expiresAt))) { setExpired(true); return; }
          setAttempted(true); save.mutate();
        }}>{save.isPending ? 'Сохраняем…' : save.isError ? 'Повторить сохранение записи' : 'Сохранить эту запись'}</button>
      </>}
      {!preview.found && <p>Сверьте код, сезон и группу на официальном сайте. Отсутствие записи не означает отказ или отзыв заявления.</p>}
    </div>}
    {save.isError && <p role="alert">{save.error.message}</p>}
    {saved && <p role="status">Архивное направление сохранено. <Link ref={savedLink} data-router-link to="/tracker">Открыть мои направления →</Link></p>}
  </div>;
}
