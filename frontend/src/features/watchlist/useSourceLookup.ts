import { useEffect, useRef, useState } from 'react';
import { ApiError, request, sessionChanged, sessionExpired } from '../../shared/api';
import { useResource } from '../../shared/resource';
import { groups, lookup, saved, type Group } from './decode';

export function useSourceLookup() {
    const [q, setQ] = useState(''), [cursor, setCursor] = useState(''), [group, setGroup] = useState<Group | null>(null), [code, setCode] = useState(''), [result, setResult] = useState<ReturnType<typeof lookup>>(), [busy, setBusy] = useState(false), [error, setError] = useState<Error>(), [success, setSuccess] = useState('');
    const pending = useRef<AbortController | null>(null);
    const r = useResource('groups?' + new URLSearchParams({ q, after: cursor, limit: '20' }), groups);
    useEffect(() => {
        const clear = () => {
            pending.current?.abort();
            setBusy(false);
            setResult(undefined);
            setCode('');
            setSuccess('');
            setError(undefined);
        };
        // Keep a 401 visible until the user explicitly starts a guest session.
        const expired = () => { clear(); setError(new ApiError(401)); };
        window.addEventListener(sessionExpired, expired);
        window.addEventListener(sessionChanged, clear);
        return () => {
            pending.current?.abort();
            window.removeEventListener(sessionExpired, expired);
            window.removeEventListener(sessionChanged, clear);
        };
    }, []);
    async function submit() {
        if (pending.current && !pending.current.signal.aborted && busy) return;
        const controller = new AbortController();
        pending.current = controller;
        setBusy(true);
        setError(undefined);
        setSuccess('');
        try {
            if (result) {
                const id = await request('subscriptions', saved, { method: 'POST', json: { confirmationToken: result.token }, signal: controller.signal });
                if (controller.signal.aborted) return;
                setSuccess(id);
                setResult(undefined);
                setCode('');
            }
            else if (group?.sourceId) {
                const found = await request(`sources/${encodeURIComponent(group.sourceId)}/lookup`, lookup, { method: 'POST', json: { publicCode: code }, signal: controller.signal });
                if (!controller.signal.aborted) setResult(found);
            }
        }
        catch (e) {
            if (!controller.signal.aborted) setError(e instanceof Error ? e : new Error('Не удалось выполнить запрос.'));
        }
        finally {
            if (!controller.signal.aborted) setBusy(false);
        }
    }
    return { q, setQ, cursor, setCursor, group, setGroup, code, setCode, result, setResult, busy, error, setError, success, setSuccess, r, submit };
}
