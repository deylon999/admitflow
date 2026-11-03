import type { CalculationValues } from './calculator';
import type { DataExport, SessionInfo, WatchCreate } from './contracts';
import { readJsonResponse, RequestTimeoutError, withRequestTimeout } from './transport';
import { InvalidResponseError, parseCatalog, parseCoverage, parseDetail, parseExport, parseHistoryPage, parseImportResult, parseSession, parseSnapshot, parseWatch, parseWatches } from './contracts';
import { parseArchiveDirections, parseArchiveHistory, parseDirectionBudget, parseGroupCatalog, parseLookup, parseSubscriptionSaved, parseSourceChecks, parseArchiveExport } from './source-contracts';
export type { Snapshot, Watch, WatchDetail, WatchCreate, SessionInfo, University, Catalog } from './contracts';
export class SessionExpiredError extends Error {
  constructor() { super('Срок доступа истёк или данные браузера были удалены. Начните новую сессию, чтобы сохранять направления снова.'); }
}
export class SessionChangedError extends Error {
  constructor() { super('Доступ изменился во время запроса. Синхронизируйте текущую сессию.'); }
}
let sessionEpoch = 0;
class ApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}
async function request(path: string, init: RequestInit = {}): Promise<unknown> {
  const epoch = sessionEpoch;
  const privateRequest = !path.startsWith('/universities') && !path.startsWith('/groups') && path !== '/coverage';
  const checkAccess = () => { if (privateRequest && epoch !== sessionEpoch) throw new SessionChangedError(); };
  return withRequestTimeout(async signal => {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, { ...init, signal, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'abiturient', ...init.headers } });
  } catch { signal.throwIfAborted(); checkAccess(); throw new Error('Не удалось связаться с сервером. Проверьте соединение и попробуйте ещё раз.'); }
  try { checkAccess(); }
  catch (error) { void response.body?.cancel().catch(() => {}); throw error; }
  if (!response.ok) {
    if (response.status === 401) { void response.body?.cancel().catch(() => {}); throw new SessionExpiredError(); }
    const body = await readJsonResponse(response, signal, 64 * 1024).catch(() => null) as { detail?: unknown } | null;
    checkAccess();
    const message = typeof body?.detail === 'string' && body.detail.length <= 500 ? body.detail : response.status === 422 ? 'Проверьте названия, ссылку и числовые значения.' : 'Сервис временно недоступен. Попробуйте ещё раз.';
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined;
  let body: unknown;
  try { body = await readJsonResponse(response, signal); } catch { checkAccess(); throw new InvalidResponseError(); }
  checkAccess();
  return body;
  }, init.signal);
}
const sessionMarker = 'admitflow-session-used';
export const sessionChangeKey = 'admitflow-session-change';
let session: Promise<SessionInfo> | undefined;
function forgetSession() { sessionEpoch++; session = undefined; }
function usedSession() {
  try { return localStorage.getItem(sessionMarker) === '1'; } catch { return false; }
}
async function serializeSession<T>(operation: () => Promise<T>): Promise<T> {
  if (typeof navigator === 'undefined' || !navigator.locks) return operation();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new RequestTimeoutError()), 15_000);
  try {
    return await navigator.locks.request('admitflow-guest-session', { signal: controller.signal }, () => {
      clearTimeout(timer);
      return operation();
    });
  } finally { clearTimeout(timer); }
}
async function loadSession() {
    if (!usedSession()) await request('/session', { method: 'POST' });
    const info = parseSession(await request('/session'));
    try { localStorage.setItem(sessionMarker, '1'); } catch { /* Cookie access still works. */ }
    return info;
}
async function ensureSession() {
  if (!session) {
    const epoch = sessionEpoch;
    const pending = serializeSession(() => {
      if (epoch !== sessionEpoch) throw new SessionChangedError();
      return loadSession();
    }).catch(error => { if (session === pending) session = undefined; throw error; });
    session = pending;
  }
  return session;
}
async function read<T>(path: string, parse: (value: unknown) => T, signal?: AbortSignal): Promise<T> {
  signal?.throwIfAborted();
  const epoch = sessionEpoch;
  const pending = ensureSession();
  if (signal) {
    let abort!: () => void;
    const canceled = new Promise<never>((_resolve, reject) => { abort = () => reject(signal.reason); });
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
    try { await Promise.race([pending, canceled]); }
    finally { signal.removeEventListener('abort', abort); }
    signal.throwIfAborted();
  } else await pending;
  if (epoch !== sessionEpoch) throw new SessionChangedError();
  return parse(await request(path, { signal }));
}
export const api = {
  session: ensureSession,
  forgetSession,
  async resumeSession() {
    const info = parseSession(await request('/session'));
    session = Promise.resolve(info);
    try { localStorage.setItem(sessionMarker, '1'); } catch { /* Cookie still works. */ }
    return info;
  },
  async resetSession() {
    return serializeSession(async () => {
    forgetSession();
    await request('/session', { method: 'DELETE' });
    try { localStorage.setItem(sessionChangeKey, crypto.randomUUID()); } catch { /* Cross-tab notification unavailable. */ }
    session = undefined;
    try { localStorage.removeItem(sessionMarker); } catch { /* Storage may be disabled. */ }
    const info = await loadSession();
    session = Promise.resolve(info);
    return info;
    });
  },
  universities: async (query: string, signal?: AbortSignal) => parseCatalog(await request(`/universities?q=${encodeURIComponent(query)}`, { signal })),
  groups: async (filters: { q: string; universityId: string; branchId: string; year: string }, after: string | null = null, signal?: AbortSignal) => {
    const params = new URLSearchParams(Object.entries(filters).filter(([,value]) => value !== ''));
    if (after) params.set('after', after);
    return parseGroupCatalog(await request(`/groups?${params}`, { signal }));
  },
  async lookup(sourceId: string, publicCode: string) {
    await ensureSession();
    const value = parseLookup(await request(`/sources/${encodeURIComponent(sourceId)}/lookup`, { method: 'POST', body: JSON.stringify({ publicCode }) }));
    if (value.group.sourceId !== sourceId) throw new InvalidResponseError();
    return value;
  },
  async removeSubscription(id: string) { await ensureSession(); await request(`/subscriptions/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
  async subscribe(confirmationToken: string) {
    await ensureSession();
    return parseSubscriptionSaved(await request('/subscriptions', { method: 'POST', body: JSON.stringify({ confirmationToken }) }));
  },
  subscriptions: (signal?: AbortSignal) => read('/subscriptions', parseArchiveDirections, signal),
  exportArchive: () => read('/archive-export', parseArchiveExport),
  sourceChecks: async (id: string, signal?: AbortSignal) => parseSourceChecks(await request(`/sources/${encodeURIComponent(id)}/checks`, { signal })),
  archiveHistory: (id: string, before: string | null, signal?: AbortSignal) => read(`/subscriptions/${encodeURIComponent(id)}/history?limit=20${before ? `&before=${encodeURIComponent(before)}` : ''}`, parseArchiveHistory, signal),
  directionBudget: (signal?: AbortSignal) => read('/direction-budget', parseDirectionBudget, signal),
  coverage: async () => parseCoverage(await request('/coverage')),
  exportData: () => read('/export', parseExport),
  async importData(bundle: DataExport, key: string) {
    await ensureSession();
    return parseImportResult(await request('/import', { method: 'POST', body: JSON.stringify({ bundle }), headers: { 'Idempotency-Key': key } }));
  },
  list: (signal?: AbortSignal) => read('/watches', parseWatches, signal),
  detail: (id: string) => read(`/watches/${encodeURIComponent(id)}`, parseDetail),
  history: (id: string, before: string | null, signal?: AbortSignal) => read(`/watches/${encodeURIComponent(id)}/history${before ? `?before=${encodeURIComponent(before)}` : ''}`, parseHistoryPage, signal),
  async create(body: WatchCreate, key?: string) { await ensureSession(); return parseWatch(await request('/watches', { method: 'POST', body: JSON.stringify(body), headers: key ? { 'Idempotency-Key': key } : undefined })); },
  async update(id: string, values: CalculationValues, key?: string, expectedSnapshot?: string) { await ensureSession(); return parseSnapshot(await request(`/watches/${encodeURIComponent(id)}/snapshots`, { method: 'POST', body: JSON.stringify(values), headers: { ...(key ? { 'Idempotency-Key': key } : {}), ...(expectedSnapshot ? { 'X-Expected-Snapshot': expectedSnapshot } : {}) } })); },
  async remove(id: string) { await ensureSession(); await request(`/watches/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
};
