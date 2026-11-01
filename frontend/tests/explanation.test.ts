import { expect, it } from 'vitest';
import { explainScenario } from '../src/lib/explanation';
import { exampleValues } from '../src/lib/calculator';

it('ties both formulas and the boundary to the supplied numbers', () => {
  const explanation = explainScenario(exampleValues);
  expect(explanation?.current).toBe('120 − 30 − 16 = 74');
  expect(explanation?.allConsent).toBe('120 − 30 = 90');
  expect(explanation?.interpretation).toContain('90 мест');
});

it('changes the conditional explanation when capacity changes', () => {
  const explanation = explainScenario({ ...exampleValues, seats: 80 });
  expect(explanation?.interpretation).toContain('Место 74');
  expect(explanation?.interpretation).toContain('80 мест');
  expect(explanation?.interpretation).toContain('место 90');
});

it('does not invent an explanation for incomplete values', () => {
  expect(explainScenario({ ...exampleValues, rank: '' })).toBeNull();
});
