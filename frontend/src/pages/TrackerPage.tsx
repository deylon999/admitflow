import { useCallback, useEffect, useRef, useState } from 'react';
import { useInfiniteQuery, useIsMutating, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalculationInputs } from '../components/Calculator';
import { UniversityPicker } from '../components/UniversityPicker';
import { ScenarioExplanation } from '../components/ScenarioExplanation';
import { HistoryComparison } from '../components/HistoryComparison';
import { WatchComparison } from '../components/WatchComparison';
import { ImportData } from '../components/ImportData';
import { CoverageSummary } from '../components/CoverageSummary';
import { downloadExport } from '../lib/download';
import { calculatePlace } from '../lib/calculator';
import type { CalculationForm, CalculationValues } from '../lib/calculator';
import { api, SessionExpiredError } from '../lib/api';
import type { Watch } from '../lib/api';
import { assertSnapshotOrder } from '../lib/contracts';
import { draftSignature, validateDirection } from '../lib/direction';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';
import { selectWatches } from '../lib/watch-list';
import type { WatchOrder } from '../lib/watch-list';
import { ManualReport } from '../components/ManualReport';

const emptyValues: CalculationForm = { rank: '', seats: '', excluded: '0', noConsent: '0' };
const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
function date(value: string) { return dateFormat.format(new Date(value)); }
function exactDate(value: string) { return `${new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value))} (${value})`; }
function errorText(error: unknown) { return error instanceof Error ? error.message : 'Не удалось выполнить действие.'; }

function DirectionForm({ watch, focusRequest, onDone, onCancel, onDirtyChange }: { watch?: Watch; focusRequest: number; onDone: () => void; onCancel: () => void; onDirtyChange: (dirty: boolean) => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, [focusRequest]);
  const [values, setValues] = useState<CalculationForm>(watch?.latest.values ?? emptyValues);
  const [university, setUniversity] = useState(watch?.university ?? '');
  const [title, setTitle] = useState(watch?.title ?? '');
  const [sourceUrl, setSourceUrl] = useState(watch?.sourceUrl ?? '');
  const [submitted, setSubmitted] = useState(false);
  const currentDraft = draftSignature({ university, title, sourceUrl, values });
  const initialDraft = useRef(currentDraft);
  const dirty = currentDraft !== initialDraft.current;
  useEffect(() => { onDirtyChange(dirty); return () => onDirtyChange(false); }, [dirty, onDirtyChange]);
  useEffect(() => {
    if (!dirty) return;
    let acceptedLink = false;
    const beforeUnload = (event: BeforeUnloadEvent) => { if (!acceptedLink) { event.preventDefault(); event.returnValue = ''; } };
    const guardLink = (event: MouseEvent) => {
      const link = event.target instanceof Element ? event.target.closest<HTMLAnchorElement>('a[href]') : null;
      if (!link || link.target === '_blank' || link.hasAttribute('download') || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const target = new URL(link.href, location.href);
      if (target.origin === location.origin && target.pathname === location.pathname && target.search === location.search) return;
      if (!window.confirm('Удалить несохранённые изменения формы и перейти?')) { event.preventDefault(); event.stopPropagation(); }
      else acceptedLink = true;
    };
    window.addEventListener('beforeunload', beforeUnload);
    document.addEventListener('click', guardLink, true);
    return () => { window.removeEventListener('beforeunload', beforeUnload); document.removeEventListener('click', guardLink, true); };
  }, [dirty, currentDraft]);
  const intent = useRef<{ fingerprint: string; key: string } | null>(null);
  const result = calculatePlace(values);
  const validation = validateDirection({ university, title, sourceUrl, values }, Boolean(watch));
  const error = validation.calculation;
  const metadata = submitted ? validation.metadata : {};
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
  });
  return <form className="direction-form surface" noValidate aria-labelledby="direction-form-heading" onKeyDown={event => {
    if (event.key === 'Escape' && !event.defaultPrevented && !save.isPending) { event.preventDefault(); onCancel(); }
  }} onSubmit={event => {
    event.preventDefault();
    setSubmitted(true);
    if (save.isPending) return;
    if (validation.firstInvalidId) document.getElementById(validation.firstInvalidId)?.focus();
    else save.mutate();
  }}>
    <div className="tracker-form-heading"><h2 id="direction-form-heading" ref={heading} tabIndex={-1}>{watch ? 'Обновить цифры' : 'Добавить направление'}</h2><button className="text-button" type="button" onClick={onCancel} aria-label="Закрыть форму" disabled={save.isPending}>✕</button></div>
    <fieldset className="direction-fields" disabled={save.isPending}><legend className="visually-hidden">Данные направления</legend>
    {watch ? <p className="small-copy">{watch.university} · {watch.title}</p> : <>
      <UniversityPicker value={university} onChange={setUniversity} error={metadata.university} onSelect={item => { setUniversity(item.name); setSourceUrl(item.provenanceUrl); }} />
      <div className="field"><label htmlFor="direction-title">Направление и конкурсная группа</label><input id="direction-title" value={title} maxLength={200} required aria-invalid={Boolean(metadata.title) || undefined} aria-describedby={metadata.title ? 'direction-title-error' : undefined} onChange={event => setTitle(event.target.value)} placeholder="Например: информатика, общий конкурс" />{metadata.title && <p id="direction-title-error" className="form-error" role="alert">{metadata.title}</p>}</div>
      <div className="field"><label htmlFor="source-url">Ссылка на конкурсный список</label><input id="source-url" type="url" value={sourceUrl} maxLength={2048} required aria-invalid={Boolean(metadata.sourceUrl) || undefined} aria-describedby={metadata.sourceUrl ? 'source-url-error' : undefined} onChange={event => setSourceUrl(event.target.value)} placeholder="https://…" />{metadata.sourceUrl && <p id="source-url-error" className="form-error" role="alert">{metadata.sourceUrl}</p>}</div>
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

function DirectionCard({ watch, onEdit, disabled, beforeDelete, onRemoved }: { watch: Watch; onEdit: (button: HTMLButtonElement) => void; disabled: boolean; beforeDelete: () => boolean; onRemoved: () => void }) {
  const [showHistory, setShowHistory] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const queryClient = useQueryClient();
  const history = useInfiniteQuery({ queryKey: ['history', watch.id], initialPageParam: null as string | null, queryFn: ({ pageParam, signal }) => api.history(watch.id, pageParam, signal), getNextPageParam: page => page.nextCursor, enabled: showHistory,
    select: data => { const snapshots = data.pages.flatMap(page => page.items); assertSnapshotOrder(snapshots); return { ...data, snapshots }; } });
  const snapshots = history.data?.snapshots ?? [];
  const totalSnapshots = history.data?.pages[0]?.total;
  const remove = useMutation({ mutationFn: () => api.remove(watch.id), onSuccess: async () => { onRemoved(); await queryClient.invalidateQueries({ queryKey: ['watches'] }); } });
  const { calculation } = watch.latest;
  const old = Date.now() - new Date(watch.latest.capturedAt).getTime() > 86400_000;
  return <article className="direction-card surface">
    <div className="direction-top"><span className="eyebrow">{watch.university}</span><span className="tag">Ручной ввод</span></div>
    <h2>{watch.title}</h2>
    <div className="direction-result"><strong>{calculation.place}</strong><span>по вашему вводу<br /><b>{calculation.seats}</b> бюджетных мест</span></div>
    <p className="result-status" data-state={calculation.state}>{calculation.status}</p>
    <p className="direction-worst">Если все выше вас подадут согласие: <b>{calculation.worstPlace}-е место</b>.</p>
    <ScenarioExplanation values={watch.latest.values} />
    <div className="direction-source"><a href={watch.sourceUrl} target="_blank" rel="noopener noreferrer">Открыть источник ↗</a><span>Сохранено <time dateTime={watch.latest.capturedAt}>{date(watch.latest.capturedAt)}</time></span></div>
    {old && <p className="stale-note">Цифры сохранены больше суток назад. Проверьте свежий список.</p>}
    <div className="direction-actions"><button className="button button-secondary" type="button" disabled={disabled} onClick={event => onEdit(event.currentTarget)}>Обновить цифры</button><button className="text-button" type="button" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>История</button><button className="text-button delete-link" type="button" onClick={() => setConfirmDelete(!confirmDelete)}>Удалить</button></div>
    {confirmDelete && <div className="delete-confirm"><p>Удалить направление и всю его историю?</p><div><button className="button button-secondary" type="button" disabled={remove.isPending} onClick={() => setConfirmDelete(false)}>Отмена</button><button className="button danger-button" type="button" disabled={remove.isPending} onClick={() => { if (beforeDelete()) remove.mutate(); }}>{remove.isPending ? 'Удаляем…' : 'Да, удалить'}</button></div></div>}
    {remove.isError && <p className="form-error" role="alert">{errorText(remove.error)}</p>}
    {showHistory && <div className="direction-history"><h3>История расчётов</h3>{totalSnapshots != null && <p className="small-copy">Сохранено {totalSnapshots} из 500. Осталось обновлений: {500 - totalSnapshots}.</p>}{history.isPending ? <p role="status">Загружаем историю…</p> : <>
      {history.isError && <p className="form-error" role="alert">{errorText(history.error)} <button className="text-button" type="button" onClick={() => void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())}>Повторить загрузку истории</button></p>}
      {snapshots.length > 0 && <><HistoryComparison snapshots={snapshots} /><p className="small-copy">Загружено {snapshots.length} сохранений. Дата — время ручного ввода.</p><div className="history-scroll"><table><caption className="visually-hidden">Сохранённые значения и рассчитанное место</caption><thead><tr><th>Дата и время</th><th>Номер</th><th>Вне конкурса</th><th>Без согласия</th><th>Место</th><th>При всех согласиях</th><th>Бюджет</th><th>Модель</th></tr></thead><tbody>{snapshots.map(snapshot => <tr key={snapshot.id}><td><time dateTime={snapshot.capturedAt}>{exactDate(snapshot.capturedAt)}</time></td><td>{snapshot.values.rank}</td><td>{snapshot.values.excluded}</td><td>{snapshot.values.noConsent}</td><td>{snapshot.calculation.place}</td><td>{snapshot.calculation.worstPlace}</td><td>{snapshot.values.seats}</td><td>{snapshot.modelVersion}</td></tr>)}</tbody></table></div></>}
      {history.hasNextPage && <button className="text-button" type="button" disabled={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()}>{history.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё'}</button>}
    </>}</div>}
  </article>;
}

export default function TrackerPage() {
  const [reportDate, setReportDate] = useState('');
  const [search, setSearch] = useState('');
  const [scenario, setScenario] = useState('all');
  const [order, setOrder] = useState<WatchOrder>('updated');
  const [form, setForm] = useState<'new' | Watch | null>(null);
  const [focusRequest, setFocusRequest] = useState(0);
  const formOpener = useRef<HTMLButtonElement | null>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  const draftDirty = useRef(false);
  const setDraftDirty = useCallback((dirty: boolean) => { draftDirty.current = dirty; }, []);
  const canDiscard = () => !draftDirty.current || window.confirm('Удалить несохранённые изменения формы?');
  function openForm(value: 'new' | Watch, button: HTMLButtonElement) {
    const sameForm = form === value || (form && form !== 'new' && value !== 'new' && form.id === value.id);
    if (!sameForm && !canDiscard()) return;
    formOpener.current = button;
    setNotice('');
    setForm(value);
    setFocusRequest(request => request + 1);
  }
  function closeForm(saved = false) {
    if (!saved && !canDiscard()) return;
    draftDirty.current = false;
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
  const access = useQuery<SessionAccess>({ queryKey: sessionAccessKey, queryFn: async (): Promise<SessionAccess> => 'active', enabled: false, initialData: 'active' });
  const expired = access.data === 'expired' || watches.error instanceof SessionExpiredError;
  useEffect(() => {
    if (expired) { draftDirty.current = false; setForm(null); setConfirmReset(false); setNotice(''); }
  }, [expired]);
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
      queryClient.setQueryData<SessionAccess>(sessionAccessKey, 'active');
      download.reset();
    },
  });
  const count = expired || watches.isError ? 0 : watches.data?.length ?? 0;
  const visible = selectWatches(watches.data ?? [], search, scenario, order);
  return <main className="container tracker-page" id="top">
    <div className="tracker-page-heading"><div><p className="eyebrow">Ваша приёмная кампания</p><h1>Мои направления</h1><p className="section-description">Сравнивайте место и сохраняйте изменения в одном окне.</p></div><button ref={addButton} className="button button-primary" type="button" disabled={expired || count >= 20 || busy} onClick={event => openForm('new', event.currentTarget)}>Добавить направление</button></div>
    <div className="tracker-info"><span className="tag">Ручной режим</span><p>Направления доступны в этом браузере 30 дней с начала сессии. Очистка cookies удалит доступ. Автоматическое обновление вузов ещё не подключено.</p></div>
    <div className="tracker-data-actions"><button className="text-button" type="button" disabled={busy || !count} onClick={() => download.mutate()}>{download.isPending ? 'Готовим файл…' : 'Скачать данные (JSON)'}</button>
    {count > 0 && <button className="text-button delete-link" type="button" disabled={busy} onClick={() => setConfirmReset(true)}>Удалить все мои данные</button>}</div>
    {download.isError && <p className="form-error" role="alert">{errorText(download.error)}</p>}
    {confirmReset && !expired && <div className="delete-confirm surface"><p>Удалить все направления и историю в этом браузере? Отменить удаление нельзя.</p><div><button className="button button-secondary" type="button" disabled={reset.isPending} onClick={() => setConfirmReset(false)}>Отмена</button><button className="button danger-button" type="button" disabled={reset.isPending} onClick={() => reset.mutate()}>Удалить всё</button></div></div>}
    {expired && <div className="surface empty-state"><h2>Срок гостевой сессии истёк</h2><p>Доступ к прежним направлениям завершён или cookies были удалены. Для дальнейшей работы начните новую сессию.</p><button className="button button-primary" type="button" disabled={reset.isPending} onClick={() => reset.mutate()}>{reset.isPending ? 'Создаём…' : 'Начать новую сессию'}</button></div>}
    {reset.isError && <p className="form-error" role="alert">{errorText(reset.error)}</p>}
    <p className="tracker-notice" role="status">{notice}</p>
    <CoverageSummary />
    {!expired && <ImportData count={count} disabled={busy || watches.isPending || watches.isError} onDone={result => setNotice(result.replayed ? 'Этот файл уже импортирован. Повтор не создаёт копий и не восстанавливает удалённое.' : `Импортировано направлений: ${result.importedCount}; сохранений: ${result.snapshotCount}.`)} />}
    {!expired && !watches.isError && watches.data && <WatchComparison watches={watches.data} />}
    {!expired && count > 0 && <section className="watch-filters surface" aria-label="Поиск направлений">
      <div className="field"><label htmlFor="watch-search">Поиск по вузу и направлению</label><input id="watch-search" type="search" value={search} onChange={event => setSearch(event.target.value)} /></div>
      <div className="field"><label htmlFor="watch-state">Ручной сценарий</label><select id="watch-state" value={scenario} onChange={event => setScenario(event.target.value)}><option value="all">Все сценарии</option><option value="safe">В пределах в обоих сценариях</option><option value="conditional">В пределах только при текущих согласиях</option><option value="out">За границей мест</option></select></div>
      <div className="field"><label htmlFor="watch-order">Порядок направлений</label><select id="watch-order" value={order} onChange={event => setOrder(event.target.value as WatchOrder)}><option value="updated">Недавно сохранённые</option><option value="university">По вузу и названию</option><option value="created">Недавно добавленные</option></select></div>
      <p role="status">Показано {visible.length} из {count}</p><button className="text-button" type="button" onClick={() => { setSearch(''); setScenario('all'); setOrder('updated'); }}>Сбросить поиск и фильтры</button>
    </section>}
    <div className={`tracker-layout ${form && !expired ? 'with-form' : ''}`}><div className="directions-list">
      {expired ? null : watches.isPending ? <div className="empty-state surface" role="status"><h2>Загружаем направления…</h2><p>Проверяем сохранённые данные.</p></div> : watches.isError ? <div className="empty-state surface" role="alert"><h2>Не удалось загрузить направления</h2><p>{errorText(watches.error)}</p><button className="button button-secondary" type="button" onClick={() => void watches.refetch()}>Повторить</button></div> : count === 0 ? <div className="empty-state surface"><span className="empty-mark" aria-hidden="true">＋</span><h2>Направлений пока нет</h2><p>Добавьте вуз, направление и ссылку на список. Введите текущие цифры — сервис сохранит расчёт и его историю.</p><button className="button button-primary" type="button" onClick={event => openForm('new', event.currentTarget)}>Добавить первое направление</button></div> : visible.length === 0 ? <div className="surface empty-state"><h2>Поиск не дал результатов</h2><p>Измените запрос или сбросьте фильтры. Сохранённые направления остаются в кабинете.</p></div> : visible.map(watch => <DirectionCard key={watch.id} watch={watch} disabled={busy} onEdit={button => openForm(watch, button)} beforeDelete={() => form === null || form === 'new' || form.id !== watch.id || canDiscard()} onRemoved={() => { if (form && form !== 'new' && form.id === watch.id) closeForm(true); setNotice('Направление удалено.'); }} />)}
    </div>{form && !expired && <aside className="tracker-sidebar"><DirectionForm key={form === 'new' ? 'new' : form.id} focusRequest={focusRequest} watch={form === 'new' ? undefined : form} onDirtyChange={setDraftDirty} onCancel={() => closeForm()} onDone={() => { closeForm(true); setNotice('Данные сохранены. Расчёт и история обновлены.'); }} /></aside>}</div>
    {!expired && count > 0 && <button className="text-button print-action" type="button" disabled={visible.length === 0 || busy} onClick={() => { setReportDate(new Date().toISOString()); requestAnimationFrame(() => window.print()); }}>Распечатать выбранный список ({visible.length})</button>}
    {!expired && <ManualReport watches={visible} generatedAt={reportDate} />}
    <p className="tracker-disclaimer">Расчёт описывает положение по введённым данным в одной конкурсной группе. Он не учитывает все правила и приоритеты конкретного вуза и не гарантирует зачисление.</p>
  </main>;
}
