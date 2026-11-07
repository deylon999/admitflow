import { Card, Badge } from '@/shared/ui';
import type { ScenarioAssessment, CalculationForm } from '../model/calculator';
import { ScenarioExplanation } from './ScenarioExplanation';

function ResultLegend() {
  return (
    <div className="legend result-legend">
      <span>
        <i className="swatch competitor" />
        Конкурируют с вами
      </span>
      <span>
        <i className="swatch yours" />
        Вы
      </span>
      <span>
        <i className="swatch vacant" />
        Свободно
      </span>
    </div>
  );
}
export function CalculationOutput({
  assessment,
  values,
}: {
  assessment: ScenarioAssessment;
  values: CalculationForm;
}) {
  const result =
    assessment.state === 'ready' ? assessment.result : { error: assessment.reason, fields: [] };
  const valid = !('error' in result);
  return (
    <Card
      className="result-card"
      aria-live="polite"
      aria-atomic="true"
    >
      <Badge>Ручной сценарий</Badge>
      <div
        className="result-place"
        id="result-place"
      >
        {valid ? result.place : '—'}
      </div>
      <p className="result-caption">место по введённым данным</p>
      <div className="result-facts">
        <div>
          <strong id="effective-seats">{valid ? result.worstPlace : '—'}</strong>
          <p>место, если все, кто выше и пока без согласия, подадут его</p>
        </div>
        <div>
          <strong id="budget-seats">{valid ? result.seats : '—'}</strong>
          <p>бюджетных мест</p>
        </div>
      </div>
      <p
        className="result-status"
        id="result-status"
        data-state={valid ? result.state : assessment.state}
      >
        {valid ? result.status : result.error}
      </p>
      <div
        className="progress-bar"
        id="progress-bar"
        hidden={!valid}
        role="img"
        aria-label={
          valid ? `Ваше место ${result.place}, бюджетных мест ${result.seats}` : undefined
        }
      >
        <span
          className="progress-competitors"
          style={{
            width: valid
              ? `${((result.place - 1) / Math.max(result.place, result.seats)) * 100}%`
              : 0,
          }}
        />
        <span
          className="progress-yours"
          style={{ width: valid ? `${(1 / Math.max(result.place, result.seats)) * 100}%` : 0 }}
        />
        <span className="progress-free" />
      </div>
      <ResultLegend />
      {valid && <ScenarioExplanation values={values} />}
    </Card>
  );
}
