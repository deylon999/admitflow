import { useState } from 'react';
import { assessScenario, exampleValues } from '../lib/calculator';
import type { CalculationForm, CalculationError, ScenarioAssessment } from '../lib/calculator';
import { ScenarioExplanation } from './ScenarioExplanation';

export const calculationFields = [
  { name: 'rank', id: 'rank', label: 'Ваш номер в списке', min: 1 },
  { name: 'seats', id: 'seats', label: 'Бюджетных мест', min: 1 },
  { name: 'excluded', id: 'excluded', label: 'Выше вас вне общего конкурса', min: 0 },
  { name: 'noConsent', id: 'no-consent', label: 'Выше вас без согласия на зачисление', min: 0 },
] as const;

export function CalculationInputs({ values, onChange, error, prefix = '' }: { values: CalculationForm; onChange: (values: CalculationForm) => void; error?: CalculationError; prefix?: string }) {
  return <>{calculationFields.map(field => <div className="field" key={field.name}>
    <label htmlFor={prefix + field.id}>{field.label}</label>
    <input id={prefix + field.id} name={field.name} type="number" inputMode="numeric" min={field.min} max="1000000" step="1" value={values[field.name]} required aria-invalid={error?.fields.includes(field.name) || undefined} aria-describedby={error ? prefix + 'calculation-error' : undefined} onChange={event => onChange({ ...values, [field.name]: event.target.value })} />
  </div>)}</>;
}

export function ResultLegend() {
  return <div className="legend result-legend"><span><i className="swatch competitor" />Конкурируют с вами</span><span><i className="swatch yours" />Вы</span><span><i className="swatch vacant" />Свободно</span></div>;
}
export function CalculationOutput({ assessment, values }: { assessment: ScenarioAssessment; values: CalculationForm }) {
  const result = assessment.state === 'ready' ? assessment.result : { error: assessment.reason, fields: [] };
  const valid = !('error' in result);
  return <div className="result-card surface" aria-live="polite" aria-atomic="true">
    <span className="tag">Ручной сценарий</span>
    <div className="result-place" id="result-place">{valid ? result.place : '—'}</div>
    <p className="result-caption">место по введённым данным</p>
    <div className="result-facts"><div><strong id="effective-seats">{valid ? result.worstPlace : '—'}</strong><p>место, если все, кто выше и пока без согласия, подадут его</p></div><div><strong id="budget-seats">{valid ? result.seats : '—'}</strong><p>бюджетных мест</p></div></div>
    <p className="result-status" id="result-status" data-state={valid ? result.state : assessment.state}>{valid ? result.status : result.error}</p>
    <div className="progress-bar" id="progress-bar" hidden={!valid} role="img" aria-label={valid ? `Ваше место ${result.place}, бюджетных мест ${result.seats}` : undefined}>
      <span className="progress-competitors" style={{ width: valid ? `${(result.place - 1) / Math.max(result.place, result.seats) * 100}%` : 0 }} /><span className="progress-yours" style={{ width: valid ? `${1 / Math.max(result.place, result.seats) * 100}%` : 0 }} /><span className="progress-free" />
    </div><ResultLegend />
    {valid && <ScenarioExplanation values={values} />}
  </div>;
}

export function Calculator() {
  const [values, setValues] = useState<CalculationForm>(exampleValues);
  const assessment = assessScenario(values);
  const error = assessment.state === 'insufficient_data' ? assessment.error : undefined;
  return <section className="section container calculator-section" id="calculator" aria-labelledby="calculator-title">
    <p className="eyebrow">Калькулятор</p><h2 id="calculator-title">Посчитайте своё место</h2><p className="section-description">Подставьте данные из своего списка. Расчёт идёт по текущим цифрам.</p>
    <div className="calculator-grid"><form className="calculator-form" id="calculator-form" noValidate onSubmit={event => event.preventDefault()}>
      <CalculationInputs values={values} onChange={setValues} error={error} />
      <p className="form-note">Значения — пример. Подставьте данные из своего списка. Учитывайте людей в одной конкурсной группе, без повторов между двумя вычитаемыми группами.</p>
      <p className="form-error" id="calculation-error" role="alert" hidden={!error}>{error?.error}</p>
    </form><CalculationOutput assessment={assessment} values={values} /></div>
  </section>;
}
