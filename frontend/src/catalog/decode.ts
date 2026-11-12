import { array, bool, checksum, count, date, identifier, invalid, nullable, object, oneOf, positive, text, url, year } from '../shared/api';
import type { Accreditation, CatalogProgram, ExamRequirements, ExamTest, ProgramResults, Provenance, University, UniversityResults } from './types';

function provenance(value: unknown): Provenance {
    const p = object(value);
    return { ...p, url: url(p.url), verifiedAt: date(p.verifiedAt), sourceUpdatedAt: nullable(p.sourceUpdatedAt, date), kind: oneOf(p.kind, ['archive', 'monitoring', 'accreditation']), edition: nullable(p.edition, year), originalSha256: nullable(p.originalSha256, checksum) };
}
function accreditation(value: unknown): Accreditation {
    const p = object(value);
    const ogrn = text(p.ogrn);
    if (!/^\d{13}$/.test(ogrn)) invalid();
    return { ...p, status: oneOf(p.status, ['active']), ogrn, inn: nullable(p.inn, text), certificateNumber: nullable(p.certificateNumber, text), bachelorPrograms: count(p.bachelorPrograms), specialistPrograms: count(p.specialistPrograms), branchesWithPrograms: count(p.branchesWithPrograms), departmental: bool(p.departmental), matchMethod: oneOf(p.matchMethod, ['registry', 'name', 'domain', 'core-region', 'honorary-name-region', 'fuzzy-region']), datasetDate: date(p.datasetDate), sourceUrl: url(p.sourceUrl) };
}
export function university(value: unknown): University {
    const p = object(value);
    return { ...p, id: identifier(p.id), name: text(p.name), legalName: text(p.legalName), region: text(p.region), isBranch: bool(p.isBranch), officialUrl: nullable(p.officialUrl, url), knownProgramCount: count(p.knownProgramCount), years: array(p.years, year), provenance: provenance(p.provenance), accreditation: nullable(p.accreditation, accreditation) };
}
function examTests(value: unknown): ExamTest[] {
    const tests = array(value, item => {
        const t = object(item);
        const options = array(t.options, raw => {
            const o = object(raw);
            if (Object.keys(o).length !== 3 || !/^[a-z]+$/.test(text(o.subject))) invalid();
            const minScore = nullable(o.minScore, positive);
            if (minScore !== null && minScore > 100) invalid();
            return { subject: text(o.subject), title: text(o.title), minScore };
        });
        if (Object.keys(t).length !== 2 || !options.length) invalid();
        return { position: positive(t.position), options };
    });
    if (tests.some((t, i) => t.position !== i + 1)) invalid();
    return tests;
}
function examRequirements(value: unknown): ExamRequirements {
    const p = object(value);
    if (Object.keys(p).length !== 5 || p.benefits !== null) invalid();
    const tests = examTests(p.tests);
    if (!tests.length) invalid();
    const s = object(p.source);
    return { tests, additionalTests: nullable(p.additionalTests, examTests), benefits: null, notes: array(p.notes, text), source: { ...s, url: url(s.url), title: text(s.title), documentDate: date(s.documentDate), checkedAt: date(s.checkedAt), sha256: checksum(s.sha256), crossCheckUrl: nullable(s.crossCheckUrl, url) } };
}
export function program(value: unknown): CatalogProgram {
    const p = object(value);
    if (p.historicalCutoff !== null || p.forecast !== null) invalid();
    return { ...p, id: identifier(p.id), title: text(p.title), universityId: identifier(p.universityId), universityName: text(p.universityName), region: text(p.region), campaignId: identifier(p.campaignId), level: text(p.level), studyForm: text(p.studyForm), funding: text(p.funding), category: text(p.category), year: year(p.year), code: nullable(p.code, text), seats: nullable(p.seats, count), historicalCutoff: null, forecast: null, examRequirements: nullable(p.examRequirements, examRequirements), provenance: provenance(p.provenance) };
}
function page(value: unknown) {
    const p = object(value);
    return { p, total: count(p.total), nextOffset: nullable(p.nextOffset, positive) };
}
export function universityResults(value: unknown): UniversityResults {
    const { p, total, nextOffset } = page(value);
    const items = array(p.items, university);
    if (items.length > total || (nextOffset !== null && nextOffset >= total)) invalid();
    return { ...p, items, total, nextOffset, regions: array(p.regions, text), registryEdition: year(p.registryEdition), accreditationDate: date(p.accreditationDate) };
}
export function programResults(value: unknown): ProgramResults {
    const { p, total, nextOffset } = page(value);
    const items = array(p.items, program);
    if (items.length > total || (nextOffset !== null && nextOffset >= total)) invalid();
    return { ...p, items, total, nextOffset, years: array(p.years, year), subjects: array(p.subjects, text) };
}
