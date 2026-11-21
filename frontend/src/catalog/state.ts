import { useEffect, useMemo, useState } from 'react';
import { useResource } from '../shared/resource';
import { invalid, object, type Decoder } from '../shared/api';

export { useUrlFilters as useCatalogFilters } from '../app/useUrlFilters';

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

export function useDebounced(value: string) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timeout = window.setTimeout(() => setDebounced(value), 200);
        return () => window.clearTimeout(timeout);
    }, [value]);
    return debounced;
}
