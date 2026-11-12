import { array, bool, checksum, count, date, identifier, invalid, nullable, object, oneOf, positive, text, url, year } from './api';

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
export function coverage(value: unknown) {
    const p = object(value);
    return { ...p, catalogUniversities: count(p.catalogUniversities), registeredSources: count(p.registeredSources), freshGroups: count(p.freshGroups), archiveGroups: count(p.archiveGroups), generatedAt: date(p.generatedAt) };
}
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
function share(value: unknown) {
    if (value === null) return null;
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1 ? value : invalid();
}
function counts(value: unknown) { return Object.fromEntries(Object.entries(object(value)).map(([k, v]) => [k, count(v)])); }
export function nationalCoverage(value: unknown) {
    const p = object(value), d = object(p.denominator), s = object(p.sources), o = object(p.operations), worker = object(o.worker), jobs = object(o.jobs), inputs = object(p.inputs), gaps = object(p.gaps), lists = object(p.lists);
    const denominator = { ...d, total: count(d.total), civil: count(d.civil), departmental: count(d.departmental), abroadExcluded: count(d.abroadExcluded), datasetDate: date(d.datasetDate), sourceUrl: url(d.sourceUrl), rule: text(d.rule) };
    if (denominator.civil + denominator.departmental !== denominator.total) invalid();
    const target = share(p.target);
    if (target === null) invalid();
    const layers = array(p.layers, v => {
        const x = object(v), covered = count(x.covered), total = count(x.total);
        if (covered > total || total !== denominator.total) invalid();
        return { ...x, id: identifier(x.id), title: text(x.title), note: text(x.note), covered, total, share: share(x.share), targetMet: bool(x.targetMet) };
    });
    return {
        ...p, generatedAt: date(p.generatedAt), target, denominator, layers,
        byYear: array(p.byYear, v => { const x = object(v); return { ...x, year: year(x.year), programs: count(x.programs), examRequirements: count(x.examRequirements) }; }),
        gaps: { ...gaps, unmatchedCatalogHeads: count(gaps.unmatchedCatalogHeads), ambiguousCatalogHeads: count(gaps.ambiguousCatalogHeads), registryOnly: count(gaps.registryOnly), branchProgramsNotCounted: count(gaps.branchProgramsNotCounted), headsWithoutPrograms: count(gaps.headsWithoutPrograms) },
        lists: { ...lists, groups: count(lists.groups), freshGroups: count(lists.freshGroups), archiveGroups: count(lists.archiveGroups) },
        regions: array(p.regions, v => { const x = object(v); return { ...x, region: text(x.region), total: count(x.total), catalog: count(x.catalog), programs: count(x.programs), lists: count(x.lists) }; }),
        sources: { ...s, total: count(s.total), byState: counts(s.byState), problems: array(s.problems, v => { const x = object(v); return { ...x, sourceId: identifier(x.sourceId), university: text(x.university), group: text(x.group), state: text(x.state), domain: text(x.domain) }; }) },
        operations: { ...o, status: text(o.status), worker: { ...worker, state: text(worker.state), lastSeenAt: nullable(worker.lastSeenAt, date) }, jobs: { ...jobs, byState: counts(jobs.byState), overdue: count(jobs.overdue) } },
        inputs: { ...inputs, checksum: checksum(inputs.checksum), registrySha256: checksum(inputs.registrySha256), catalogSha256: checksum(inputs.catalogSha256) },
    };
}
export type NationalCoverage = ReturnType<typeof nationalCoverage>;
export type CoverageLayer = NationalCoverage['layers'][number];
export function competition(value: unknown) {
    const p = object(value), s = object(p.snapshot);
    return { ...p, groupId: identifier(p.groupId), title: text(p.title), universityId: identifier(p.universityId), universityName: text(p.universityName), year: year(p.year), level: text(p.level), studyForm: text(p.studyForm), funding: text(p.funding), category: text(p.category), sourceState: text(p.sourceState),
        snapshot: { ...s, id: identifier(s.id), fetchedAt: date(s.fetchedAt), sourceUpdatedAt: nullable(s.sourceUpdatedAt, date), kind: oneOf(s.kind, ['live', 'archive']), rowCount: count(s.rowCount), complete: bool(s.complete), seats: nullable(s.seats, count), sourceUrl: nullable(s.sourceUrl, url) },
        warnings: array(p.warnings, text), prioritiesPublished: bool(p.prioritiesPublished), consentPublished: bool(p.consentPublished), myRank: nullable(p.myRank, positive),
        history: array(p.history, v => { const h = object(v); return { ...h, id: identifier(h.id), fetchedAt: date(h.fetchedAt), rowCount: count(h.rowCount), seats: nullable(h.seats, count), published: bool(h.published) }; }),
    };
}
export type CompetitionInfo = ReturnType<typeof competition>;
export function competitionRows(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => {
        const r = object(v);
        const score = nullable(r.score, text);
        if (score !== null && (!/^\d+(\.\d+)?$/.test(score) || !Number.isFinite(Number(score)))) invalid();
        for (const k of Object.keys(r)) if (!['officialRank', 'score', 'consent', 'priority', 'participation', 'mine'].includes(k)) invalid();
        return { officialRank: positive(r.officialRank), score, consent: nullable(r.consent, bool), priority: nullable(r.priority, positive), participation: oneOf(r.participation, ['unknown', 'active', 'withdrawn', 'enrolled']), mine: bool(r.mine) };
    });
    const total = count(p.total), nextOffset = nullable(p.nextOffset, positive);
    if (items.length > total || (nextOffset !== null && nextOffset >= total)) invalid();
    return { items, total, nextOffset };
}
export type CompetitionRow = ReturnType<typeof competitionRows>['items'][number];
export function competitionSummary(value: unknown) {
    const p = object(value), c = object(p.byConsent), part = object(p.byParticipation);
    const total = count(p.total);
    const byConsent = { yes: count(c.yes), no: count(c.no), unknown: count(c.unknown) };
    const byParticipation = { unknown: count(part.unknown), active: count(part.active), withdrawn: count(part.withdrawn), enrolled: count(part.enrolled) };
    if (Object.values(byConsent).reduce((a, b) => a + b, 0) !== total || Object.values(byParticipation).reduce((a, b) => a + b, 0) !== total) invalid();
    return { ...p, total, seats: nullable(p.seats, count), byConsent, byParticipation, priorityKnown: count(p.priorityKnown), priorityFirst: count(p.priorityFirst), scoreKnown: count(p.scoreKnown),
        scoreBins: array(p.scoreBins, v => { const b = object(v), lower = count(b.lower), upper = count(b.upper); if (upper <= lower) invalid(); return { lower, upper, count: count(b.count) }; }),
        myRank: nullable(p.myRank, positive), aboveMe: nullable(p.aboveMe, v => { const a = object(v); return { ...a, total: count(a.total), consentYes: count(a.consentYes), consentNo: count(a.consentNo), consentUnknown: count(a.consentUnknown), withdrawn: count(a.withdrawn), priorityFirst: count(a.priorityFirst) }; }), warnings: array(p.warnings, text),
    };
}
export type CompetitionSummary = ReturnType<typeof competitionSummary>;
export function competitionGroups(value: unknown) {
    const p = object(value);
    const items = array(p.items, v => { const g = object(v); return { ...g, id: identifier(g.id), title: text(g.title), universityName: text(g.universityName), year: year(g.year), coverage: oneOf(g.coverage, ['archive', 'automatic', 'manual', 'unsupported']), seats: nullable(g.seats, count) }; });
    const total = count(p.total);
    if (items.length > total) invalid();
    return { ...p, items, total, nextCursor: nullable(p.nextCursor, identifier) };
}
export type CompetitionGroup = ReturnType<typeof competitionGroups>['items'][number];
