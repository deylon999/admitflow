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
function program(value: unknown) {
    const p = object(value);
    for (const k of ['id', 'title', 'universityId', 'universityName', 'region', 'campaignId', 'level', 'studyForm', 'funding', 'category'])
        text(p[k]);
    count(p.year);
    if (p.code !== null)
        text(p.code);
    if (p.seats !== null)
        count(p.seats);
    for (const k of ['historicalCutoff', 'examRequirements', 'forecast'])
        if (p[k] !== null)
            invalid();
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
