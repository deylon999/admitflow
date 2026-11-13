let sessionEpoch = 0;
export const sessionChanged = 'admitflow-session-change';
export const sessionExpired = 'admitflow-session-expired';
window.addEventListener('storage', event => {
    if (event.key !== sessionChanged && event.key !== null) return;
    let expired = false;
    try { expired = JSON.parse(event.newValue ?? 'null')?.expired === true; }
    catch { /* Previous clients used an opaque change marker. */ }
    changeSession(false, expired);
});

function changeSession(broadcast: boolean, expired = false) {
    sessionEpoch++;
    window.dispatchEvent(new Event(expired ? sessionExpired : sessionChanged));
    if (broadcast) {
        try { localStorage.setItem(sessionChanged, JSON.stringify({ id: crypto.randomUUID(), expired })); }
        catch { /* Other tabs reconcile on their next authorized request. */ }
    }
}

export type ApiScope = 'public' | 'guest' | 'auth' | 'account';
export function apiScope(path: string): ApiScope {
    const route = path.split('?')[0];
    if (route.startsWith('auth/')) return 'auth';
    if (route.startsWith('account/')) return 'account';
    // Competition responses contain guest myRank/mine, including anonymous reads.
    if (route.startsWith('catalog/') || route === 'groups' || route === 'coverage' || route.startsWith('coverage/') || /^sources\/[^/]+\/status$/.test(route)) return 'public';
    return 'guest';
}
export function sessionBound(path: string): boolean { return apiScope(path) === 'guest'; }
export const accountInvalidated = 'admitflow-account-invalidated';
export const accountChanged = 'admitflow-account-changed';
let accountEpoch = 0;
const accountRequests = new Set<AbortController>();
export function invalidateAccount() {
    accountEpoch++;
    for (const controller of accountRequests) controller.abort();
    window.dispatchEvent(new Event(accountInvalidated));
}
let accountPolicy: { ready: () => Promise<void>; refresh: () => Promise<void>; expired: () => void } | undefined;
export function configureAccountPolicy(policy: NonNullable<typeof accountPolicy>) { accountPolicy = policy; }
const authMessages: Record<string, string> = {
    not_authenticated: 'Не удалось войти. Проверьте данные и подтверждение email.',
    access_expired: 'Срок доступа истёк. Войдите снова.',
    csrf_invalid: 'Не удалось подтвердить безопасность запроса. Повторите действие.',
    invalid_token: 'Ссылка недействительна или срок её действия истёк. Запросите новую.',
    invalid_input: 'Проверьте email и пароль. Новый пароль: от 15 до 128 символов.',
    auth_unavailable: 'Авторизация временно недоступна. Повторите позже.',
    rate_limited: 'Слишком много запросов. Повторите позже.',
};
export class ApiError extends Error {
    constructor(public status: number, message?: string, public requiresSession = status === 401, public code?: string, public retryAfter?: number) {
        super(message ?? ({ 400: 'Проверьте параметры запроса.', 401: 'Гостевой доступ не начат или уже завершён. Начните гостевую сессию, чтобы сохранять направления.', 403: 'Действие недоступно. Проверьте гостевой доступ.', 409: 'Данные изменились или источник недоступен. Проверьте список и повторите действие.', 410: 'Срок подтверждения истёк. Найдите запись заново.', 404: 'Запись не найдена', 422: 'Проверьте параметры запроса.', 429: 'Слишком много запросов. Повторите позже.' }[status] ?? (status >= 500 ? 'Сервер временно недоступен. Повторите позже.' : 'Не удалось загрузить данные')));
    }
}
export type Decoder<T> = (value: unknown) => T;
type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type RequestOptions = Omit<RequestInit, 'body'> & { expectedStatus?: number } & ({ json?: Json; body?: never } | { body?: BodyInit | null; json?: never });

export async function request<T>(path: string, decode: Decoder<T>, init: RequestOptions = {}): Promise<T> {
    if (apiScope(path) !== 'account' || !accountPolicy) return performRequest(path, decode, init);
    const ownerBefore = accountEpoch;
    await accountPolicy.ready();
    init.signal?.throwIfAborted();
    if (ownerBefore !== accountEpoch) throw new ApiError(401, 'Состояние аккаунта изменилось.', false, 'account_changed');
    try { return await performRequest(path, decode, init); }
    catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error;
        if (error.code === 'account_changed') throw error;
        if (error.code !== 'access_expired') { accountPolicy.expired(); throw error; }
        await accountPolicy.refresh();
        init.signal?.throwIfAborted();
        if (ownerBefore !== accountEpoch) throw new ApiError(401, 'Состояние аккаунта изменилось.', false, 'account_changed');
        try { return await performRequest(path, decode, init); }
        catch (retryError) {
            if (retryError instanceof ApiError && retryError.status === 401) accountPolicy.expired();
            throw retryError;
        }
    }
}
async function performRequest<T>(path: string, decode: Decoder<T>, init: RequestOptions): Promise<T> {
    const epoch = sessionEpoch;
    const ownerEpoch = accountEpoch;
    const scope = apiScope(path);
    const accountRead = scope === 'account' || (path === 'auth/session' && (init.method ?? 'GET') === 'GET');
    const method = (init.method ?? 'GET').toUpperCase();
    const sessionWrite = path === 'session' && (method === 'POST' || method === 'DELETE');
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (accountRead) accountRequests.add(controller);
    const check = () => {
        if (accountRead && ownerEpoch !== accountEpoch) throw new ApiError(401, 'Состояние аккаунта изменилось.', false, 'account_changed');
        if (!sessionWrite && sessionBound(path) && epoch !== sessionEpoch) throw new ApiError(401);
        controller.signal.throwIfAborted();
    };
    init.signal?.addEventListener('abort', abort, { once: true });
    if (init.signal?.aborted) controller.abort();
    const timeout = setTimeout(abort, 15000);
    try {
        const { json, expectedStatus, ...options } = init;
        const headers = new Headers(init.headers);
        headers.set('Accept', 'application/json');
        headers.set('X-Requested-With', 'abiturient');
        let body = init.body;
        if (json !== undefined) {
            try {
                body = JSON.stringify(json, (_key, value: unknown) => {
                    if (value === undefined || typeof value === 'function' || typeof value === 'symbol' || typeof value === 'bigint' || (typeof value === 'number' && !Number.isFinite(value))) throw new Error('Invalid JSON value');
                    return value;
                });
            } catch { throw new ApiError(400, 'Не удалось подготовить данные запроса.'); }
            headers.set('Content-Type', 'application/json');
        }
        check();
        const response = await fetch(`/api/v1/${path}`, { ...options, body, signal: controller.signal, credentials: 'same-origin', headers });
        check();
        if (!response.ok) {
            if (response.status === 401 && sessionBound(path)) changeSession(true, true);
            let code: string | undefined;
            if (scope === 'auth' || scope === 'account') {
                // Error bodies never reach the UI; accept only a bounded, known code.
                const reader = response.body?.getReader();
                if (reader) {
                    try {
                        let size = 0;
                        const chunks: Uint8Array[] = [];
                        while (true) {
                            const chunk = await reader.read();
                            if (chunk.done) break;
                            size += chunk.value.byteLength;
                            if (size > 4096) break;
                            chunks.push(chunk.value);
                        }
                        if (size <= 4096) {
                            const bytes = new Uint8Array(size);
                            let offset = 0;
                            for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
                            const value: unknown = JSON.parse(new TextDecoder().decode(bytes));
                            if (value && typeof value === 'object' && 'code' in value && typeof value.code === 'string' && Object.hasOwn(authMessages, value.code)) code = value.code;
                        }
                    } catch { /* A malformed error remains a safe status-only error. */ }
                    finally { void reader.cancel().catch(() => {}); }
                }
            }
            check();
            const retry = response.headers.get('Retry-After');
            const retryAfter = retry && /^\d{1,6}$/.test(retry) ? Math.min(Number(retry), 86400) : undefined;
            const message = code ? authMessages[code] : response.status === 401 && scope === 'public' ? 'Не удалось получить доступ к данным. Повторите запрос позже.' : response.status === 401 && !sessionBound(path) ? 'Не удалось получить доступ к аккаунту. Войдите снова.' : response.status === 403 && scope === 'auth' ? 'Не удалось подтвердить безопасность запроса. Повторите действие.' : undefined;
            throw new ApiError(response.status, message, sessionBound(path), code, retryAfter);
        }
        if (expectedStatus !== undefined && response.status !== expectedStatus) invalid();
        if ((method === 'DELETE' || sessionWrite) && response.status !== 204) invalid();
        let value: unknown = null;
        if (response.status !== 204) {
            if (response.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') throw new ApiError(502, 'Сервер вернул некорректные данные.');
            try { value = await response.json(); }
            catch {
                check();
                invalid();
            }
        }
        // fetch resolves at headers; owner/abort can change while reading its body.
        check();
        let result: T;
        try { result = decode(value); }
        catch { invalid(); }
        check();
        if (sessionWrite) changeSession(true);
        return result;
    }
    catch (error) {
        if (init.signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
        if (accountRead && ownerEpoch !== accountEpoch) throw new ApiError(401, 'Состояние аккаунта изменилось.', false, 'account_changed');
        if (error instanceof ApiError) throw error;
        throw new ApiError(0, controller.signal.aborted ? 'Ответ занимает слишком много времени. Повторите запрос.' : 'Не удалось связаться с сервером. Повторите запрос.');
    }
    finally {
        accountRequests.delete(controller);
        clearTimeout(timeout);
        init.signal?.removeEventListener('abort', abort);
    }
}
export function invalid(): never { throw new ApiError(502, 'Не удалось проверить полученные данные.'); }
export function object(value: unknown): Record<string, unknown> {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return invalid();
    return value as Record<string, unknown>;
}
export function text(value: unknown): string { return typeof value === 'string' ? value : invalid(); }
export function identifier(value: unknown): string {
    const s = text(value);
    return s.trim() && !/[\s/\\?#]/.test(s) && !Array.from(s).some(c => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127) ? s : invalid();
}
export function count(value: unknown): number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : invalid(); }
export function positive(value: unknown): number { const n = count(value); return n > 0 ? n : invalid(); }
export function year(value: unknown): number { const n = count(value); return n >= 1900 && n <= 9999 ? n : invalid(); }
export function bool(value: unknown): boolean { return typeof value === 'boolean' ? value : invalid(); }
export function nullable<T>(value: unknown, read: Decoder<T>): T | null { return value === null ? null : read(value); }
export function oneOf<const T extends string>(value: unknown, options: readonly T[]): T {
    return options.find(option => option === value) ?? invalid();
}
export function array<T>(value: unknown, decode: Decoder<T>): T[] { return Array.isArray(value) ? value.map(decode) : invalid(); }
export function date(value: unknown): string {
    const s = text(value);
    const match = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|([+-])(\d{2}):(\d{2})))?$/.exec(s);
    if (!match || !Number.isFinite(Date.parse(s))) return invalid();
    const [, y, m, d, h, min, sec, , offsetHour, offsetMinute] = match;
    const calendar = new Date(`${y}-${m}-${d}T00:00:00Z`);
    if (calendar.getUTCFullYear() !== Number(y) || calendar.getUTCMonth() + 1 !== Number(m) || calendar.getUTCDate() !== Number(d) || Number(h ?? 0) > 23 || Number(min ?? 0) > 59 || Number(sec ?? 0) > 59 || Number(offsetHour ?? 0) > 23 || Number(offsetMinute ?? 0) > 59) invalid();
    return s;
}
export function url(value: unknown): string {
    const s = text(value);
    try { if (!['http:', 'https:'].includes(new URL(s).protocol)) invalid(); }
    catch { invalid(); }
    return s;
}
export function checksum(value: unknown): string {
    const s = text(value);
    return /^[a-f0-9]{64}$/.test(s) ? s : invalid();
}
