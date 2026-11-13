import { accountChanged, ApiError, configureAccountPolicy, invalidateAccount, request, type Decoder } from './api';
import { accepted, accountSession, csrfToken, noContent, type AccountSession } from './authDto';

export type AccountState = { status: 'idle' | 'checking' | 'anonymous' } | { status: 'authenticated'; session: AccountSession } | { status: 'error'; error: Error };
let state: AccountState = { status: 'idle' };
const listeners = new Set<() => void>();
let enabled = false, revision = 0;
let restoring: Promise<void> | undefined;
let localQueue: Promise<unknown> = Promise.resolve();
export const accountMarker = 'admitflow-account-operation';
export const getAccount = () => state;
export const subscribeAccount = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
function publish(next: AccountState) {
    state = next;
    for (const listener of listeners) listener();
    window.dispatchEvent(new Event(accountChanged));
}
function boundary() { revision++; invalidateAccount(); publish({ status: 'checking' }); }
function marker(phase: 'begin' | 'end' | 'expired') {
    try { localStorage.setItem(accountMarker, JSON.stringify({ id: crypto.randomUUID(), phase })); }
    catch { /* Focus and server checks reconcile when storage is unavailable. */ }
}
function lost() { revision++; invalidateAccount(); publish({ status: 'anonymous' }); marker('expired'); }
function asError(error: unknown): Error { return error instanceof Error ? error : new ApiError(0); }

// Serialise all account cookie operations, including pre-auth CSRF, across tabs.
// A refresh mutation is never retried: a lost response requires a new login.
function locked<T>(operation: () => Promise<T>): Promise<T> {
    const run = async () => {
        if (typeof navigator !== 'undefined' && navigator.locks) {
            const waiting = new AbortController();
            const timeout = setTimeout(() => waiting.abort(), 15000);
            try {
                return await navigator.locks.request(accountMarker, { signal: waiting.signal }, async () => {
                    clearTimeout(timeout);
                    return operation();
                });
            } finally { clearTimeout(timeout); }
        }
        return operation();
    };
    const result = localQueue.then(run, run);
    localQueue = result.catch(() => {});
    return result;
}
async function mutation<T>(path: string, json: { [key: string]: string }, decode: Decoder<T>, expectedStatus: number, signal?: AbortSignal) {
    signal?.throwIfAborted();
    const csrf = await request('auth/csrf', csrfToken, { signal, expectedStatus: 200 });
    signal?.throwIfAborted();
    return request(`auth/${path}`, decode, { method: 'POST', json, headers: { 'X-CSRF-Token': csrf }, signal, expectedStatus });
}
async function readSession(): Promise<AccountSession | null> {
    try { return await request('auth/session', accountSession, { expectedStatus: 200 }); }
    catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error;
        if (error.code !== 'access_expired') return null;
        if (typeof navigator === 'undefined' || !navigator.locks) throw new ApiError(503, 'Для безопасного продления сессии нужен браузер с Web Locks и HTTPS. Войдите снова.');
        await mutation('refresh', {}, accountSession, 200);
        return request('auth/session', accountSession, { expectedStatus: 200 });
    }
}
export function restoreAccount(): Promise<void> {
    if (restoring) return restoring;
    restoring = (async () => {
        let observed: number;
        do {
            observed = revision;
            try {
                const session = await locked(readSession);
                if (observed === revision && enabled) publish(session ? { status: 'authenticated', session } : { status: 'anonymous' });
            } catch (error) {
                if (observed === revision && enabled) {
                    invalidateAccount();
                    if (error instanceof ApiError && error.status === 401) publish({ status: 'anonymous' });
                    else publish({ status: 'error', error: asError(error) });
                }
            }
        } while (observed !== revision && enabled);
    })().finally(() => { restoring = undefined; });
    return restoring;
}
export function enableAccount(value: boolean) {
    if (enabled === value) return;
    enabled = value;
    boundary();
    if (value) void restoreAccount();
    else publish({ status: 'idle' });
}
export function retryAccount() { boundary(); void restoreAccount(); }
async function ready() {
    if (state.status === 'idle' || state.status === 'checking') await restoreAccount();
    if (state.status === 'error') throw state.error;
    if (state.status !== 'authenticated') throw new ApiError(401, 'Войдите в аккаунт.', false, 'not_authenticated');
}
configureAccountPolicy({ ready, refresh: async () => { await restoreAccount(); await ready(); }, expired: lost });
let peerDeadline: ReturnType<typeof setTimeout> | undefined;
window.addEventListener('storage', event => {
    if (!enabled || (event.key !== accountMarker && event.key !== null)) return;
    let phase: unknown;
    try { phase = JSON.parse(event.newValue ?? 'null')?.phase; } catch { /* Reconcile unknown markers too. */ }
    clearTimeout(peerDeadline);
    boundary();
    if (phase === 'expired') publish({ status: 'anonymous' });
    else if (phase !== 'begin') void restoreAccount();
    else peerDeadline = setTimeout(() => { if (enabled) void restoreAccount(); }, 30000);
});
const revalidate = () => {
    if (!enabled || document.visibilityState === 'hidden') return;
    boundary(); void restoreAccount();
};
window.addEventListener('focus', revalidate);
window.addEventListener('pageshow', revalidate);

export async function login(email: string, password: string, signal?: AbortSignal) {
    boundary(); marker('begin');
    const observed = revision;
    try {
        const verified = await locked(async () => {
            const created = await mutation('login', { email, password }, accountSession, 200, signal);
            const current = await request('auth/session', accountSession, { expectedStatus: 200, signal });
            if (current.account.id !== created.account.id) throw new ApiError(502);
            return current;
        });
        if (observed === revision) publish({ status: 'authenticated', session: verified });
        else {
            await restoreAccount();
            if (state.status !== 'authenticated' || state.session.account.id !== verified.account.id) throw new ApiError(401, 'Состояние аккаунта изменилось. Повторите вход.', false);
        }
    } catch (error) {
        if (observed === revision) publish({ status: 'error', error: asError(error) });
        throw error;
    } finally { marker('end'); }
}
export async function logout() {
    boundary(); marker('begin');
    const observed = revision;
    try {
        await locked(() => mutation('logout', {}, noContent, 204));
        if (observed === revision) publish({ status: 'anonymous' });
        else await restoreAccount();
    } catch (error) {
        if (observed === revision) publish({ status: 'error', error: asError(error) });
        throw error;
    } finally { marker('end'); }
}
export function sendAccountEmail(kind: 'register' | 'verification/request' | 'recovery/request', email: string, password?: string, signal?: AbortSignal) {
    const json: Record<string, string> = password === undefined ? { email } : { email, password };
    return locked(() => mutation(kind, json, accepted, 202, signal));
}
export function confirmEmail(token: string, signal?: AbortSignal) { return locked(() => mutation('verification/confirm', { token }, noContent, 204, signal)); }
export async function resetPassword(token: string, password: string, signal?: AbortSignal) {
    boundary(); marker('begin');
    try { await locked(() => mutation('recovery/confirm', { token, password }, noContent, 204, signal)); }
    finally { marker('end'); await restoreAccount(); }
}
