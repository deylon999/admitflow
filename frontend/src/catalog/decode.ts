import { array, count, date, invalid, object, text, url } from '../shared/api';
function provenance(value: unknown) {
    const p = object(value);
    url(p.url);
    date(p.verifiedAt);
    if (p.sourceUpdatedAt !== null)
        date(p.sourceUpdatedAt);
    if (!['archive', 'monitoring', 'accreditation'].includes(text(p.kind)))
        invalid();
    if (p.edition !== null)
        count(p.edition);
    return p;
}
function accreditation(value: unknown) {
    const p = object(value);
    if (p.status !== 'active' || !/^\d{13}$/.test(text(p.ogrn)))
        invalid();
    if (p.inn !== null)
        text(p.inn);
    if (p.certificateNumber !== null)
        text(p.certificateNumber);
    for (const k of ['bachelorPrograms', 'specialistPrograms', 'branchesWithPrograms'])
        count(p[k]);
    if (typeof p.departmental !== 'boolean')
        invalid();
    text(p.matchMethod);
    date(p.datasetDate);
    url(p.sourceUrl);
    return p;
}
function university(value: unknown) {
    const p = object(value);
    for (const k of ['id', 'name', 'legalName', 'region'])
        text(p[k]);
    if (typeof p.isBranch !== 'boolean')
        invalid();
    if (p.officialUrl !== null)
        url(p.officialUrl);
    count(p.knownProgramCount);
    array(p.years, count);
    provenance(p.provenance);
    if (p.accreditation !== null)
        accreditation(p.accreditation);
    return p;
}
function examTests(value: unknown) {
    const tests = array(value, item => {
        const t = object(item);
        const options = array(t.options, raw => {
            const o = object(raw);
            if (Object.keys(o).length !== 3 || !/^[a-z]+$/.test(text(o.subject)))
                invalid();
            text(o.title);
            if (o.minScore !== null && (count(o.minScore) < 1 || (o.minScore as number) > 100))
                invalid();
            return o;
        });
        if (Object.keys(t).length !== 2 || !options.length)
            invalid();
        return { position: count(t.position) };
    });
    // Tests are numbered as in the document, 1..N without gaps.
    if (tests.some((t, i) => t.position !== i + 1))
        invalid();
}
function examRequirements(value: unknown) {
    const p = object(value);
    if (Object.keys(p).length !== 5 || p.benefits !== null)
        invalid();
    examTests(p.tests);
    if (!(p.tests as unknown[]).length)
        invalid();
    if (p.additionalTests !== null)
        examTests(p.additionalTests);
    array(p.notes, text);
    const s = object(p.source);
    url(s.url);
    text(s.title);
    date(s.documentDate);
    date(s.checkedAt);
    if (!/^[a-f0-9]{64}$/.test(text(s.sha256)))
        invalid();
    if (s.crossCheckUrl !== null)
        url(s.crossCheckUrl);
}
function program(value: unknown) {
    const p = object(value);
    for (const k of ['id', 'title', 'universityId', 'universityName', 'region', 'campaignId', 'level', 'studyForm', 'funding', 'category'])
        text(p[k]);
    count(p.year);
    if (p.code !== null)
        text(p.code);
    if (p.seats !== null)
        count(p.seats);
    for (const k of ['historicalCutoff', 'forecast'])
        if (p[k] !== null)
            invalid();
    if (p.examRequirements !== null)
        examRequirements(p.examRequirements);
    provenance(p.provenance);
    return p;
}
export function decodeCatalog(path: string, value: unknown): unknown {
    const isUniversity = path.startsWith('universities');
    const item = isUniversity ? university : program;
    if (path.split('?')[0].includes('/'))
        return item(value);
    const p = object(value);
    const items = array(p.items, item);
    const total = count(p.total);
    if (items.length > total)
        invalid();
    if (p.nextOffset !== null)
        count(p.nextOffset);
    if (isUniversity) {
        array(p.regions, text);
        count(p.registryEdition);
        date(p.accreditationDate);
    }
    else {
        array(p.years, count);
        array(p.subjects, text);
    }
    return p;
}
