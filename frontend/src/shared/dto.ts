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
export type CoverageLayer = { id: string; title: string; covered: number; total: number; share: number | null; targetMet: boolean; note: string };
export type NationalCoverage = {
    generatedAt: string;
    target: number;
    denominator: { total: number; civil: number; departmental: number; abroadExcluded: number; datasetDate: string; sourceUrl: string; rule: string };
    layers: CoverageLayer[];
    byYear: { year: number; programs: number; examRequirements: number }[];
    gaps: { unmatchedCatalogHeads: number; ambiguousCatalogHeads: number; registryOnly: number; branchProgramsNotCounted: number; headsWithoutPrograms: number };
    lists: { groups: number; freshGroups: number; archiveGroups: number };
    regions: { region: string; total: number; catalog: number; programs: number; lists: number }[];
    sources: { total: number; byState: Record<string, number>; problems: { sourceId: string; university: string; group: string; state: string; domain: string }[] };
    operations: { status: string; worker: { state: string; lastSeenAt: string | null }; jobs: { byState: Record<string, number>; overdue: number } };
    inputs: { checksum: string; registrySha256: string; catalogSha256: string };
};
function share(value: unknown) {
    if (value === null)
        return null;
    if (typeof value !== 'number' || value < 0 || value > 1)
        invalid();
    return value;
}
function counts(value: unknown) {
    const p = object(value);
    for (const k of Object.keys(p))
        count(p[k]);
    return p as Record<string, number>;
}
export function nationalCoverage(value: unknown): NationalCoverage {
    const p = object(value);
    date(p.generatedAt);
    if (share(p.target) === null)
        invalid();
    const d = object(p.denominator);
    for (const k of ['total', 'civil', 'departmental', 'abroadExcluded'])
        count(d[k]);
    date(d.datasetDate);
    url(d.sourceUrl);
    text(d.rule);
    if (Number(d.civil) + Number(d.departmental) !== d.total)
        invalid();
    array(p.layers, v => {
        const x = object(v);
        for (const k of ['id', 'title', 'note'])
            text(x[k]);
        if (count(x.covered) > count(x.total) || x.total !== d.total)
            invalid();
        share(x.share);
        if (typeof x.targetMet !== 'boolean')
            invalid();
        return x;
    });
    array(p.byYear, v => {
        const x = object(v);
        count(x.year);
        count(x.programs);
        count(x.examRequirements);
        return x;
    });
    counts(p.gaps);
    counts(p.lists);
    array(p.regions, v => {
        const x = object(v);
        text(x.region);
        for (const k of ['total', 'catalog', 'programs', 'lists'])
            count(x[k]);
        return x;
    });
    const s = object(p.sources);
    count(s.total);
    counts(s.byState);
    array(s.problems, v => {
        const x = object(v);
        for (const k of ['sourceId', 'university', 'group', 'state', 'domain'])
            text(x[k]);
        return x;
    });
    const o = object(p.operations);
    text(o.status);
    text(object(o.worker).state);
    const jobs = object(o.jobs);
    counts(jobs.byState);
    count(jobs.overdue);
    const i = object(p.inputs);
    for (const k of ['checksum', 'registrySha256', 'catalogSha256'])
        if (!/^[a-f0-9]{64}$/.test(text(i[k])))
            invalid();
    return p as unknown as NationalCoverage;
}
export type CompetitionInfo = {
    groupId: string; title: string; universityId: string; universityName: string; year: number; level: string; studyForm: string; funding: string; category: string;
    sourceState: string;
    snapshot: { id: string; fetchedAt: string; sourceUpdatedAt: string | null; kind: 'live' | 'archive'; rowCount: number; complete: boolean; seats: number | null; sourceUrl: string | null };
    warnings: string[]; prioritiesPublished: boolean; consentPublished: boolean; myRank: number | null;
    history: { id: string; fetchedAt: string; rowCount: number; seats: number | null; published: boolean }[];
};
function bool(value: unknown) {
    if (typeof value !== 'boolean')
        invalid();
    return value as boolean;
}
function nullable<T>(value: unknown, read: (v: unknown) => T): T | null {
    return value === null ? null : read(value);
}
export function competition(value: unknown): CompetitionInfo {
    const p = object(value);
    for (const k of ['groupId', 'title', 'universityId', 'universityName', 'level', 'studyForm', 'funding', 'category', 'sourceState'])
        text(p[k]);
    count(p.year);
    const s = object(p.snapshot);
    text(s.id);
    date(s.fetchedAt);
    nullable(s.sourceUpdatedAt, date);
    if (!['live', 'archive'].includes(text(s.kind)))
        invalid();
    count(s.rowCount);
    bool(s.complete);
    nullable(s.seats, count);
    nullable(s.sourceUrl, url);
    array(p.warnings, text);
    bool(p.prioritiesPublished);
    bool(p.consentPublished);
    nullable(p.myRank, count);
    array(p.history, v => {
        const h = object(v);
        text(h.id);
        date(h.fetchedAt);
        count(h.rowCount);
        nullable(h.seats, count);
        bool(h.published);
        return h;
    });
    return p as unknown as CompetitionInfo;
}
export type CompetitionRow = { officialRank: number; score: string | null; consent: boolean | null; priority: number | null; participation: string; mine: boolean };
export function competitionRows(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const r = object(v);
        count(r.officialRank);
        if (r.score !== null && !/^\d+(\.\d+)?$/.test(text(r.score)))
            invalid();
        nullable(r.consent, bool);
        nullable(r.priority, count);
        if (!['unknown', 'active', 'withdrawn', 'enrolled'].includes(text(r.participation)))
            invalid();
        bool(r.mine);
        for (const k of Object.keys(r))
            if (!['officialRank', 'score', 'consent', 'priority', 'participation', 'mine'].includes(k))
                invalid();
        return r as unknown as CompetitionRow;
    });
    const total = count(p.total);
    return { items, total, nextOffset: nullable(p.nextOffset, count) };
}
export type CompetitionSummary = {
    total: number; seats: number | null; byConsent: Record<'yes' | 'no' | 'unknown', number>; byParticipation: Record<string, number>;
    priorityKnown: number; priorityFirst: number; scoreKnown: number; scoreBins: { lower: number; upper: number; count: number }[];
    myRank: number | null; aboveMe: { total: number; consentYes: number; consentNo: number; consentUnknown: number; withdrawn: number; priorityFirst: number } | null;
    warnings: string[];
};
export function competitionSummary(value: unknown): CompetitionSummary {
    const p = object(value);
    count(p.total);
    nullable(p.seats, count);
    counts(p.byConsent);
    counts(p.byParticipation);
    for (const k of ['priorityKnown', 'priorityFirst', 'scoreKnown'])
        count(p[k]);
    array(p.scoreBins, v => {
        const b = object(v);
        count(b.lower);
        count(b.upper);
        count(b.count);
        return b;
    });
    nullable(p.myRank, count);
    nullable(p.aboveMe, counts);
    array(p.warnings, text);
    return p as unknown as CompetitionSummary;
}
export type CompetitionGroup = { id: string; title: string; universityName: string; year: number; coverage: string; seats: number | null };
export function competitionGroups(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const g = object(v);
        for (const k of ['id', 'title', 'universityName', 'coverage'])
            text(g[k]);
        count(g.year);
        nullable(g.seats, count);
        return g as unknown as CompetitionGroup;
    });
    return { items, total: count(p.total), nextCursor: nullable(p.nextCursor, text) };
}
