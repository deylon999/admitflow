import { afterEach, expect, it, vi } from 'vitest';
import { RequestTimeoutError, withRequestTimeout } from '@/shared/api';

afterEach(() => vi.useRealTimers());
it('limits a stalled response/body and aborts the underlying operation', async () => {
  vi.useFakeTimers();
  let received!: AbortSignal;
  const result = withRequestTimeout((signal) => {
    received = signal;
    return new Promise(() => {});
  });
  const assertion = expect(result).rejects.toBeInstanceOf(RequestTimeoutError);
  await vi.advanceTimersByTimeAsync(15_000);
  await assertion;
  expect(received.aborted).toBe(true);
  expect(vi.getTimerCount()).toBe(0);
});
it('supports cancellation and does not retry writes', async () => {
  const controller = new AbortController();
  const operation = vi.fn(() => new Promise(() => {}));
  const result = withRequestTimeout(operation, controller.signal);
  const assertion = expect(result).rejects.toHaveProperty('name', 'AbortError');
  controller.abort();
  await assertion;
  expect(operation).toHaveBeenCalledTimes(1);
});
it('clears the timer after success or failure', async () => {
  vi.useFakeTimers();
  await expect(withRequestTimeout(async () => 42)).resolves.toBe(42);
  await expect(
    withRequestTimeout(async () => {
      throw new Error('offline');
    }),
  ).rejects.toThrow('offline');
  expect(vi.getTimerCount()).toBe(0);
});
