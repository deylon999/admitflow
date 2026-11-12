import { useEffect, useMemo, useState } from 'react';
import { navigate } from '../app/navigation';
import { useResource } from '../shared/resource';
import { invalid, object, type Decoder } from '../shared/api';
export function useCatalog<T>(path: string, decode: Decoder<T>) {
    const scoped = useMemo(() => (value: unknown) => {
        const data = decode(value);
        const result = object(data);
        const target = new URL(path, 'https://catalog.invalid/');
        const id = target.pathname.split('/')[2];
        if (id && result.id !== decodeURIComponent(id)) invalid();
        if (Array.isArray(result.items)) {
            const year = target.searchParams.get('year'), universityId = target.searchParams.get('universityId');
            if (result.items.some(item => (year && object(item).year !== Number(year)) || (universityId && object(item).universityId !== universityId))) invalid();
            if (result.nextOffset !== null && typeof result.nextOffset === 'number' && result.nextOffset <= Number(target.searchParams.get('offset') ?? 0)) invalid();
        }
        return data;
    }, [path, decode]);
    return useResource<T>(`catalog/${path}`, scoped);
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
