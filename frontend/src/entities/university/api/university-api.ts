import { request } from '@/shared/api';
import { parseCatalog } from '../model/contracts';

export const universityApi = {
  universities: async (query: string, signal?: AbortSignal, offset = 0) =>
    parseCatalog(
      await request(
        `/universities?q=${encodeURIComponent(query)}&offset=${offset}`,
        { signal },
        'public',
      ),
    ),
};
