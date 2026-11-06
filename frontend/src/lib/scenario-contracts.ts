import { InvalidResponseError } from './contracts';
import { sourceInt, sourceObject, sourceText, sourceTime } from './source-contracts';
import { compareOpaqueIds, instantMicros } from './time';
export type ScenarioState = 'within' | 'conditional' | 'out' | 'unsupported' | 'insufficient_data';
export type ScenarioNumbers = {
  currentLower: number;
  currentUpper: number;
  allConsentPlace: number;
  seats: number;
  consentYesAbove: number;
  consentNoAbove: number;
  consentUnknownAbove: number;
  withdrawnAbove: number;
};
export type ScenarioResult = {
  modelVersion: 'listed-consent-v1';
  state: ScenarioState;
  numbers: ScenarioNumbers | null;
  reasonCodes: string[];
  assumptions: string[];
  officialResultAvailable: false;
};
export type Scenario = {
  subscriptionId: string;
  groupId: string;
  sourceId: string | null;
  available: boolean;
  id: string | null;
  snapshotId: string | null;
  fetchedAt: string | null;
  sourceUpdatedAt: string | null;
  assessedAt: string | null;
  result: ScenarioResult | null;
  changes: { field: string; before: unknown; after: unknown }[];
  notice: string | null;
  explanation: {
    version: 'scenario-explanation-v1';
    summary: string;
    basis: string[];
    limitations: string[];
    changes: string[];
  } | null;
  previousId: string | null;
};
const states = ['within', 'conditional', 'out', 'unsupported', 'insufficient_data'];
const reasons = [
  'listed_consent_scenario',
  'priorities_not_applied',
  'own_consent_assumed',
  'unknown_participation_included',
  'unknown_consent_bounds',
  'unknown_consent_crosses_capacity',
  'unsupported_funding',
  'unsupported_category',
  'missing_or_zero_capacity',
  'candidate_not_in_snapshot',
  'candidate_withdrawn',
  'incomplete_official_order',
  'incomplete_snapshot',
  'unsupported_model_version',
];
const numeric = [
  'currentLower',
  'currentUpper',
  'allConsentPlace',
  'seats',
  'consentYesAbove',
  'consentNoAbove',
  'consentUnknownAbove',
  'withdrawnAbove',
] as const;
const fields = [
  ...numeric,
  'officialRank',
  'score',
  'consent',
  'priority',
  'participation',
  'present',
  'state',
  'modelVersion',
];
const strings = (v: unknown, max = 10) => {
  if (!Array.isArray(v) || v.length > max) throw new InvalidResponseError();
  return v.map((x) => sourceText(x, 700));
};
const nullableText = (v: unknown, max = 36) => (v === null ? null : sourceText(v, max));
const nullableTime = (v: unknown) => (v === null ? null : sourceTime(v));
export function parseResult(value: unknown): ScenarioResult {
  const o = sourceObject(value);
  if (
    o.modelVersion !== 'listed-consent-v1' ||
    o.officialResultAvailable !== false ||
    !states.includes(String(o.state))
  )
    throw new InvalidResponseError();
  let numbers: ScenarioNumbers | null = null;
  if (o.numbers !== null) {
    const n = sourceObject(o.numbers);
    numbers = Object.fromEntries(
      numeric.map((key) => [
        key,
        sourceInt(
          n[key],
          ['currentLower', 'currentUpper', 'allConsentPlace', 'seats'].includes(key) ? 1 : 0,
        ),
      ]),
    ) as ScenarioNumbers;
    if (
      numbers.currentLower !== 1 + numbers.consentYesAbove ||
      numbers.currentUpper !== numbers.currentLower + numbers.consentUnknownAbove ||
      numbers.allConsentPlace !==
        1 + numbers.consentYesAbove + numbers.consentNoAbove + numbers.consentUnknownAbove
    )
      throw new InvalidResponseError();
    if (
      (o.state === 'within' && numbers.allConsentPlace > numbers.seats) ||
      (o.state === 'out' && numbers.currentLower <= numbers.seats) ||
      (o.state === 'conditional' &&
        !(numbers.currentUpper <= numbers.seats && numbers.allConsentPlace > numbers.seats)) ||
      (o.state === 'insufficient_data' &&
        !(numbers.currentLower <= numbers.seats && numbers.currentUpper > numbers.seats)) ||
      o.state === 'unsupported'
    )
      throw new InvalidResponseError();
  } else if (!['unsupported', 'insufficient_data'].includes(String(o.state)))
    throw new InvalidResponseError();
  const reasonCodes = strings(o.reasonCodes, 10);
  if (reasonCodes.some((code) => !reasons.includes(code))) throw new InvalidResponseError();
  return {
    modelVersion: 'listed-consent-v1',
    state: o.state as ScenarioState,
    numbers,
    reasonCodes,
    assumptions: strings(o.assumptions, 10),
    officialResultAvailable: false,
  };
}
export function parseScenario(value: unknown): Scenario {
  const o = sourceObject(value);
  if (typeof o.available !== 'boolean' || !Array.isArray(o.changes) || o.changes.length > 20)
    throw new InvalidResponseError();
  const result = o.result === null ? null : parseResult(o.result);
  const id = nullableText(o.id),
    snapshotId = nullableText(o.snapshotId),
    fetchedAt = nullableTime(o.fetchedAt),
    assessedAt = nullableTime(o.assessedAt);
  const e = o.explanation === null ? null : sourceObject(o.explanation);
  if (
    (o.available && (!result || !id || !snapshotId || !fetchedAt || !assessedAt || !e)) ||
    (!o.available && (result || id || assessedAt || e || o.changes.length))
  )
    throw new InvalidResponseError();
  if (e && e.version !== 'scenario-explanation-v1') throw new InvalidResponseError();
  const changes = o.changes.map((value) => {
    const c = sourceObject(value),
      field = sourceText(c.field, 50);
    if (
      !fields.includes(field) ||
      c.before === undefined ||
      c.after === undefined ||
      [c.before, c.after].some(
        (x) => x !== null && !['string', 'number', 'boolean'].includes(typeof x),
      )
    )
      throw new InvalidResponseError();
    return { field, before: c.before, after: c.after };
  });
  return {
    subscriptionId: sourceText(o.subscriptionId, 36),
    groupId: sourceText(o.groupId, 36),
    sourceId: nullableText(o.sourceId),
    available: o.available,
    id,
    snapshotId,
    fetchedAt,
    sourceUpdatedAt: nullableTime(o.sourceUpdatedAt),
    assessedAt,
    result,
    changes,
    notice: nullableText(o.notice, 500),
    previousId: nullableText(o.previousId),
    explanation: e
      ? {
          version: 'scenario-explanation-v1',
          summary: sourceText(e.summary, 700),
          basis: strings(e.basis, 8),
          limitations: strings(e.limitations, 10),
          changes: strings(e.changes, 20),
        }
      : null,
  };
}
export function assertScenarioOrder(items: Scenario[]) {
  const seen = new Set<string>();
  items.forEach((item, index) => {
    if (
      !item.available ||
      !item.id ||
      !item.fetchedAt ||
      seen.has(item.id) ||
      item.subscriptionId !== items[0].subscriptionId ||
      item.groupId !== items[0].groupId ||
      item.sourceId !== items[0].sourceId
    )
      throw new InvalidResponseError();
    seen.add(item.id);
    const previous = items[index - 1];
    if (
      previous &&
      (instantMicros(previous.fetchedAt!) < instantMicros(item.fetchedAt) ||
        (instantMicros(previous.fetchedAt!) === instantMicros(item.fetchedAt) &&
          compareOpaqueIds(previous.id!, item.id) <= 0))
    )
      throw new InvalidResponseError();
  });
}
export function parseScenarioPage(value: unknown) {
  const o = sourceObject(value);
  if (!Array.isArray(o.items) || o.items.length > 100) throw new InvalidResponseError();
  const items = o.items.map(parseScenario);
  assertScenarioOrder(items);
  const total = sourceInt(o.total),
    nextCursor = nullableText(o.nextCursor);
  if (total < items.length || (nextCursor !== null && nextCursor !== items.at(-1)?.id))
    throw new InvalidResponseError();
  return { items, total, nextCursor };
}
