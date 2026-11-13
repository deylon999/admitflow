import { useEffect, useState } from 'react';
import { accountChanged, accountInvalidated, apiScope, ApiError, request, sessionBound, sessionChanged, sessionExpired, type Decoder } from './api';
type State<T> = {
    key: string;
    data?: T;
    error?: Error;
    loading: boolean;
};
export function useResource<T>(path: string, decode: Decoder<T>) {
    const [attempt, setAttempt] = useState(0);
    const [state, setState] = useState<State<T>>({ key: path, loading: true });
    useEffect(() => {
        let active = true;
        const controller = new AbortController();
        const changed = () => {
            if (!sessionBound(path)) return;
            active = false;
            controller.abort();
            setState({ key: path, loading: true });
            setAttempt(n => n + 1);
        };
        const expired = () => {
            if (!sessionBound(path)) return;
            active = false;
            controller.abort();
            setState({ key: path, loading: false, error: new ApiError(401) });
        };
        const accountReset = () => {
            if (apiScope(path) !== 'account') return;
            active = false;
            controller.abort();
            setState({ key: path, loading: false, error: new ApiError(401, 'Состояние аккаунта изменилось.', false) });
        };
        const accountReady = () => {
            if (apiScope(path) === 'account') setAttempt(n => n + 1);
        };
        window.addEventListener(accountInvalidated, accountReset);
        window.addEventListener(accountChanged, accountReady);
        window.addEventListener(sessionChanged, changed);
        window.addEventListener(sessionExpired, expired);
        setState(old => ({ key: path, data: old.key === path ? old.data : undefined, loading: true }));
        request(path, decode, { signal: controller.signal }).then(data => {
            if (active)
                setState({ key: path, data, loading: false });
        }, error => {
            if (active)
                setState(old => ({ key: path, data: old.key === path && !(error instanceof ApiError && [401, 403, 404, 410].includes(error.status)) ? old.data : undefined, error, loading: false }));
        });
        return () => {
            active = false;
            controller.abort();
            window.removeEventListener(accountInvalidated, accountReset);
            window.removeEventListener(accountChanged, accountReady);
            window.removeEventListener(sessionChanged, changed);
            window.removeEventListener(sessionExpired, expired);
        };
    }, [path, decode, attempt]);
    return { ...(state.key === path ? state : { key: path, loading: true }), retry: () => setAttempt(n => n + 1) };
}
