import { date, identifier, invalid, object, text } from './api';

export type AccountSession = {
    account: { id: string; email: string; emailVerified: true };
    accessExpiresAt: string;
    absoluteExpiresAt: string;
};
export function accountSession(value: unknown): AccountSession {
    const v = object(value), a = object(v.account);
    if (a.emailVerified !== true) invalid();
    const accessExpiresAt = date(v.accessExpiresAt), absoluteExpiresAt = date(v.absoluteExpiresAt);
    if (!accessExpiresAt.includes('T') || !absoluteExpiresAt.includes('T') || Date.parse(accessExpiresAt) > Date.parse(absoluteExpiresAt)) invalid();
    const email = text(a.email);
    if (email.length > 320 || !/^[^\s@]+@[^\s@]+$/.test(email)) invalid();
    return { account: { id: identifier(a.id), email, emailVerified: true }, accessExpiresAt, absoluteExpiresAt };
}
export function csrfToken(value: unknown): string {
    const token = text(object(value).csrfToken);
    return /^[A-Za-z0-9_-]{43}$/.test(token) ? token : invalid();
}
export function accepted(value: unknown): null { text(object(value).message); return null; }
export function noContent(value: unknown): null { return value === null ? null : invalid(); }
