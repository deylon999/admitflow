import { expect, it } from 'vitest';
import {
  clearDraft,
  DRAFT_KEY,
  DRAFT_TTL,
  MAX_DRAFT_BYTES,
  readDraft,
  storeDraft,
} from '@/features/edit-manual-direction';
import type { DraftPayload } from '@/features/edit-manual-direction';

const scope = 'a'.repeat(64),
  now = Date.parse('2026-11-01T12:00:00Z'),
  deadline = '2026-12-01T12:00:00Z';
const payload: DraftPayload = {
  watchId: null,
  baseSnapshotId: null,
  intent: null,
  draft: {
    university: '🎓',
    title: '',
    sourceUrl: '',
    values: { rank: '', seats: '20', excluded: 0, noConsent: '1e' },
  },
};
function memory() {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
    removeItem: (key: string) => {
      data.delete(key);
    },
  };
}
it('preserves incomplete input within one bounded namespace and original TTL', () => {
  const storage = memory();
  const saved = storeDraft(scope, deadline, payload, now, storage)!;
  expect(saved.expiresAt).toBe(now + DRAFT_TTL);
  expect(readDraft(scope, deadline, now + 1000, storage)?.draft.values).toEqual({
    rank: '',
    seats: '20',
    excluded: '0',
    noConsent: '1e',
  });
  expect(
    storeDraft(
      scope,
      deadline,
      { ...payload, draft: { ...payload.draft, title: 'replacement' } },
      now,
      storage,
    ),
  ).not.toBeNull();
  expect(readDraft(scope, deadline, now, storage)?.draft.title).toBe('replacement');
  expect(clearDraft(storage)).toBe(true);
  expect(readDraft(scope, deadline, now, storage)).toBeNull();
});
it('rejects another owner, expiry, unsupported versions and corrupt state', () => {
  for (const change of [
    (x: object) => ({ ...x, scope: 'b'.repeat(64) }),
    (x: object) => ({ ...x, expiresAt: now }),
    (x: object) => ({ ...x, version: 2 }),
    (x: object) => ({ ...x, expiresAt: now + DRAFT_TTL + 1 }),
    (x: object) => ({ ...x, watchId: 'orphan-edit' }),
  ]) {
    const storage = memory();
    const saved = storeDraft(scope, deadline, payload, now, storage)!;
    storage.setItem(DRAFT_KEY, JSON.stringify(change(saved)));
    expect(readDraft(scope, deadline, now, storage)).toBeNull();
    expect(storage.getItem(DRAFT_KEY)).toBeNull();
  }
  const storage = memory();
  storage.setItem(DRAFT_KEY, '{broken');
  expect(readDraft(scope, deadline, now, storage)).toBeNull();
});
it('bounds bytes, validates retry intent and handles storage denial without throwing', () => {
  const storage = memory();
  storage.setItem(DRAFT_KEY, 'x'.repeat(MAX_DRAFT_BYTES + 1));
  expect(readDraft(scope, deadline, now, storage)).toBeNull();
  expect(
    storeDraft(
      scope,
      deadline,
      { ...payload, intent: { key: 'invalid', fingerprint: 'x' } },
      now,
      storage,
    ),
  ).toBeNull();
  const denied = {
    getItem() {
      throw new Error();
    },
    setItem() {
      throw new Error();
    },
    removeItem() {
      throw new Error();
    },
  };
  expect(storeDraft(scope, deadline, payload, now, denied)).toBeNull();
  expect(readDraft(scope, deadline, now, denied)).toBeNull();
  expect(clearDraft(denied)).toBe(false);
});
it('never extends recovery beyond session deadline or by reading it', () => {
  const storage = memory(),
    soon = new Date(now + 60_000).toISOString();
  expect(storeDraft(scope, soon, payload, now, storage)?.expiresAt).toBe(now + 60_000);
  expect(readDraft(scope, soon, now + 59_999, storage)?.expiresAt).toBe(now + 60_000);
  expect(readDraft(scope, soon, now + 60_000, storage)).toBeNull();
});
