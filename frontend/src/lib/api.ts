import type { CalculationResult, CalculationValues } from './calculator';

export type Snapshot = { id: string; capturedAt: string; sourceKind: 'manual'; modelVersion: string; values: CalculationValues; calculation: CalculationResult };
export type Watch = { id: string; university: string; title: string; sourceUrl: string; createdAt: string; latest: Snapshot };
export type WatchDetail = Watch & { history: Snapshot[] };
export type WatchCreate = { university: string; title: string; sourceUrl: string; values: CalculationValues };
class ApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, { ...init, credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'abiturient', ...init.headers } });
  } catch { throw new Error('Не удалось связаться с сервером. Проверьте соединение и попробуйте ещё раз.'); }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: unknown } | null;
    const message = typeof body?.detail === 'string' ? body.detail : response.status === 422 ? 'Проверьте названия, ссылку и числовые значения.' : 'Сервис временно недоступен. Попробуйте ещё раз.';
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
let session: Promise<void> | undefined;
async function ensureSession() {
  session ??= request<void>('/session', { method: 'POST' }).catch(error => { session = undefined; throw error; });
  return session;
}
async function read<T>(path: string): Promise<T> {
  await ensureSession();
  try { return await request<T>(path); } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      session = undefined;
      await ensureSession();
      return request<T>(path);
    }
    throw error;
  }
}
export const api = {
  list: () => read<Watch[]>('/watches'),
  detail: (id: string) => read<WatchDetail>(`/watches/${encodeURIComponent(id)}`),
  async create(body: WatchCreate) { await ensureSession(); return request<Watch>('/watches', { method: 'POST', body: JSON.stringify(body) }); },
  async update(id: string, values: CalculationValues) { await ensureSession(); return request<Snapshot>(`/watches/${encodeURIComponent(id)}/snapshots`, { method: 'POST', body: JSON.stringify(values) }); },
  async remove(id: string) { await ensureSession(); return request<void>(`/watches/${encodeURIComponent(id)}`, { method: 'DELETE' }); },
};
