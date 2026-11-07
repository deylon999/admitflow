import { useEffect, useState } from 'react';
import { navigate } from '../app/navigation';
import { CatalogError, getCatalog } from './api';

type Resource<T> = { key: string; data?: T; error?: Error; loading: boolean };

export function useCatalog<T>(path: string) {
  const [attempt, setAttempt] = useState(0);
  const [resource, setResource] = useState<Resource<T>>({ key: path, loading: true });
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15_000);
    setResource(previous => ({ key: path, data: previous.data, loading: true }));
    getCatalog<T>(path, controller.signal).then(
      data => { if (active) setResource({ key: path, data, loading: false }); },
      error => {
        if (active) setResource({ key: path, loading: false, error: error instanceof CatalogError ? error : new CatalogError(503) });
      },
    ).finally(() => window.clearTimeout(timeout));
    return () => { active = false; controller.abort(); window.clearTimeout(timeout); };
  }, [path, attempt]);
  return {
    ...(resource.key === path ? resource : { key: path, data: resource.data, loading: true }),
    retry: () => setAttempt(value => value + 1),
  };
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
    if (value) next.set(name, value); else next.delete(name);
    if (name !== 'offset') next.delete('offset');
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
