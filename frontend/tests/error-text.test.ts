import { afterEach, expect, it, vi } from 'vitest';
import { request, requestErrorText, InvalidResponseError, RequestTimeoutError } from '@/shared/api';

afterEach(() => vi.unstubAllGlobals());

it('does not display internal server details as user instructions', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'database_pool private_debug' }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }),
    ),
  );
  const error = await request('/example', {}, 'public').catch((failure: unknown) => failure);
  expect(requestErrorText(error)).toBe(
    'Сервис временно недоступен. Попробуйте ещё раз чуть позже.',
  );
});

it('distinguishes invalid data and timeout from an empty result', () => {
  expect(requestErrorText(new InvalidResponseError())).toContain(
    'Не удалось проверить полученные данные',
  );
  expect(requestErrorText(new RequestTimeoutError())).toContain('слишком много времени');
});

it('retains the existing network recovery message', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
  const error = await request('/example', {}, 'public').catch((failure: unknown) => failure);
  expect(requestErrorText(error)).toContain('Проверьте соединение');
  expect(requestErrorText(error)).not.toContain('Failed to fetch');
});
