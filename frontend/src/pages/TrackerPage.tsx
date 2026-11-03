import { ArchiveDirections } from '../components/ArchiveDirections';
import { DirectionForm } from '../components/DirectionForm';
import { Link } from 'react-router';
import { DraftRecovery } from '../components/DraftRecovery';
import { clearDraft, readDraft } from '../lib/draft';
import type { StoredDraft } from '../lib/draft';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useInfiniteQuery, useIsMutating, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ScenarioExplanation } from '../components/ScenarioExplanation';
import { HistoryComparison } from '../components/HistoryComparison';
import { WatchComparison } from '../components/WatchComparison';
import { ImportData } from '../components/ImportData';
import { CoverageSummary } from '../components/CoverageSummary';
import { downloadExport } from '../lib/download';
import { api, SessionExpiredError } from '../lib/api';
import type { Watch } from '../lib/api';
import { assertSnapshotOrder } from '../lib/contracts';
import { sessionAccessKey } from '../lib/query-client';
import type { SessionAccess } from '../lib/query-client';
import { selectWatches } from '../lib/watch-list';
import type { WatchOrder } from '../lib/watch-list';
import { ManualReport } from '../components/ManualReport';
import { DeleteConfirmation } from '../components/DeleteConfirmation';

const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
const exactDateFormat = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'medium' });
function date(value: string) { return dateFormat.format(new Date(value)); }
function exactDate(value: string) { return `${exactDateFormat.format(new Date(value))} (${value})`; }
function errorText(error: unknown) { return error instanceof Error ? error.message : 'Не удалось выполнить действие.'; }

function DirectionCard({ watch, onEdit, disabled, beforeDelete, onRemoved }: { watch: Watch; onEdit: (button: HTMLButtonElement) => void; disabled: boolean; beforeDelete: () => boolean; onRemoved: () => void }) {
  const deleteButton = useRef<HTMLButtonElement>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const queryClient = useQueryClient();
  const history = useInfiniteQuery({ queryKey: ['history', watch.id], initialPageParam: null as string | null, queryFn: ({ pageParam, signal }) => api.history(watch.id, pageParam, signal), getNextPageParam: page => page.nextCursor, enabled: showHistory,
    select: data => { const snapshots = data.pages.flatMap(page => page.items); assertSnapshotOrder(snapshots); return { ...data, snapshots }; } });
  const snapshots = history.data?.snapshots ?? [];
  const totalSnapshots = history.data?.pages[0]?.total;
  const remove = useMutation({ mutationFn: () => api.remove(watch.id), onSuccess: async () => { onRemoved(); await queryClient.invalidateQueries({ queryKey: ['watches'] }); await queryClient.invalidateQueries({ queryKey: ['direction-budget'] }); } });
  const { calculation } = watch.latest;
  const old = Date.now() - new Date(watch.latest.capturedAt).getTime() > 86400_000;
  return <article className="direction-card surface">
    <div className="direction-top"><span className="eyebrow">{watch.university}</span><span className="tag">Ручной ввод</span></div>
    <h2>{watch.title}</h2>
    <div className="direction-result"><strong>{calculation.place}</strong><span>по вашему вводу<br /><b>{calculation.seats}</b> бюджетных мест</span></div>
    <p className="result-status" data-state={calculation.state}>{calculation.status}</p>
    <p className="direction-worst">Если все выше вас подадут согласие: <b>{calculation.worstPlace}-е место</b>.</p>
    <ScenarioExplanation values={watch.latest.values} />
    <p className="small-copy">Модель ручного сценария: {watch.latest.modelVersion}. Дата сохранения — время вашего ввода, обновление источника не проверено.</p>
    <div className="direction-source"><a href={watch.sourceUrl} target="_blank" rel="noopener noreferrer">Открыть источник ↗</a><span>Сохранено <time dateTime={watch.latest.capturedAt}>{date(watch.latest.capturedAt)}</time></span></div>
    {old && <p className="stale-note">Цифры сохранены больше суток назад. Проверьте свежий список.</p>}
    <div className="direction-actions"><button className="button button-secondary" type="button" disabled={disabled} onClick={event => onEdit(event.currentTarget)}>Обновить цифры</button><button className="text-button" type="button" aria-expanded={showHistory} onClick={() => setShowHistory(!showHistory)}>История</button><button ref={deleteButton} className="text-button delete-link" type="button" disabled={disabled} onClick={() => setConfirmDelete(!confirmDelete)}>Удалить</button></div>
    {confirmDelete && <DeleteConfirmation text="Удалить направление и всю его историю?" label="Да, удалить" disabled={disabled || remove.isPending} onCancel={() => { setConfirmDelete(false); requestAnimationFrame(() => deleteButton.current?.focus()); }} onConfirm={() => { if (beforeDelete()) remove.mutate(); }} />}
    {remove.isError && <p className="form-error" role="alert">{errorText(remove.error)}</p>}
    {showHistory && <div className="direction-history"><h3>История расчётов</h3>{totalSnapshots != null && <p className="small-copy">Сохранено {totalSnapshots} из 500. Осталось обновлений: {500 - totalSnapshots}.</p>}{history.isPending ? <p role="status">Загружаем историю…</p> : <>
      {history.isError && <p className="form-error" role="alert">{errorText(history.error)} <button className="text-button" type="button" onClick={() => void (history.isFetchNextPageError ? history.fetchNextPage() : history.refetch())}>Повторить загрузку истории</button></p>}
      {snapshots.length > 0 && <><HistoryComparison snapshots={snapshots} /><p className="small-copy">Загружено {snapshots.length} сохранений. Дата — время ручного ввода.</p><p className="small-copy">Таблицу можно прокручивать вбок, в том числе стрелками с клавиатуры после перехода в неё.</p><div className="history-scroll" tabIndex={0} role="region" aria-label={`История ${watch.title}`}><table><caption className="visually-hidden">Сохранённые значения и рассчитанное место</caption><thead><tr><th scope="col">Дата и время</th><th scope="col">Номер</th><th scope="col">Вне конкурса</th><th scope="col">Без согласия</th><th scope="col">Место</th><th scope="col">При всех согласиях</th><th scope="col">Бюджет</th><th scope="col">Модель</th></tr></thead><tbody>{snapshots.map(snapshot => <tr key={snapshot.id}><td><time dateTime={snapshot.capturedAt}>{exactDate(snapshot.capturedAt)}</time></td><td>{snapshot.values.rank}</td><td>{snapshot.values.excluded}</td><td>{snapshot.values.noConsent}</td><td>{snapshot.calculation.place}</td><td>{snapshot.calculation.worstPlace}</td><td>{snapshot.values.seats}</td><td>{snapshot.modelVersion}</td></tr>)}</tbody></table></div></>}
      {history.hasNextPage && <button className="text-button" type="button" disabled={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()}>{history.isFetchingNextPage ? 'Загружаем…' : 'Загрузить ещё'}</button>}
    </>}</div>}
  </article>;
}

export default function TrackerPage() {
  const resetButton = useRef<HTMLButtonElement>(null);
  const [reportDate, setReportDate] = useState(() => new Date().toISOString());
  const [search, setSearch] = useState('');
  const [scenario, setScenario] = useState('all');
  const [order, setOrder] = useState<WatchOrder>('updated');
  const [form, setForm] = useState<'new' | Watch | null>(null);
  const [recovery, setRecovery] = useState<StoredDraft | null>(null);
  const [restored, setRestored] = useState<StoredDraft | null>(null);
  const [focusRequest, setFocusRequest] = useState(0);
  const [returnFocus, setReturnFocus] = useState(false);
  const formOpener = useRef<HTMLButtonElement | null>(null);
  const addButton = useRef<HTMLButtonElement>(null);
  const pageHeading = useRef<HTMLHeadingElement>(null);
  const draftDirty = useRef(false);
  const setDraftDirty = useCallback((dirty: boolean) => { draftDirty.current = dirty; }, []);
  const canDiscard = () => !draftDirty.current || window.confirm('Удалить несохранённые изменения формы?');
  function openForm(value: 'new' | Watch, button: HTMLButtonElement) {
    const sameForm = form === value || (form && form !== 'new' && value !== 'new' && form.id === value.id);
    if (!sameForm && !canDiscard()) return;
    if (!form && recovery && !window.confirm('Заменить сохранённый черновик новой формой?')) return;
    if (!sameForm) { clearDraft(); setRecovery(null); setRestored(null); }
    formOpener.current = button;
    setReturnFocus(false);
    setNotice('');
    setForm(value);
    setFocusRequest(request => request + 1);
  }
  function closeForm(saved = false) {
    if (!saved && !canDiscard()) return;
    draftDirty.current = false;
    clearDraft();
    setRecovery(null);
    setRestored(null);
    setForm(null);
    setReturnFocus(true);
  }
  const [notice, setNotice] = useState('');
  const [confirmReset, setConfirmReset] = useState(false);
  const busy = useIsMutating() > 0;
  const queryClient = useQueryClient();
  const access = useQuery<SessionAccess>({ queryKey: sessionAccessKey, queryFn: async (): Promise<SessionAccess> => 'active', enabled: false, initialData: 'active' });
  const changed = access.data === 'changed';
  const watches = useQuery({ queryKey: ['watches'], queryFn: ({ signal }) => api.list(signal), enabled: !changed, staleTime: 0, refetchOnWindowFocus: true });
  const expired = changed || access.data === 'expired' || watches.error instanceof SessionExpiredError;
  useEffect(() => {
    if (!returnFocus || busy || form || expired) return;
    const opener = formOpener.current;
    const target = opener?.isConnected && !opener.disabled ? opener
      : addButton.current && !addButton.current.disabled ? addButton.current : pageHeading.current;
    target?.focus();
    setReturnFocus(false);
  }, [returnFocus, busy, form, expired]);
  const sessionInfo = useQuery({ queryKey: ['session-info'], queryFn: api.session, enabled: !expired, staleTime: Infinity });
  useEffect(() => {
    if (!expired && !form && watches.isSuccess && sessionInfo.data?.draftScope) {
      setRecovery(readDraft(sessionInfo.data.draftScope, sessionInfo.data.expiresAt));
    }
  }, [expired, form, watches.isSuccess, watches.data, sessionInfo.data]);
  useEffect(() => {
    if (!recovery || form) return;
    const timer = setTimeout(() => {
      clearDraft(); setRecovery(null); setNotice('Срок хранения черновика закончился. Сохранённые направления не изменены.');
    }, Math.max(0, recovery.expiresAt - Date.now()));
    return () => clearTimeout(timer);
  }, [recovery, form]);
  const restore = useMutation({ mutationFn: async () => {
    if (!recovery || !sessionInfo.data?.draftScope) return null;
    // Recheck the cookie owner, including changes made without a storage event.
    const info = await api.resumeSession();
    if (info.draftScope !== sessionInfo.data.draftScope) {
      clearDraft(); setRecovery(null); api.forgetSession();
      queryClient.setQueryData<SessionAccess>(sessionAccessKey, 'changed');
      return null;
    }
    const latest = await api.list();
    queryClient.setQueryData(['watches'], latest);
    const current = readDraft(info.draftScope, info.expiresAt);
    if (!current) { setRecovery(null); setNotice('Черновик больше недоступен.'); return null; }
    const watch = current.watchId ? latest.find(item => item.id === current.watchId) : undefined;
    if (current.watchId && !watch) { setNotice('Направление черновика уже удалено. Поля можно посмотреть перед удалением черновика.'); return null; }
    if (watch && watch.latest.id !== current.baseSnapshotId && !current.intent) { setNotice('На сервере более новая версия. Устаревший черновик не восстановлен.'); return null; }
    return { current, watch };
  }, onSuccess: result => {
    if (!result) return;
    setRestored(result.current); setForm(result.watch ?? 'new'); setFocusRequest(value => value + 1); setRecovery(null);
  } });
  useEffect(() => {
    if (expired) { clearDraft(); draftDirty.current = false; setRecovery(null); setRestored(null); setForm(null); setConfirmReset(false); setNotice(''); }
  }, [expired]);
  const download = useMutation({ mutationFn: api.exportData, onSuccess: downloadExport });
  const synchronize = useMutation({ mutationFn: async () => {
    const info = await api.resumeSession();
    await queryClient.fetchQuery({ queryKey: ['watches'], queryFn: ({ signal }) => api.list(signal), staleTime: 0 });
    return info;
  }, onSuccess: info => {
    queryClient.setQueryData(['session-info'], info);
    for (const key of ['history', 'archive-directions', 'direction-budget', 'archive-history']) queryClient.removeQueries({ queryKey: [key] });
    queryClient.setQueryData<SessionAccess>(sessionAccessKey, 'active');
    download.reset();
    requestAnimationFrame(() => addButton.current?.focus());
  } });
  const reset = useMutation({
    mutationFn: async () => {
      await queryClient.cancelQueries({ queryKey: ['watches'] });
      await queryClient.cancelQueries({ queryKey: ['history'] });
      await queryClient.cancelQueries({ queryKey: ['session-info'] });
      for (const key of ['archive-directions', 'direction-budget', 'archive-history']) await queryClient.cancelQueries({ queryKey: [key] });
      clearDraft(); setRecovery(null); setRestored(null); draftDirty.current = false; setForm(null);
      return api.resetSession();
    },
    onSuccess: async info => {
      queryClient.setQueryData(['session-info'], info);
      for (const key of ['history', 'archive-directions', 'direction-budget', 'archive-history']) queryClient.removeQueries({ queryKey: [key] });
      setForm(null);
      setConfirmReset(false);
      setNotice('Создана новая гостевая сессия.');
      await queryClient.invalidateQueries({ queryKey: ['watches'] });
      queryClient.setQueryData<SessionAccess>(sessionAccessKey, 'active');
      download.reset();
    requestAnimationFrame(() => addButton.current?.focus());
    },
  });
  const budget = useQuery({ queryKey: ['direction-budget'], queryFn: ({ signal }) => api.directionBudget(signal), enabled: !expired });
  const directionTotal = expired ? 0 : Math.max(budget.data?.total ?? 0, watches.data?.length ?? 0);
  const count = expired ? 0 : watches.data?.length ?? 0;
  const visible = selectWatches(watches.data ?? [], search, scenario, order);
  const recoveryWatch = recovery?.watchId ? watches.data?.find(item => item.id === recovery.watchId) : undefined;
  const recoveryBlocked = recovery?.watchId && !recoveryWatch ? 'Направление уже удалено.'
    : recoveryWatch && recoveryWatch.latest.id !== recovery?.baseSnapshotId && !recovery?.intent ? 'На сервере есть более новое сохранение.' : undefined;
  return <main className="container tracker-page" id="top">
    <div className="tracker-page-heading"><div><p className="eyebrow">Ваша приёмная кампания</p><h1 ref={pageHeading} tabIndex={-1}>Мои направления</h1><p className="section-description">Сравнивайте место и сохраняйте изменения в одном окне.</p><Link data-router-link to="/sources">Посмотреть источники и архивные группы →</Link></div><button ref={addButton} className="button button-primary" type="button" disabled={expired || directionTotal >= 20 || busy} onClick={event => openForm('new', event.currentTarget)}>Добавить направление</button></div>
    <div className="tracker-info"><span className="tag">Ручной режим</span><p>Направления доступны в этом браузере 30 дней с начала сессии. Очистка cookies удалит доступ. Автоматическое обновление вузов ещё не подключено.</p></div>
    {!expired && sessionInfo.data && <p className="small-copy session-deadline">Гостевой доступ до <time dateTime={sessionInfo.data.expiresAt} title={sessionInfo.data.expiresAt}>{new Intl.DateTimeFormat('ru-RU', { dateStyle: 'long', timeStyle: 'short' }).format(new Date(sessionInfo.data.expiresAt))}</time>. Открытие страницы не продлевает срок.</p>}
    {!expired && sessionInfo.isError && <p className="small-copy">Не удалось проверить точную дату окончания доступа.</p>}
    <div className="tracker-data-actions"><button className="text-button" type="button" disabled={expired || busy || watches.isFetching} onClick={async () => { const result = await watches.refetch(); if (!result.error) setNotice('Список направлений обновлён. Ручные цифры не загружались из вузов.'); }}>{watches.isFetching ? 'Обновляем…' : 'Обновить направления'}</button><button className="text-button" type="button" disabled={busy || !count} onClick={() => download.mutate()}>{download.isPending ? 'Готовим файл…' : 'Скачать данные (JSON)'}</button>
    {directionTotal > 0 && <button ref={resetButton} className="text-button delete-link" type="button" disabled={busy} onClick={() => setConfirmReset(true)}>Удалить все мои данные</button>}</div>
    {download.isError && <p className="form-error" role="alert">{errorText(download.error)}</p>}
    {confirmReset && !expired && <DeleteConfirmation text="Удалить все направления и историю в этом браузере? Отменить удаление нельзя." label="Удалить всё" disabled={busy} onCancel={() => { setConfirmReset(false); requestAnimationFrame(() => resetButton.current?.focus()); }} onConfirm={() => reset.mutate()} />}
    {expired && <div className="surface empty-state"><h2>{changed ? 'Гостевой доступ изменён' : 'Срок гостевой сессии истёк'}</h2><p>{changed ? 'Старые карточки и черновик скрыты. Синхронизируйте доступ, чтобы увидеть текущую сессию.' : 'Доступ к прежним направлениям завершён или cookies были удалены. Для дальнейшей работы начните новую сессию.'}</p><button className="button button-primary" type="button" disabled={reset.isPending || synchronize.isPending} onClick={() => changed ? synchronize.mutate() : reset.mutate()}>{changed ? 'Синхронизировать доступ' : reset.isPending ? 'Создаём…' : 'Начать новую сессию'}</button></div>}
    {synchronize.isError && <p className="form-error" role="alert">{errorText(synchronize.error)}</p>}{reset.isError && <p className="form-error" role="alert">{errorText(reset.error)}</p>}
    <p className="tracker-notice" role="status">{notice}</p>
    {restore.isError && !expired && <p className="form-error" role="alert">Не удалось проверить доступ перед восстановлением. {errorText(restore.error)}</p>}
    {!expired && !form && recovery && <DraftRecovery record={recovery} blockedReason={recoveryBlocked} disabled={busy || watches.isFetching || watches.isError} onRestore={() => restore.mutate()} onDiscard={() => {
      if (!clearDraft()) { setNotice('Не удалось удалить черновик из хранилища вкладки.'); return; }
      setRecovery(null); setNotice('Черновик удалён. Сохранённые направления не изменены.'); requestAnimationFrame(() => addButton.current?.focus());
    }} />}
    {!expired && watches.isError && watches.data && <div className="surface stale-warning" role="alert"><p>Не удалось обновить направления. Показаны последние загруженные сохранения с их исходными датами.</p><p>{errorText(watches.error)}</p><button className="text-button" type="button" disabled={watches.isFetching} onClick={() => void watches.refetch()}>Повторить обновление</button></div>}
    <CoverageSummary />
    {!expired && <ArchiveDirections />}
    {!expired && <p className="small-copy">Всего направлений: {directionTotal} из 20 (ручные и архивные вместе). JSON, сравнение и печать ниже включают только ручные направления.</p>}
    {!expired && <ImportData count={directionTotal} disabled={busy || watches.isPending || watches.isError || budget.isPending || budget.isError} onDone={result => setNotice(result.replayed ? 'Этот файл уже импортирован. Повтор не создаёт копий и не восстанавливает удалённое.' : `Импортировано направлений: ${result.importedCount}; сохранений: ${result.snapshotCount}.`)} />}
    {!expired && !watches.isError && watches.data && <WatchComparison watches={watches.data} />}
    {!expired && count > 0 && <section className="watch-filters surface" aria-label="Поиск направлений">
      <div className="field"><label htmlFor="watch-search">Поиск по вузу и направлению</label><input id="watch-search" type="search" value={search} onChange={event => setSearch(event.target.value)} /></div>
      <div className="field"><label htmlFor="watch-state">Ручной сценарий</label><select id="watch-state" value={scenario} onChange={event => setScenario(event.target.value)}><option value="all">Все сценарии</option><option value="safe">В пределах в обоих сценариях</option><option value="conditional">В пределах только при текущих согласиях</option><option value="out">За границей мест</option></select></div>
      <div className="field"><label htmlFor="watch-order">Порядок направлений</label><select id="watch-order" value={order} onChange={event => setOrder(event.target.value as WatchOrder)}><option value="updated">Недавно сохранённые</option><option value="university">По вузу и названию</option><option value="created">Недавно добавленные</option></select></div>
      <p role="status">Показано {visible.length} из {count}</p><button className="text-button" type="button" onClick={() => { setSearch(''); setScenario('all'); setOrder('updated'); }}>Сбросить поиск и фильтры</button>
    </section>}
    <div className={`tracker-layout ${form && !expired ? 'with-form' : ''}`}><div className="directions-list">
      {expired ? null : watches.isPending ? <div className="empty-state surface" role="status"><h2>Загружаем направления…</h2><p>Проверяем сохранённые данные.</p></div> : watches.isError && !watches.data ? <div className="empty-state surface" role="alert"><h2>Не удалось загрузить направления</h2><p>{errorText(watches.error)}</p><button className="button button-secondary" type="button" onClick={() => void watches.refetch()}>Повторить</button></div> : count === 0 ? <div className="empty-state surface"><span className="empty-mark" aria-hidden="true">＋</span><h2>{directionTotal ? 'Ручных направлений пока нет' : 'Направлений пока нет'}</h2><p>Добавьте вуз, направление и ссылку на список. Введите текущие цифры — сервис сохранит расчёт и его историю.</p><button className="button button-primary" type="button" disabled={directionTotal >= 20 || busy} onClick={event => openForm('new', event.currentTarget)}>Добавить первое направление</button></div> : visible.length === 0 ? <div className="surface empty-state"><h2>Поиск не дал результатов</h2><p>Измените запрос или сбросьте фильтры. Сохранённые направления остаются в кабинете.</p></div> : visible.map(watch => <DirectionCard key={watch.id} watch={watch} disabled={busy} onEdit={button => openForm(watch, button)} beforeDelete={() => form === null || form === 'new' || form.id !== watch.id || canDiscard()} onRemoved={() => { if (form && form !== 'new' && form.id === watch.id) closeForm(true); setNotice('Направление удалено.'); requestAnimationFrame(() => addButton.current?.focus()); }} />)}
    </div>{form && !expired && <aside className="tracker-sidebar"><DirectionForm restored={restored} sessionInfo={sessionInfo.data} disabled={busy} key={form === 'new' ? 'new' : form.id} focusRequest={focusRequest} watch={form === 'new' ? undefined : form} onDirtyChange={setDraftDirty} onCancel={() => closeForm()} onDone={() => { closeForm(true); setNotice('Данные сохранены. Расчёт и история обновлены.'); }} /></aside>}</div>
    {!expired && count > 0 && <button className="text-button print-action" type="button" disabled={visible.length === 0 || busy} onClick={() => { setReportDate(new Date().toISOString()); requestAnimationFrame(() => window.print()); }}>Распечатать выбранный список ({visible.length})</button>}
    {!expired && <ManualReport watches={visible} generatedAt={reportDate} />}
    <p className="tracker-disclaimer">Расчёт описывает положение по введённым данным в одной конкурсной группе. Он не учитывает все правила и приоритеты конкретного вуза и не гарантирует зачисление.</p>
  </main>;
}
