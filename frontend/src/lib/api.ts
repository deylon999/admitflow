import type { CalculationValues } from './calculator';
import type { SessionInfo, WatchCreate } from './contracts';
import { InvalidResponseError, parseCatalog, parseDetail, parseSession, parseSnapshot, parseWatch, parseWatches } from './contracts';
export type { Snapshot, Watch, WatchDetail, WatchCreate, SessionInfo, University, Catalog } from './contracts';
export class SessionExpiredError extends Error {
  constructor() { super('Срок доступа истёк или данные браузера были удалены. Начните новую сессию, чтобы сохранять направления снова.'); }
}
class ApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}
async function request(path: string, init: RequestInit = {}): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, { ...init, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'abiturient', ...init.headers } });
  } catch { throw new Error('Не удалось связаться с сервером. Проверьте соединение и попробуйте ещё раз.'); }
  if (!response.ok) {
    if (response.status === 401) throw new SessionExpiredError();
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    const message = typeof body?.detail === 'string' ? body.detail : response.status === 422 ? 'Проверьте названия, ссылку и числовые значения.' : 'Сервис временно недоступен. Попробуйте ещё раз.';
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined;
  try { return await response.json(); } catch { throw new InvalidResponseError(); }
}
const sessionMarker = 'admitflow-session-used';
let session: Promise<SessionInfo> | undefined;
function usedSession() {
  try { return localStorage.getItem(sessionMarker) === '1'; } catch { return false; }
}
async function ensureSession() {
  session ??= (async () => {
    if (!usedSession()) await request('/session', { method: 'POST' });
    const info = parseSession(await request('/session'));
    try { localStorage.setItem(sessionMarker, '1'); } catch { /* Cookie access still works. */ }
    return info;
  })().catch(error => { session = undefined; throw error; });
  return session;
}
async function read<T>(path: string, parse: (value: unknown) => T): Promise<T> {
  await ensureSession();
  return parse(await request(path));
}
export const api = {
  session: ensureSession,
  async resetSession() {
    await request('/session', { method: 'DELETE' });
    session = undefined;
    try { localStorage.removeItem(sessionMarker); } catch { /* Storage may be disabled. */ }
    return ensureSession();
  },
  universities: async (query: string) => parseCatalog(await request(`/universities?q=${encodeURIComponent(query)}`)),
  list: () => read('/watches', parseWatches),
  detail: (id: string) => read(`/watches/${encodeURIComponent(id)}`, parseDetail),
  async create(body: WatchCreate) { await ensureSession(); return parseWatch(await request('/watches', { method: 'POST', body: JSON.stringify(body) })); },
  async update(id: string, values: CalculationValues) { await ensureSession(); return parseSnapshot(await request(`/watches/${encodeURIComponent(id)}/snapshots`, { method: 'POST', body: JSON.stringify(values) })); },
  async remove(id: string) { await ensureSession(); await request(`/watches/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
};
