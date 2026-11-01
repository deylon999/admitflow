import { explainScenario } from '../lib/explanation';
import type { CalculationForm } from '../lib/calculator';

export function ScenarioExplanation({ values }: { values: CalculationForm }) {
  const explanation = explainScenario(values);
  if (!explanation) return null;
  return <details className="scenario-explanation">
    <summary>Как получен результат</summary>
    <dl>
      <dt>Текущий сценарий: номер − вне этого конкурса − без согласия</dt>
      <dd><code>{explanation.current}</code></dd>
      <dt>Если все указанные выше подадут согласие: номер − вне этого конкурса</dt>
      <dd><code>{explanation.allConsent}</code></dd>
    </dl>
    <p>{explanation.interpretation}</p>
    <p>Вычитаемые группы не пересекаются. Число мест, состав списка и остальные условия считаются неизменными. Приоритеты и специальные правила вуза здесь не проверены. Расчёт не гарантирует зачисление.</p>
  </details>;
}
