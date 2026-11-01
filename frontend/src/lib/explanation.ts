import { calculatePlace } from './calculator';
import type { CalculationForm } from './calculator';

export function explainScenario(values: CalculationForm) {
  const result = calculatePlace(values);
  if ('error' in result) return null;
  const rank = Number(values.rank);
  const excluded = Number(values.excluded);
  const noConsent = Number(values.noConsent);
  return {
    current: `${rank} − ${excluded} − ${noConsent} = ${result.place}`,
    allConsent: `${rank} − ${excluded} = ${result.worstPlace}`,
    interpretation: {
      safe: `Расчётное место укладывается в ${result.seats} мест в обоих рассмотренных сценариях.`,
      conditional: `Место ${result.place} укладывается в ${result.seats} мест. При согласии всех указанных выше место ${result.worstPlace} окажется за этой границей.`,
      out: `В обоих рассмотренных сценариях место находится за границей ${result.seats} мест. Изменения состава списка эта модель не прогнозирует.`,
    }[result.state],
  };
}
