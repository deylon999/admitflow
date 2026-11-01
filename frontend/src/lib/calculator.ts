export type CalculationValues = { rank: number; seats: number; excluded: number; noConsent: number };
export type CalculationField = keyof CalculationValues;
export type CalculationForm = Record<CalculationField, string | number>;
export type CalculationState = 'safe' | 'conditional' | 'out';
export type CalculationResult = {
  place: number;
  worstPlace: number;
  seats: number;
  state: CalculationState;
  status: string;
};
export type CalculationError = { error: string; fields: CalculationField[] };
export const exampleValues: CalculationValues = { rank: 120, seats: 90, excluded: 30, noConsent: 16 };

/** Two disjoint groups ABOVE the applicant, within one competition group. */
export function calculatePlace(form: CalculationForm): CalculationResult | CalculationError {
  const values = {} as CalculationValues;
  for (const field of ['rank', 'seats', 'excluded', 'noConsent'] as const) {
    const raw = form[field];
    if ((typeof raw !== 'string' && typeof raw !== 'number') || String(raw).trim() === '' || !Number.isSafeInteger(Number(raw))) {
      return { error: 'Введите целые числа во все четыре поля.', fields: [field] };
    }
    values[field] = Number(raw);
    if (values[field] > 1_000_000 || values[field] < (field === 'rank' || field === 'seats' ? 1 : 0)) {
      return { error: field === 'rank' || field === 'seats' ? 'Номер и количество мест должны быть от 1 до 1 000 000.' : 'Количество людей должно быть от 0 до 1 000 000.', fields: [field] };
    }
  }
  if (values.excluded + values.noConsent >= values.rank) {
    return { error: 'Число людей выше вас должно быть меньше вашего номера. Не учитывайте одного человека в обеих группах.', fields: ['excluded', 'noConsent'] };
  }
  const place = values.rank - values.excluded - values.noConsent;
  const worstPlace = values.rank - values.excluded;
  const state = worstPlace <= values.seats ? 'safe' : place <= values.seats ? 'conditional' : 'out';
  return { place, worstPlace, seats: values.seats, state, status: {
    safe: 'В пределах мест в обоих рассмотренных сценариях',
    conditional: 'В пределах мест только в текущем сценарии согласий',
    out: 'За границей мест по введённым данным',
  }[state] };
}

export type ScenarioAssessment =
  | { state: 'ready'; result: CalculationResult }
  | { state: 'unsupported'; reason: string }
  | { state: 'insufficient_data'; reason: string; error?: CalculationError };

export function assessScenario(form: CalculationForm | null, mode = 'manual', modelVersion = 'manual-v1'): ScenarioAssessment {
  if (mode !== 'manual' || modelVersion !== 'manual-v1') {
    return { state: 'unsupported', reason: 'Этот режим или версия правил ещё не поддерживается. Числовой вывод недоступен.' };
  }
  if (form === null) return { state: 'insufficient_data', reason: 'Недостаточно данных для расчёта. Заполните четыре числовых поля.' };
  const result = calculatePlace(form);
  return 'error' in result ? { state: 'insufficient_data', reason: result.error, error: result } : { state: 'ready', result };
}
