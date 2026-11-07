import { expect, it } from 'vitest';
import cases from '../../shared/assessment-cases.json';
import { assessScenario, exampleValues } from '@/entities/manual-direction';

it.each(cases)('assessment parity: $name', ({ input, state }) => {
  const result = assessScenario(input.values, input.mode, input.modelVersion);
  expect(result.state).toBe(state);
  if (result.state !== 'ready') expect(result).not.toHaveProperty('result');
  else expect(result.result).toMatchObject({ place: 74, worstPlace: 90, state: 'safe' });
});

it('incomplete form is not classified as outside the budget', () => {
  const result = assessScenario({ ...exampleValues, rank: '' });
  expect(result.state).toBe('insufficient_data');
  expect(result).not.toHaveProperty('result');
});
