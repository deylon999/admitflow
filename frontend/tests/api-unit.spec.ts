import { test, expect } from '@playwright/test';
import { mock } from 'node:test';

// Isolated transport/decoder tests, no production endpoint or browser fixtures.
test.describe.configure({ mode: 'default' });
const originalFetch = globalThis.fetch;
let api: typeof import('../src/shared/api');
let dto: typeof import('../src/shared/dto');
let catalog: typeof import('../src/catalog/decode');
test.beforeAll(async () => {
    Object.defineProperty(globalThis, 'window', { configurable: true, value: new EventTarget() });
    api = await import('../src/shared/api');
    dto = await import('../src/shared/dto');
    catalog = await import('../src/catalog/decode');
});
test.afterEach(() => { globalThis.fetch = originalFetch; mock.timers.reset(); });
test.afterAll(() => { Reflect.deleteProperty(globalThis, 'window'); });

for (const status of [400, 401, 403, 404, 409, 410, 422, 429, 500, 503]) {
    test(`transport HTTP ${status} is controlled and never leaks detail`, async () => {
        let calls = 0;
        globalThis.fetch = async () => { calls++; return Response.json({ detail: 'secret stack trace' }, { status }); };
        await expect(api.request('subscriptions', dto.subscriptions)).rejects.toMatchObject({ status });
        expect(calls).toBe(1);
        expect(new api.ApiError(status).message).not.toContain('secret');
    });
}
for (const [name, response] of [
    ['invalid JSON', () => new Response('{', { headers: { 'Content-Type': 'application/json' } })],
    ['HTML', () => new Response('<html>', { headers: { 'Content-Type': 'text/html' } })],
    ['misleading Content-Type', () => new Response('[]', { headers: { 'Content-Type': 'application/json-broken' } })],
    ['wrong DTO', () => Response.json({ items: [] })],
] as const) test(`transport rejects ${name}`, async () => {
    globalThis.fetch = async () => response();
    await expect(api.request('subscriptions', dto.subscriptions)).rejects.toMatchObject({ status: 502 });
});
test('Headers and tuple headers survive, typed JSON is serialized; unsafe JSON is rejected', async () => {
    for (const headers of [new Headers({ 'X-Custom': 'ok' }), [['X-Custom', 'ok']] as [string, string][]]) {
        globalThis.fetch = async (_path, options) => {
            const actual = new Headers(options?.headers);
            expect(actual.get('X-Custom')).toBe('ok');
            expect(actual.get('Content-Type')).toBe('application/json');
            expect(options?.credentials).toBe('same-origin');
            expect(options?.body).toBe('{"publicCode":"a-1"}');
            return Response.json([]);
        };
        await api.request('test', dto.subscriptions, { headers, method: 'POST', json: { publicCode: 'a-1' } });
    }
    let calls = 0;
    globalThis.fetch = async () => { calls++; return Response.json([]); };
    await expect(api.request('test', dto.subscriptions, { method: 'POST', json: { score: Infinity } })).rejects.toMatchObject({ status: 400 });
    expect(calls).toBe(0);
});
test('caller cancellation before fetch and during body stays AbortError', async () => {
    let calls = 0;
    globalThis.fetch = async () => { calls++; return Response.json([]); };
    const controller = new AbortController(); controller.abort();
    await expect(api.request('subscriptions', dto.subscriptions, { signal: controller.signal })).rejects.toMatchObject({ name: 'AbortError' });
    expect(calls).toBe(0);
    const during = new AbortController();
    globalThis.fetch = async () => {
        const response = Response.json([]);
        response.json = async () => { during.abort(); return []; };
        return response;
    };
    await expect(api.request('subscriptions', dto.subscriptions, { signal: during.signal })).rejects.toMatchObject({ name: 'AbortError' });
});
test('timeout while waiting for body is controlled, no automatic retry', async () => {
    mock.timers.enable({ apis: ['setTimeout'] });
    globalThis.fetch = async (_path, options) => {
        const response = Response.json([]);
        response.json = () => new Promise((_resolve, reject) => {
            options?.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
        });
        return response;
    };
    const pending = api.request('subscriptions', dto.subscriptions);
    const assertion = expect(pending).rejects.toMatchObject({ status: 0, message: expect.stringContaining('слишком много времени') });
    await Promise.resolve();
    mock.timers.tick(15000);
    await assertion;
});
test('old owner body arriving after session change never returns private data', async () => {
    let release: (value: unknown) => void = () => {};
    globalThis.fetch = async () => {
        const response = Response.json([]);
        response.json = () => new Promise(resolve => { release = resolve; });
        return response;
    };
    const pending = api.request('subscriptions', dto.subscriptions);
    const assertion = expect(pending).rejects.toMatchObject({ status: 401 });
    await Promise.resolve();
    window.dispatchEvent(Object.assign(new Event('storage'), { key: api.sessionChanged }));
    release([]);
    await assertion;
});
test('public requests survive session changes, network error is distinct from DTO error', async () => {
    globalThis.fetch = async () => { window.dispatchEvent(Object.assign(new Event('storage'), { key: api.sessionChanged })); return Response.json([]); };
    await expect(api.request('groups', dto.subscriptions)).resolves.toEqual([]);
    globalThis.fetch = async () => { throw new TypeError('network'); };
    await expect(api.request('groups', dto.subscriptions)).rejects.toMatchObject({ status: 0 });
    globalThis.fetch = async () => Response.json([]);
    await expect(api.request('groups', () => { throw new TypeError('decoder'); })).rejects.toMatchObject({ status: 502 });
});
for (const value of ['2026-02-30', '2025-02-29T10:00:00Z', '2026-11-01T24:00:00Z', '12', '', '2026-11-01T12:00:00']) test(`reject invalid date ${value}`, () => { expect(() => api.date(value)).toThrow(api.ApiError); });
test('valid ISO dates, timezone and null facts survive without invented defaults', () => {
    for (const value of ['2024-02-29', '2026-11-01T10:00:00.123456+03:00', '2026-11-01T10:00:00Z']) expect(api.date(value)).toBe(value);
    const record = { id: 'sub', createdAt: '2026-11-01T00:00:00Z', group: { id: 'group', title: 'A', universityName: 'B', year: 2026, seats: null, sourceUrl: null, dataKind: null } };
    expect(dto.subscriptions([record])[0].group.seats).toBeNull();
    for (const bad of ['', ' ', 'bad/id', 'bad\u0000id']) expect(() => dto.subscriptions([{ ...record, id: bad }])).toThrow();
    for (const bad of [undefined, -1, 1.5, NaN, Infinity]) expect(() => dto.subscriptions([{ ...record, group: { ...record.group, seats: bad } }])).toThrow();
    expect(() => dto.subscriptions([{ ...record, group: { ...record.group, year: 0 } }])).toThrow();
    expect(() => dto.lookup({ found: true, candidate: { officialRank: 0 }, group: { title: 'A', year: 2026 }, confirmationToken: 'token', expiresAt: record.createdAt })).toThrow();
    expect(() => dto.competitionSummary({ total: 0, byConsent: {}, byParticipation: {} })).toThrow();
});
test('catalog decoder returns concrete typed DTO and retains official provenance', () => {
    const provenance = { url: 'https://example.org', verifiedAt: '2026-11-01T00:00:00Z', sourceUpdatedAt: null, kind: 'archive', edition: 2026, originalSha256: 'a'.repeat(64) };
    const record = { id: 'university', name: 'A', legalName: 'A', region: 'B', isBranch: false, officialUrl: null, knownProgramCount: 0, years: [2026], provenance, accreditation: null };
    expect(catalog.university(record).provenance.originalSha256).toBe(provenance.originalSha256);
    expect(() => catalog.university({ ...record, provenance: { ...provenance, originalSha256: 'bad' } })).toThrow();
    expect(() => catalog.university({ ...record, years: [0] })).toThrow();
});

test('demo links merge query and hash while explicit exit and real catalog remain live', async () => {
    const navigation = await import('../src/app/navigation');
    Object.defineProperty(window, 'location', { configurable: true, value: new URL('https://example.org/app?mode=demo') });
    expect(navigation.routeHref('/app/forecast?from=compare#form')).toBe('/app/forecast?from=compare&mode=demo#form');
    expect(navigation.routeHref('/app/forecast?mode=live&from=compare')).toBe('/app/forecast?mode=live&from=compare');
    expect(navigation.routeHref('/programs?year=2026')).toBe('/programs?year=2026');
    expect(navigation.routeHref('//elsewhere.org/app')).toBe('//elsewhere.org/app');
    for (const bad of ['%', '%E0%A4%A', 'bad%2Fid', 'bad%00id']) expect(navigation.decodeRouteId(bad)).toBeNull();
    expect(navigation.decodeRouteId('%73gu-saratov')).toBe('sgu-saratov');
});
