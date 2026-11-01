import { useEffect, useRef, useState } from 'react';
import { useInfiniteQuery, useIsMutating, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalculationInputs } from '../components/Calculator';
import { UniversityPicker } from '../components/UniversityPicker';
import { ScenarioExplanation } from '../components/ScenarioExplanation';
import { HistoryComparison } from '../components/HistoryComparison';
import { WatchComparison } from '../components/WatchComparison';
import { downloadExport } from '../lib/download';
import { calculatePlace } from '../lib/calculator';
import type { CalculationForm, CalculationValues } from '../lib/calculator';
import { api, SessionExpiredError } from '../lib/api';
import type { Watch } from '../lib/api';

const emptyValues: CalculationForm = { rank: '', seats: '', excluded: '0', noConsent: '0' };
const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
function date(value: string) { return dateFormat.format(new Date(value)); }
function errorText(error: unknown) { return error instanceof Error ? error.message : 'Не удалось выполнить действие.'; }

function DirectionForm({ watch, focusRequest, onDone, onCancel }: { watch?: Watch; focusRequest: number; onDone: () => void; onCancel: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, [focusRequest]);
  const [values, setValues] = useState<CalculationForm>(watch?.latest.values ?? emptyValues);
  const [university, setUniversity] = useState(watch?.university ?? '');
  const [title, setTitle] = useState(watch?.title ?? '');
  const [sourceUrl, setSourceUrl] = useState(watch?.sourceUrl ?? '');
  const [submitted, setSubmitted] = useState(false);
  const intent = useRef<{ fingerprint: string; key: string } | null>(null);
  const result = calculatePlace(values);
  const error = 'error' in result ? result : undefined;
  const queryClient = useQueryClient();
  const save = useMutation({
    mutationFn: async () => {
      const numeric = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Number(value)])) as CalculationValues;
      const body = { university: university.trim(), title: title.trim(), sourceUrl: sourceUrl.trim(), values: numeric };
      const fingerprint = JSON.stringify({ watchId: watch?.id, ...body });
      if (intent.current?.fingerprint !== fingerprint) intent.current = { fingerprint, key: crypto.randomUUID() };
      if (watch) await api.update(watch.id, numeric, intent.current.key);
      else await api.create(body, intent.current.key);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['watches'] });
      await queryClient.invalidateQueries({ queryKey: ['history'] });
      onDone();
    },
    onError: error => {
      if (error instanceof SessionExpiredError) void queryClient.invalidateQueries({ queryKey: ['watches'] });
    },
  });
  return <form className="direction-form surface" aria-labelledby="direction-form-heading" onKeyDown={event => {
    if (event.key === 'Escape' && !event.defaultPrevented && !save.isPending) { event.preventDefault(); onCancel(); }
  }} onSubmit={event => { event.preventDefault(); setSubmitted(true); if (!save.isPending && !error && university.trim() && title.trim()) save.mutate(); }}>
    <div className="tracker-form-heading"><h2 id="direction-form-heading" ref={heading} tabIndex={-1}>{watch ? 'Обновить цифры' : 'Добавить направление'}</h2><button className="text-button" type="button" onClick={onCancel} aria-label="Закрыть форму" disabled={save.isPending}>✕</button></div>
    <fieldset className="direction-fields" disabled={save.isPending}><legend className="visually-hidden">Данные направления</legend>
    {watch ? <p className="small-copy">{watch.university} · {watch.title}</p> : <>
      <UniversityPicker value={university} onChange={setUniversity} onSelect={item => { setUniversity(item.name); setSourceUrl(item.provenanceUrl); }} />
      <div className="field"><label htmlFor="direction-title">Направление и конкурсная группа</label><input id="direction-title" value={title} maxLength={200} required onChange={event => setTitle(event.target.value)} placeholder="Например: информатика, общий конкурс" /></div>
      <div className="field"><label htmlFor="source-url">Ссылка на конкурсный список</label><input id="source-url" type="url" pattern="https?://.+" value={sourceUrl} maxLength={2048} required onChange={event => setSourceUrl(event.target.value)} placeholder="https://…" /></div>
    </>}
    <div className="tracker-number-fields"><CalculationInputs values={values} onChange={setValues} error={submitted ? error : undefined} prefix="tracker-" /></div>
    </fieldset>
    <p className="form-note">Берите данные одной конкурсной группы. Каждый человек выше вас учитывается только в одной из двух вычитаемых групп.</p>
    {!('error' in result) && <div className="tracker-preview"><span>Место по введённым данным</span><strong>{result.place} <small>из {result.seats}</small></strong></div>}
    {submitted && error && <p className="form-error" id="tracker-calculation-error" role="alert">{error.error}</p>}
    {save.isError && <p className="form-error" role="alert">{errorText(save.error)}</p>}
    <button className="button button-primary" type="submit" disabled={save.isPending}>{save.isPending ? 'Сохраняем…' : watch ? 'Сохранить обновление' : 'Сохранить направление'}</button>
    <p className="form-note">Числа сохраняются вручную. Сервис не запрашивает список по указанной ссылке.</p>
  </form>;
}

function DirectionCard({ watch, onEdit, disabled }: { watch: Watch; onEdit: (button: HTMLButtonElement) => void; disabled: boolean }) {
  const [showHistory, setShowHistory] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const queryClient = useQueryClient();
  const history = useInfiniteQuery({ queryKey: ['history', watch.id], initialPageParam: null as string | null, queryFn: ({ pageParam, signal }) => api.history(watch.id, pageParam, signal), getNextPageParam: page => page.nextCursor, enabled: showHistory });
  const snapshots = history.data?.pages.flatMap(page => page.items) ?? [];
  const remove = useMutation({ mutationFn: () => api.remove(watch.id), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['watches'] }) });
  const { calculation } = watch.latest;
  const old = Date.now() - new Date(watch.latest.capturedAt).getTime() > 86400_000;
  return <article className="direction-card surface">
    <div className="direction-top"><span className="eyebrow">{watch.university}</span><span className="tag">Ручной ввод</span></div>
    <h2>{watch.title}</h2>
    <div className="direction-result"><strong>{calculation.place}</strong><span>место сейчас<br /><b>{calculation.seats}</b> бюджетных мест</span></div>
    <p className="result-status" data-state={calculation.state}>{calculation.status}</p>
    <p className="direction-worst">Если все выше вас подадут согласие: <b>{calculation.worstPlace}-е место</b>.</p>
    <ScenarioExplanation values={watch.latest.values} />
    <div className="direction-source"><a href={watch.sourceUrl} target="_blank" rel="noopener noreferrer">Открыть источник ↗</a><span>Сохранено <time dateTime={watch.latest.capturedAt}>{date(watch.latest.capturedAt)}</time></span></div>
    {old && <p className="stale-note">Цифры сохранены больше суток назад. Проверьте свежий список.</p>}
    <div className="direction-actions"><button className="button button-secondary" type="button" disabled={disabled} onClick={event => onEdit(event.currentTarget)}>Обновить цифры</button><button className="text-button" type="button" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>История</button><button className="text-button delete-link" type="button" onClick={() => setConfirmDelete(!confirmDelete)}>Удалить</button></div>
    {confirmDelete && <div className="delete-confirm"><p>Удалить направление и всю его историю?</p><div><button className="button button-secondary" type="button" disabled={remove.isPending} onClick={() => setConfirmDelete(false)}>Отмена</button><button className="button danger-button" type="button" disabled={remove.isPending} onClick={() => remove.mutate()}>{remove.isPending ? 'Удаляем…' : 'Да, удалить'}</button></div></div>}
    {remove.isError && <p className="form-error" role="alert">{errorText(remove.error)}</p>}
    {showHistory && <div className="direction-history"><h3>История расчётов</h3>{history.isPending ? <p role="status">Загружаем историю…</p> : <>
      {history.isError && <p className="form-error" role="alert">{errorText(history.error)} <button className="text-button" type="button" onClick={() => void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())}>Повторить загрузку истории</button></p>}
      {snapshots.length > 0 && <><HistoryComparison snapshots={snapshots} /><p className="small-copy">Загружено {snapshots.length} сохранений. Дата — время ручного ввода.</p><div className="history-scroll"><table><caption className="visually-hidden">Сохранённые значения и рассчитанное место</caption><thead><tr><th>Дата</th><th>Номер</th><th>Место</th><th>Бюджет</th></tr></thead><tbody>{snapshots.map(snapshot => <tr key={snapshot.id}><td><time dateTime={snapshot.capturedAt}>{date(snapshot.capturedAt)}</time></td><td>{snapshot.values.rank}</td><td>{snapshot.calculation.place}</td><td>{snapshot.values.seats}</td></tr>)}</tbody></table></div></>}
      {history.hasNextPage && <button className="text-button" type="button" disabled={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()}>{history.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё'}</button>}
    </>}</div>}
  </article>;
}

export default function TrackerPage() {
  const [form, setForm] = useState<'new' | Watch | null>(null);
  const [focusRequest, setFocusRequest] = useState(0);
  const formOpener = useRef<HTMLButtonElement | null>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  function openForm(value: 'new' | Watch, button: HTMLButtonElement) {
    formOpener.current = button;
    setNotice('');
    setForm(value);
    setFocusRequest(request => request + 1);
  }
  function closeForm() {
    setForm(null);
    requestAnimationFrame(() => {
      const target = formOpener.current?.isConnected ? formOpener.current : addButton.current;
      target?.focus();
    });
  }
  const [notice, setNotice] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const busy = useIsMutating() > 0;
  const queryClient = useQueryClient();
  const watches = useQuery({ queryKey: ['watches'], queryFn: ({ signal }) => api.list(signal) });
  const download = useMutation({ mutationFn: api.exportData, onSuccess: downloadExport });
  const reset = useMutation({
    mutationFn: async () => {
      await queryClient.cancelQueries({ queryKey: ['watches'] });
      await queryClient.cancelQueries({ queryKey: ['history'] });
      await api.resetSession();
    },
    onSuccess: async () => {
      queryClient.removeQueries({ queryKey: ['history'] });
      setForm(null);
      setConfirmReset(false);
      setNotice('Создана новая гостевая сессия.');
      await queryClient.invalidateQueries({ queryKey: ['watches'] });
    },
  });
  const count = watches.data?.length ?? 0;
  const expired = watches.error instanceof SessionExpiredError;
  return <main className="container tracker-page" id="top">
    <div className="tracker-page-heading"><div><p className="eyebrow">Ваша приёмная кампания</p><h1>Мои направления</h1><p className="section-description">Сравнивайте место и сохраняйте изменения в одном окне.</p></div><button ref={addButton} className="button button-primary" type="button" disabled={count >= 20 || busy} onClick={event => openForm('new', event.currentTarget)}>Добавить направление</button></div>
    <div className="tracker-info"><span className="tag">Ручной режим</span><p>Направления доступны в этом браузере 30 дней с начала сессии. Очистка cookies удалит доступ. Автоматическое обновление вузов ещё не подключено.</p></div>
    <div className="tracker-data-actions"><button className="text-button" type="button" disabled={busy || !count} onClick={() => download.mutate()}>{download.isPending ? 'Готовим файл…' : 'Скачать данные (JSON)'}</button>
    {count > 0 && <button className="text-button delete-link" type="button" disabled={busy} onClick={() => setConfirmReset(true)}>Удалить все мои данные</button>}</div>
    {download.isError && <p className="form-error" role="alert">{errorText(download.error)}</p>}
    {confirmReset && <div className="delete-confirm surface"><p>Удалить все направления и историю в этом браузере? Отменить удаление нельзя.</p><div><button className="button button-secondary" type="button" disabled={reset.isPending} onClick={() => setConfirmReset(false)}>Отмена</button><button className="button danger-button" type="button" disabled={reset.isPending} onClick={() => reset.mutate()}>Удалить всё</button></div></div>}
    {expired && <div className="surface empty-state"><h2>Срок гостевой сессии истёк</h2><p>Доступ к прежним направлениям завершён или cookies были удалены. Для дальнейшей работы начните новую сессию.</p><button className="button button-primary" type="button" disabled={reset.isPending} onClick={() => reset.mutate()}>{reset.isPending ? 'Создаём…' : 'Начать новую сессию'}</button></div>}
    {reset.isError && <p className="form-error" role="alert">{errorText(reset.error)}</p>}
    <p className="tracker-notice" role="status">{notice}</p>
    {!watches.isError && watches.data && <WatchComparison watches={watches.data} />}
    <div className={`tracker-layout ${form ? 'with-form' : ''}`}><div className="directions-list">
      {expired ? null : watches.isPending ? <div className="empty-state surface" role="status"><h2>Загружаем направления…</h2><p>Проверяем сохранённые данные.</p></div> : watches.isError ? <div className="empty-state surface" role="alert"><h2>Не удалось загрузить направления</h2><p>{errorText(watches.error)}</p><button className="button button-secondary" type="button" onClick={() => void watches.refetch()}>Повторить</button></div> : count === 0 ? <div className="empty-state surface"><span className="empty-mark" aria-hidden="true">＋</span><h2>Направлений пока нет</h2><p>Добавьте вуз, направление и ссылку на список. Введите текущие цифры — сервис сохранит расчёт и его историю.</p><button className="button button-primary" type="button" onClick={event => openForm('new', event.currentTarget)}>Добавить первое направление</button></div> : watches.data?.map(watch => <DirectionCard key={watch.id} watch={watch} disabled={busy} onEdit={button => openForm(watch, button)} />)}
    </div>{form && <aside className="tracker-sidebar"><DirectionForm key={form === 'new' ? 'new' : form.id} focusRequest={focusRequest} watch={form === 'new' ? undefined : form} onCancel={closeForm} onDone={() => { closeForm(); setNotice('Данные сохранены. Расчёт и история обновлены.'); }} /></aside>}</div>
    <p className="tracker-disclaimer">Расчёт описывает положение по введённым данным в одной конкурсной группе. Он не учитывает все правила и приоритеты конкретного вуза и не гарантирует зачисление.</p>
  </main>;
}
