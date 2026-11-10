import { ApiError, request } from '../shared/api';
import { decodeCatalog } from './decode';
export { ApiError as CatalogError };
export function getCatalog<T>(path: string, signal: AbortSignal): Promise<T> { return request(`catalog/${path}`, value => decodeCatalog(path, value) as T, { signal }); }
