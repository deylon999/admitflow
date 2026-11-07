import { describe, expect, it } from 'vitest';
import fixtures from '../../shared/calculations.json';
import { calculatePlace, exampleValues } from '@/entities/manual-direction';
import type { CalculationForm } from '@/entities/manual-direction';

describe('manual-v1: общие сценарии TS/Python', () => {
  it.each(fixtures.valid)('$name', ({ input, expected }) => {
    expect(calculatePlace(input)).toMatchObject(expected);
  });
  it.each(fixtures.invalid)('отклоняет: $name', ({ patch }) => {
    // JSON represents untrusted runtime input, intentionally beyond the form type.
    const input = { ...exampleValues, ...patch } as unknown as CalculationForm;
    expect(calculatePlace(input)).toHaveProperty('error');
  });
});

describe('значения формы', () => {
  it('преобразует строки в целые числа', () => {
    expect(
      calculatePlace({ rank: '120', seats: '90', excluded: '30', noConsent: '16' }),
    ).toMatchObject({ place: 74, worstPlace: 90, state: 'safe' });
  });
  it.each(['', ' ', 'abc', Infinity, NaN, Number.MAX_SAFE_INTEGER])(
    'отклоняет пустой/нечисловой номер %s',
    (rank) => {
      expect(calculatePlace({ ...exampleValues, rank })).toHaveProperty('error');
    },
  );
  it('не обещает зачисление во всех возможных сценариях', () => {
    expect(calculatePlace(exampleValues)).toHaveProperty(
      'status',
      'В пределах мест в обоих рассмотренных сценариях',
    );
  });
});
