let sessionEpoch = 0;
window.addEventListener('storage', event => {
    if (event.key === 'admitflow-session-change')
        sessionEpoch++;
});
export class ApiError extends Error {
    constructor(public status: number, message?: string) {
        super(message ?? ({ 401: 'Гостевой доступ завершён. Начните новую сессию.', 403: 'Действие недоступно. Проверьте гостевой доступ.', 409: 'Данные изменились или источник недоступен. Проверьте список и повторите действие.', 410: 'Срок подтверждения истёк. Найдите запись заново.', 404: 'Запись не найдена', 422: 'Проверьте параметры запроса.', 429: 'Слишком много запросов. Повторите позже.' }[status] ?? 'Не удалось загрузить данные'));
    }
}
export type Decoder<T> = (value: unknown) => T;
export async function request<T>(path: string, decode: Decoder<T>, init: RequestInit = {}): Promise<T> {
    const epoch = sessionEpoch;
    const controller = new AbortController();
    const abort = () => controller.abort();
    init.signal?.addEventListener('abort', abort, { once: true });
    if (init.signal?.aborted)
        controller.abort();
    const timeout = setTimeout(abort, 15000);
    try {
        const response = await fetch(`/api/v1/${path}`, { ...init, signal: controller.signal, credentials: 'same-origin', headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-Requested-With': 'abiturient', ...init.headers } });
        if (!path.startsWith('catalog/') && path !== 'session' && epoch !== sessionEpoch)
            throw new ApiError(401);
        if (!response.ok) {
            if (response.status === 401) {
                sessionEpoch++;
                window.dispatchEvent(new Event('admitflow-session-expired'));
            }
            throw new ApiError(response.status);
        }
        if (path === 'session' && init.method === 'POST') {
            sessionEpoch++;
            try {
                localStorage.setItem('admitflow-session-change', crypto.randomUUID());
            }
            catch { /* Other tabs reconcile on their next authorized request. */
            }
        }
        if (response.status === 204)
            return decode(null);
        if (!response.headers.get('content-type')?.includes('application/json'))
            throw new ApiError(502, 'Сервер вернул некорректные данные.');
        let body: unknown;
        try {
            body = await response.json();
        }
        catch {
            invalid();
        }
        return decode(body);
    }
    catch (error) {
        if (init.signal?.aborted)
            throw error;
        if (error instanceof ApiError)
            throw error;
        throw new ApiError(0, controller.signal.aborted ? 'Ответ занимает слишком много времени. Повторите запрос.' : 'Не удалось связаться с сервером. Повторите запрос.');
    }
    finally {
        clearTimeout(timeout);
        init.signal?.removeEventListener('abort', abort);
    }
}
export function invalid(): never {
    throw new ApiError(502, 'Не удалось проверить полученные данные.');
}
export function object(value: unknown): Record<string, unknown> {
    if (!value || typeof value !== 'object' || Array.isArray(value))
        return invalid();
    return value as Record<string, unknown>;
}
export function text(value: unknown): string {
    return typeof value === 'string' ? value : invalid();
}
export function count(value: unknown): number {
    return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : invalid();
}
export function array<T>(value: unknown, decode: Decoder<T>): T[] {
    return Array.isArray(value) ? value.map(decode) : invalid();
}
export function date(value: unknown): string {
    const s = text(value);
    if (!Number.isFinite(Date.parse(s)))
        invalid();
    return s;
}
export function url(value: unknown): string {
    const s = text(value);
    try {
        if (!['http:', 'https:'].includes(new URL(s).protocol))
            invalid();
    }
    catch {
        invalid();
    }
    return s;
}
