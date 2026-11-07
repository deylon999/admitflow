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
