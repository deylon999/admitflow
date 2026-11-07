import { Input, Alert } from '@/shared/ui';
import type { CalculationForm, CalculationError } from '../model/calculator';

const calculationFields = [
  {
    name: 'rank',
    id: 'rank',
    label: 'Ваш номер в списке',
    min: 1,
    example: '120',
    hint: 'Порядковый номер вашей строки в списке вуза. Не баллы и не код поступающего.',
  },
  {
    name: 'seats',
    id: 'seats',
    label: 'Бюджетных мест',
    min: 1,
    example: '90',
    hint: 'Число бюджетных мест в этом конкурсе. Посмотрите его в списке или условиях приёма.',
  },
  {
    name: 'excluded',
    id: 'excluded',
    label: 'Выше вас вне общего конкурса',
    min: 0,
    example: '0',
    hint: 'Сколько людей выше вас не участвуют в этом конкурсе. Уже отсутствующих в списке не считайте.',
  },
  {
    name: 'noConsent',
    id: 'no-consent',
    label: 'Выше вас без согласия на зачисление',
    min: 0,
    example: '0',
    hint: 'Сколько из остальных людей выше вас не подали согласие. Сверяйте отметки в списке и правила вуза.',
  },
] as const;

export function CalculationInputs({
  values,
  onChange,
  error,
  prefix = '',
  withGuidance = false,
  inlineErrors = false,
}: {
  values: CalculationForm;
  onChange: (values: CalculationForm) => void;
  error?: CalculationError;
  prefix?: string;
  withGuidance?: boolean;
  inlineErrors?: boolean;
}) {
  function renderField(field: (typeof calculationFields)[number]) {
    const invalid = Boolean(error?.fields.includes(field.name));
    const errorId = prefix + 'calculation-error';
    const hintId = prefix + field.id + '-hint';
    return (
      <div
        className="field"
        key={field.name}
      >
        <label htmlFor={prefix + field.id}>
          {withGuidance && field.name === 'excluded'
            ? 'Не участвуют в этом конкурсе'
            : withGuidance && field.name === 'noConsent'
              ? 'Не подали согласие'
              : field.label}
        </label>
        <Input
          id={prefix + field.id}
          name={field.name}
          type="number"
          inputMode="numeric"
          min={field.min}
          max="1000000"
          step="1"
          value={values[field.name]}
          required
          placeholder={withGuidance ? field.example : undefined}
          aria-invalid={invalid || undefined}
          aria-describedby={
            [withGuidance ? hintId : '', invalid ? errorId : ''].filter(Boolean).join(' ') ||
            undefined
          }
          onChange={(event) => onChange({ ...values, [field.name]: event.target.value })}
        />
        {withGuidance && (
          <p
            className="form-note"
            id={hintId}
          >
            {field.hint}
          </p>
        )}
        {(withGuidance || inlineErrors) && error && field.name === error.fields[0] && (
          <Alert
            as="p"
            className="form-error"
            id={errorId}
            role="alert"
          >
            {error.error}
          </Alert>
        )}
      </div>
    );
  }
  if (!withGuidance) return <>{calculationFields.map(renderField)}</>;
  return (
    <>
      <fieldset className="direction-section">
        <legend>Данные из конкурсного списка</legend>
        <p className="form-note direction-section-intro">
          Откройте один список для выбранного направления и конкурса. Все числа берите из него.
        </p>
        {calculationFields.slice(0, 2).map(renderField)}
      </fieldset>
      <fieldset className="direction-section">
        <legend>Кто находится выше вас</legend>
        <p className="form-note direction-section-intro">
          Учитывайте только людей выше вашей строки. Один человек — только в одной из двух групп.
        </p>
        {calculationFields.slice(2).map(renderField)}
        <p className="form-note">
          Оставляйте 0, только если проверили, что таких людей нет. Если число неизвестно, сначала
          уточните его в списке или приёмной комиссии.
        </p>
        <details className="form-help">
          <summary>Как посчитать без ошибок</summary>
          <p>
            Сначала посчитайте тех, кто выше вас и не участвует в этом конкурсе. Затем среди
            остальных — тех, у кого нет согласия. Не считайте одного человека дважды.
          </p>
          <p>
            Например: ваш номер 120, вне конкурса выше вас 30 человек, ещё 16 — без согласия.
            Расчётное место будет 74. Это сценарий по введённым данным, а не гарантия поступления.
          </p>
        </details>
      </fieldset>
    </>
  );
}
