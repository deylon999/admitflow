import { expect, test } from '@playwright/test';
let api: typeof import('../src/shared/api');
let dto: typeof import('../src/shared/authDto');
test.beforeAll(async () => {
    Object.defineProperty(globalThis, 'window', { value: new EventTarget(), configurable: true });
    api = await import('../src/shared/api');
    dto = await import('../src/shared/authDto');
});
const session = { account: { id: 'user-a', email: 'a@example.org', emailVerified: true, passwordHash: 'secret' }, accessExpiresAt: '2026-11-13T12:15:00Z', absoluteExpiresAt: '2026-12-13T12:00:00Z', refreshToken: 'secret' };
test('explicit public/guest/auth/account scopes preserve guest ownership', () => {
    for (const path of ['catalog/programs', 'groups', 'coverage', 'sources/example/status']) expect(api.apiScope(path)).toBe('public');
    for (const path of ['session', 'subscriptions', 'competitions/example']) expect(api.apiScope(path)).toBe('guest');
    expect(api.apiScope('auth/session')).toBe('auth');
    expect(api.apiScope('account/profile')).toBe('account');
    expect(api.sessionBound('auth/login')).toBe(false);
});
test('account DTO whitelists fields and rejects malformed server proof', () => {
    expect(dto.accountSession(session)).toEqual({ account: { id: 'user-a', email: 'a@example.org', emailVerified: true }, accessExpiresAt: session.accessExpiresAt, absoluteExpiresAt: session.absoluteExpiresAt });
    for (const value of [{ ...session, account: { ...session.account, emailVerified: false } }, { ...session, accessExpiresAt: '2026-11-13' }, { ...session, absoluteExpiresAt: '2026-11-12T00:00:00Z' }]) expect(() => dto.accountSession(value)).toThrow();
});
test('account failures parse only bounded known codes and do not expire guests', async () => {
    const original = globalThis.fetch;
    let expired = 0;
    const listener = () => { expired++; };
    window.addEventListener(api.sessionExpired, listener);
    try {
        globalThis.fetch = async () => new Response(JSON.stringify({ code: 'not_authenticated', detail: 'PRIVATE EMAIL PASSWORD' }), { status: 401, headers: { 'Content-Type': 'application/json' } });
        await expect(api.request('auth/login', value => value)).rejects.toMatchObject({ status: 401, requiresSession: false, code: 'not_authenticated' });
        globalThis.fetch = async () => new Response(JSON.stringify({ code: 'PRIVATE', detail: 'PRIVATE' }), { status: 429, headers: { 'Retry-After': '27' } });
        await expect(api.request('auth/recovery/request', value => value)).rejects.toMatchObject({ status: 429, retryAfter: 27, code: undefined });
        expect(expired).toBe(0);
    } finally { globalThis.fetch = original; window.removeEventListener(api.sessionExpired, listener); }
});
test('account boundary rejects a response whose body completed after owner change', async () => {
    const original = globalThis.fetch;
    let release!: () => void;
    const waiting = new Promise<void>(done => { release = done; });
    globalThis.fetch = async () => ({ ok: true, status: 200, headers: new Headers({ 'Content-Type': 'application/json' }), json: async () => { await waiting; return session; } }) as Response;
    try {
        const result = api.request('auth/session', dto.accountSession);
        await Promise.resolve();
        api.invalidateAccount(); release();
        await expect(result).rejects.toMatchObject({ status: 401, code: 'account_changed', requiresSession: false });
    } finally { globalThis.fetch = original; }
});

test('only account access_expired retries once; public, guest and login 401 never refresh', async () => {
    const original = globalThis.fetch;
    let refreshes = 0, expired = 0;
    api.configureAccountPolicy({ ready: async () => {}, refresh: async () => { refreshes++; }, expired: () => { expired++; } });
    globalThis.fetch = async () => new Response(JSON.stringify({ code: 'access_expired' }), { status: 401 });
    try {
        for (const path of ['catalog/programs', 'subscriptions', 'auth/login']) await expect(api.request(path, v => v)).rejects.toMatchObject({ status: 401 });
        expect(refreshes).toBe(0);
        await expect(api.request('account/example', v => v)).rejects.toMatchObject({ status: 401 });
        expect(refreshes).toBe(1); expect(expired).toBe(1);
    } finally { globalThis.fetch = original; }
});
test('account scope rejects success when owner changes while waiting for policy', async () => {
    let release!: () => void, calls = 0;
    const original = globalThis.fetch;
    const waiting = new Promise<void>(done => { release = done; });
    api.configureAccountPolicy({ ready: () => waiting, refresh: async () => {}, expired: () => {} });
    globalThis.fetch = async () => { calls++; return new Response('{}'); };
    try {
        const result = api.request('account/example', v => v);
        api.invalidateAccount(); release();
        await expect(result).rejects.toMatchObject({ code: 'account_changed' });
        expect(calls).toBe(0);
    } finally { globalThis.fetch = original; }
});
test('owner change during retry cannot expire the newly selected account', async () => {
    let calls = 0, expired = 0;
    const original = globalThis.fetch;
    api.configureAccountPolicy({ ready: async () => {}, refresh: async () => {}, expired: () => { expired++; } });
    globalThis.fetch = async () => {
        calls++;
        if (calls === 2) api.invalidateAccount();
        return new Response(JSON.stringify({ code: 'access_expired' }), { status: 401 });
    };
    try {
        await expect(api.request('account/example', v => v)).rejects.toMatchObject({ code: 'account_changed' });
        expect(expired).toBe(0);
    } finally { globalThis.fetch = original; }
});
