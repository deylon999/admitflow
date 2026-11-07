import { InvalidResponseError } from './errors';
import { object, timestamp } from './validation';

export type SessionInfo = { expiresAt: string; draftScope?: string };

export const sessionAccessKey = ['session-access'] as const;
export type SessionAccess = 'active' | 'expired' | 'changed';

export function parseSession(value: unknown): SessionInfo {
  const row = object(value);
  const expiresAt = timestamp(row.expiresAt);
  if (row.draftScope === undefined) return { expiresAt }; // Older API: local recovery stays disabled.
  if (typeof row.draftScope !== 'string' || !/^[a-f0-9]{64}$/.test(row.draftScope))
    throw new InvalidResponseError();
  return { expiresAt, draftScope: row.draftScope };
}
