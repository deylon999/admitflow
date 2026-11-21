import { array, bool, checksum, count, date, identifier, invalid, nullable, object, text, url, year } from '../../shared/api';

export function coverage(value: unknown) {
    const p = object(value);
    return { ...p, catalogUniversities: count(p.catalogUniversities), registeredSources: count(p.registeredSources), freshGroups: count(p.freshGroups), archiveGroups: count(p.archiveGroups), generatedAt: date(p.generatedAt) };
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
