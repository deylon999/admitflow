import type { DirectionDraft } from './direction';
import { parseStrictJson } from './json';

export const DRAFT_KEY = 'admitflow-draft-v1';
export const DRAFT_TTL = 30 * 60_000;
export const MAX_DRAFT_BYTES = 16 * 1024;
type StorageAccess = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;
export type SaveIntent = { fingerprint: string; key: string };
export type DraftPayload = { draft: DirectionDraft; watchId: string | null; baseSnapshotId: string | null; intent: SaveIntent | null };
export type StoredDraft = DraftPayload & { version: 1; scope: string; updatedAt: number; expiresAt: number };

function row(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid draft');
  return value as Record<string, unknown>;
}
function text(value: unknown, max: number, empty = true): value is string {
  return typeof value === 'string' && (empty || Boolean(value.trim())) && Array.from(value).length <= max && !/[\u0000-\u001f\u007f]/.test(value);
}
function validate(value: unknown, scope: string, deadline: string, now: number): StoredDraft {
  const data = row(value);
  const draft = row(data.draft);
  const values = row(draft.values);
  if (data.version !== 1 || !/^[a-f0-9]{64}$/.test(scope) || data.scope !== scope
    || !Number.isSafeInteger(data.updatedAt) || !Number.isSafeInteger(data.expiresAt)
    || (data.updatedAt as number) > now + 60_000 || (data.expiresAt as number) <= now
    || (data.expiresAt as number) <= (data.updatedAt as number)
    || (data.expiresAt as number) > (data.updatedAt as number) + DRAFT_TTL
    || !Number.isFinite(Date.parse(deadline)) || (data.expiresAt as number) > Date.parse(deadline)
    || !text(draft.university, 160) || !text(draft.title, 200) || !text(draft.sourceUrl, 2048)
    || !['rank', 'seats', 'excluded', 'noConsent'].every(key => text(values[key], 30))
    || !(data.watchId === null && data.baseSnapshotId === null || text(data.watchId, 100, false) && text(data.baseSnapshotId, 100, false))) throw new Error('Invalid draft');
  let intent: SaveIntent | null = null;
  if (data.intent !== null) {
    const candidate = row(data.intent);
    if (typeof candidate.key !== 'string' || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(candidate.key)
      || !text(candidate.fingerprint, 10_000, false)) throw new Error('Invalid draft');
    intent = { key: candidate.key, fingerprint: candidate.fingerprint };
  }
  return { version: 1, scope, updatedAt: data.updatedAt as number, expiresAt: data.expiresAt as number,
    watchId: data.watchId as string | null, baseSnapshotId: data.baseSnapshotId as string | null, intent,
    draft: { university: draft.university, title: draft.title, sourceUrl: draft.sourceUrl,
      values: { rank: values.rank as string, seats: values.seats as string, excluded: values.excluded as string, noConsent: values.noConsent as string } } };
}

export function clearDraft(storage?: StorageAccess): boolean {
  try { (storage ?? sessionStorage).removeItem(DRAFT_KEY); return true; } catch { return false; }
}
export function readDraft(scope: string, deadline: string, now = Date.now(), storage?: StorageAccess): StoredDraft | null {
  try {
    const source = (storage ?? sessionStorage).getItem(DRAFT_KEY);
    if (source === null) return null;
    if (new TextEncoder().encode(source).byteLength > MAX_DRAFT_BYTES) throw new Error('Oversized draft');
    return validate(parseStrictJson(source), scope, deadline, now);
  } catch { clearDraft(storage); return null; }
}
export function storeDraft(scope: string, deadline: string, payload: DraftPayload, now = Date.now(), storage?: StorageAccess): StoredDraft | null {
  try {
    const normalized = { ...payload, draft: { ...payload.draft, values: Object.fromEntries(Object.entries(payload.draft.values).map(([key, value]) => [key, String(value)])) } };
    const record = validate({ ...normalized, version: 1, scope, updatedAt: now, expiresAt: Math.min(now + DRAFT_TTL, Date.parse(deadline)) }, scope, deadline, now);
    const source = JSON.stringify(record);
    if (new TextEncoder().encode(source).byteLength > MAX_DRAFT_BYTES) throw new Error('Oversized draft');
    (storage ?? sessionStorage).setItem(DRAFT_KEY, source);
    return record;
  } catch { return null; }
}
