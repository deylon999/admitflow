import { useEffect, useMemo, useState } from 'react';
import { navigate } from '../app/navigation';
import { useResource } from '../shared/resource';
import { decodeCatalog } from './decode';
export function useCatalog<T>(path: string) {
    const decode = useMemo(() => (value: unknown) => decodeCatalog(path, value) as T, [path]);
    return useResource<T>(`catalog/${path}`, decode);
}
export function useCatalogFilters() {
    const [search, setSearch] = useState(() => window.location.search);
    useEffect(() => {
        const update = () => setSearch(window.location.search);
        window.addEventListener('popstate', update);
        return () => window.removeEventListener('popstate', update);
    }, []);
    const params = new URLSearchParams(search);
    function update(name: string, value: string) {
        const next = new URLSearchParams(window.location.search);
        if (value)
            next.set(name, value);
        else
            next.delete(name);
        if (name !== 'offset')
            next.delete('offset');
        const query = next.toString();
        navigate(window.location.pathname + (query ? `?${query}` : ''));
    }
    return { params, update };
}
export function useDebounced(value: string) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timeout = window.setTimeout(() => setDebounced(value), 200);
        return () => window.clearTimeout(timeout);
    }, [value]);
    return debounced;
}
