import type { CalculationField } from './calculator';
import type { Snapshot } from './contracts';

const labels: Record<CalculationField, string> = {
  rank: 'Номер в списке', seats: 'Количество мест',
  excluded: 'Выше вне этого конкурса', noConsent: 'Выше без согласия',
};

export function compareSnapshots(current: Snapshot, previous?: Snapshot) {
  if (!previous || current.id === previous.id) return null;
  const movement = previous.calculation.place - current.calculation.place;
  return {
    before: previous.calculation.place,
    after: current.calculation.place,
    direction: movement > 0 ? 'improved' : movement < 0 ? 'worsened' : 'unchanged',
    distance: Math.abs(movement),
    boundaryChanged: previous.calculation.state !== current.calculation.state,
    changes: (Object.keys(labels) as CalculationField[])
      .filter(key => current.values[key] !== previous.values[key])
      .map(key => ({ key, label: labels[key], before: previous.values[key], after: current.values[key] })),
  };
}
