import { InvalidResponseError } from './errors';
import { instantMicros } from '@/shared/lib/time';

export function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new InvalidResponseError();
  return value as Record<string, unknown>;
}
export function text(value: unknown, max = 2048): string {
  if (
    typeof value !== 'string' ||
    !value.trim() ||
    Array.from(value).length > max ||
    /[\u0000-\u001f\u007f]/.test(value)
  )
    throw new InvalidResponseError();
  return value;
}
export function timestamp(value: unknown): string {
  const result = text(value, 50);
  try {
    instantMicros(result);
  } catch {
    throw new InvalidResponseError();
  }
  return result;
}
export function url(value: unknown): string {
  const result = text(value);
  try {
    const parsed = new URL(result);
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password)
      throw new Error();
  } catch {
    throw new InvalidResponseError();
  }
  return result;
}
export function array<T>(value: unknown, parse: (item: unknown) => T, max: number): T[] {
  if (!Array.isArray(value) || value.length > max) throw new InvalidResponseError();
  return value.map(parse);
}

export function integer(v: unknown, min = 0, max = 1_000_000): number {
  if (typeof v !== 'number' || !Number.isSafeInteger(v) || v < min || v > max)
    throw new InvalidResponseError();
  return v;
}

export function boundedText(value: unknown, max = 300): string {
  return text(value, max);
}
