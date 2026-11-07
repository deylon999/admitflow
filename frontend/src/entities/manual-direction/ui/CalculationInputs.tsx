import { Input } from '@/shared/ui';
import type { CalculationForm, CalculationError } from '../model/calculator';

const calculationFields = [
  { name: 'rank', id: 'rank', label: 'Ваш номер в списке', min: 1 },
  { name: 'seats', id: 'seats', label: 'Бюджетных мест', min: 1 },
  { name: 'excluded', id: 'excluded', label: 'Выше вас вне общего конкурса', min: 0 },
  { name: 'noConsent', id: 'no-consent', label: 'Выше вас без согласия на зачисление', min: 0 },
] as const;

export function CalculationInputs({
  values,
  onChange,
  error,
  prefix = '',
}: {
  values: CalculationForm;
  onChange: (values: CalculationForm) => void;
  error?: CalculationError;
  prefix?: string;
}) {
  return (
    <>
      {calculationFields.map((field) => (
        <div
          className="field"
          key={field.name}
        >
          <label htmlFor={prefix + field.id}>{field.label}</label>
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
            aria-invalid={error?.fields.includes(field.name) || undefined}
            aria-describedby={error ? prefix + 'calculation-error' : undefined}
            onChange={(event) => onChange({ ...values, [field.name]: event.target.value })}
          />
        </div>
      ))}
    </>
  );
}
