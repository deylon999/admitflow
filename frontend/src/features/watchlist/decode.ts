import { array, bool, count, date, identifier, invalid, nullable, object, oneOf, positive, text, url, year } from '../../shared/api';

// Construct typed views from validated fields; extra official metadata is retained.
export function subscriptions(value: unknown) {
    return array(value, v => {
        const p = object(v), g = object(p.group);
        return { ...p, id: identifier(p.id), createdAt: date(p.createdAt), group: { ...g, id: identifier(g.id), title: text(g.title), universityName: text(g.universityName), year: year(g.year), seats: nullable(g.seats, count), sourceUrl: nullable(g.sourceUrl, url), dataKind: nullable(g.dataKind, v => oneOf(v, ['live', 'archive'])) } };
    });
}
export type Subscription = ReturnType<typeof subscriptions>[number];
export function events(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const x = object(v);
        return { ...x, id: identifier(x.id), title: text(x.title), createdAt: date(x.createdAt) };
    });
    const total = count(p.total), unreadCount = count(p.unreadCount);
    if (items.length > total || unreadCount > total) invalid();
    return { ...p, items, total, unreadCount, nextCursor: nullable(p.nextCursor, identifier) };
}
export type Events = ReturnType<typeof events>;

export function groups(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const g = object(v);
        return { ...g, id: identifier(g.id), title: text(g.title), universityName: text(g.universityName), year: year(g.year), sourceId: nullable(g.sourceId, identifier), lookupAvailable: bool(g.lookupAvailable) };
    });
    const total = count(p.total);
    if (items.length > total) invalid();
    return { ...p, items, total, nextCursor: nullable(p.nextCursor, identifier) };
}
export type Group = ReturnType<typeof groups>['items'][number];
export function lookup(value: unknown) {
    const p = object(value), g = object(p.group);
    const title = text(g.title), campaignYear = year(g.year);
    if (!bool(p.found)) {
        if (p.candidate !== null || p.confirmationToken !== null || p.expiresAt !== null) invalid();
        return null;
    }
    const c = object(p.candidate);
    return { token: identifier(p.confirmationToken), rank: positive(c.officialRank), title, year: campaignYear, expiresAt: date(p.expiresAt) };
}
export function saved(value: unknown) {
    const p = object(value);
    date(p.createdAt);
    return identifier(p.id);
}
