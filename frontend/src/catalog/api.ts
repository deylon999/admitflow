export class CatalogError extends Error {
  constructor(public status: number) {
    super(status === 404 ? 'Запись не найдена' : 'Не удалось загрузить данные');
  }
}

export async function getCatalog<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`/api/v1/catalog/${path}`, {
    signal,
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new CatalogError(response.status);
  // A missing reverse proxy must not interpret the SPA index as catalog data.
  if (!response.headers.get('content-type')?.includes('application/json')) throw new CatalogError(502);
  return response.json() as Promise<T>;
}
