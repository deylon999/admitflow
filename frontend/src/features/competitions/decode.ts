import { array, bool, count, date, identifier, invalid, nullable, object, oneOf, positive, text, url, year } from '../../shared/api';

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
