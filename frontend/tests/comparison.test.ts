import { expect, it } from 'vitest';
import fixture from '../../shared/manual-watch.json';
import { calculatePlace, exampleValues } from '../src/lib/calculator';
import type { CalculationValues } from '../src/lib/calculator';
import { parseSnapshot } from '../src/lib/contracts';
import { compareSnapshots } from '../src/lib/comparison';

function snapshot(values: CalculationValues, id: string) {
  return parseSnapshot({ ...fixture.latest, id, values, calculation: calculatePlace(values) });
}
const previous = snapshot(exampleValues, 'previous');

it('shows worsening when people above submit consent', () => {
  const result = compareSnapshots(snapshot({ ...exampleValues, noConsent: 0 }, 'new'), previous);
  expect(result).toMatchObject({ before: 74, after: 90, direction: 'worsened', distance: 16 });
  expect(result?.changes).toEqual([{ key: 'noConsent', label: 'Выше без согласия', before: 16, after: 0 }]);
  expect(previous.values.noConsent).toBe(16);
});
it('shows improvement when the entered rank changes', () => {
  expect(compareSnapshots(snapshot({ ...exampleValues, rank: 100 }, 'new'), previous))
    .toMatchObject({ direction: 'improved', distance: 20 });
});
it('separates a capacity change from unchanged position', () => {
  expect(compareSnapshots(snapshot({ ...exampleValues, seats: 73 }, 'new'), previous))
    .toMatchObject({ direction: 'unchanged', distance: 0, boundaryChanged: true });
});
it('handles the first record and unchanged inputs', () => {
  expect(compareSnapshots(previous)).toBeNull();
  expect(compareSnapshots(previous, previous)).toBeNull();
  expect(compareSnapshots(snapshot(exampleValues, 'new'), previous)).toMatchObject({ direction: 'unchanged', changes: [] });
});
