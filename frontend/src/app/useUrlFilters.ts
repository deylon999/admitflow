import { useEffect, useState } from 'react';
import { navigate } from './navigation';

export function useUrlFilters() {
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
