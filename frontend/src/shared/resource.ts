import { useEffect, useState } from 'react';
import { ApiError, request, type Decoder } from './api';
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
        setState(old => ({ key: path, data: old.key === path ? old.data : undefined, loading: true }));
        request(path, decode, { signal: controller.signal }).then(data => {
            if (active)
                setState({ key: path, data, loading: false });
        }, error => {
            if (active)
                setState(old => ({ key: path, data: old.key === path && !(error instanceof ApiError && error.status === 401) ? old.data : undefined, error, loading: false }));
        });
        return () => {
            active = false;
            controller.abort();
        };
    }, [path, decode, attempt]);
    useEffect(() => {
        const clear = () => {
            setState({ key: path, loading: true });
            setAttempt(n => n + 1);
        };
        const storage = (e: StorageEvent) => {
            if (e.key === 'admitflow-session-change')
                clear();
        };
        const expired = () => {
            if (!path.startsWith('catalog/'))
                setState({ key: path, loading: false, error: new ApiError(401) });
        };
        window.addEventListener('storage', storage);
        window.addEventListener('admitflow-session-expired', expired);
        return () => {
            window.removeEventListener('storage', storage);
            window.removeEventListener('admitflow-session-expired', expired);
        };
    }, [path]);
    return { ...(state.key === path ? state : { key: path, loading: true }), retry: () => setAttempt(n => n + 1) };
}
