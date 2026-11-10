import { array, count, date, invalid, object, text, url } from './api';
export type Subscription = {
    id: string;
    createdAt: string;
    group: {
        id: string;
        title: string;
        universityName: string;
        year: number;
        seats: number | null;
        sourceUrl: string | null;
        dataKind: string | null;
    };
};
export function subscriptions(value: unknown): Subscription[] {
    return array(value, v => {
        const p = object(v), g = object(p.group);
        text(p.id);
        date(p.createdAt);
        for (const k of ['id', 'title', 'universityName'])
            text(g[k]);
        count(g.year);
        if (g.seats !== null)
            count(g.seats);
        if (g.sourceUrl !== null)
            url(g.sourceUrl);
        if (g.dataKind !== null && !['live', 'archive'].includes(text(g.dataKind)))
            invalid();
        return p as unknown as Subscription;
    });
}
export type Events = {
    items: {
        id: string;
        title: string;
        createdAt: string;
    }[];
    total: number;
    nextCursor: string | null;
};
export function events(value: unknown): Events {
    const p = object(value);
    array(p.items, v => {
        const x = object(v);
        text(x.id);
        text(x.title);
        date(x.createdAt);
        return x;
    });
    count(p.total);
    count(p.unreadCount);
    if (p.nextCursor !== null)
        text(p.nextCursor);
    return p as unknown as Events;
}
export function coverage(value: unknown) {
    const p = object(value);
    return { catalogUniversities: count(p.catalogUniversities), registeredSources: count(p.registeredSources), freshGroups: count(p.freshGroups), archiveGroups: count(p.archiveGroups), generatedAt: date(p.generatedAt) };
}
export type Group = {
    id: string;
    title: string;
    universityName: string;
    year: number;
    sourceId: string | null;
    lookupAvailable: boolean;
};
export function groups(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const g = object(v);
        for (const k of ['id', 'title', 'universityName'])
            text(g[k]);
        count(g.year);
        if (g.sourceId !== null)
            text(g.sourceId);
        if (typeof g.lookupAvailable !== 'boolean')
            invalid();
        return g as unknown as Group;
    });
    const nextCursor = p.nextCursor === null ? null : text(p.nextCursor);
    return { items, total: count(p.total), nextCursor };
}
export function lookup(value: unknown) {
    const p = object(value);
    if (typeof p.found !== 'boolean')
        invalid();
    if (!p.found)
        return null;
    const c = object(p.candidate);
    const group = object(p.group);
    const result = { token: text(p.confirmationToken), rank: count(c.officialRank), title: text(group.title), year: count(group.year) };
    date(p.expiresAt);
    return result;
}
export function saved(value: unknown) {
    const p = object(value);
    date(p.createdAt);
    return text(p.id);
}
