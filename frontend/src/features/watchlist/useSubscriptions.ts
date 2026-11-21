import { useEffect, useRef, useState } from 'react';
import { request, sessionChanged, sessionExpired } from '../../shared/api';
import { useResource } from '../../shared/resource';
import { subscriptions } from './decode';

export function useSubscriptions() {
    const r = useResource('subscriptions', subscriptions);
    const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('');
    const pending = useRef<AbortController | null>(null);
    useEffect(() => {
        const clear = () => {
            pending.current?.abort();
            setBusy(false);
            setMessage('');
            setError('');
        };
        window.addEventListener(sessionChanged, clear);
        window.addEventListener(sessionExpired, clear);
        return () => {
            pending.current?.abort();
            window.removeEventListener(sessionChanged, clear);
            window.removeEventListener(sessionExpired, clear);
        };
    }, []);
    async function remove(key: string) {
        if (busy) return;
        if (!confirm('Удалить подписку и её историю?'))
            return;
        setBusy(true);
        const controller = new AbortController();
        pending.current = controller;
        setError('');
        setMessage('');
        try {
            await request(`subscriptions/${encodeURIComponent(key)}`, () => null, { method: 'DELETE', signal: controller.signal });
            if (controller.signal.aborted) return;
            setMessage('Подписка удалена.');
            r.retry();
        }
        catch (e) {
            if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Не удалось удалить подписку.');
        }
        finally {
            if (!controller.signal.aborted) setBusy(false);
        }
    }
    return { r, busy, message, error, remove };
}
