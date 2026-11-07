import { Card, Alert } from '@/shared/ui';
import { useState } from 'react';
import {
  assessScenario,
  exampleValues,
  CalculationInputs,
  CalculationOutput,
} from '@/entities/manual-direction';
import type { CalculationForm } from '@/entities/manual-direction';
export function Calculator() {
  const [values, setValues] = useState<CalculationForm>(exampleValues);
  const assessment = assessScenario(values);
  const error = assessment.state === 'insufficient_data' ? assessment.error : undefined;
  return (
    <section
      className="section container calculator-section"
      id="calculator"
      aria-labelledby="calculator-title"
    >
      <p className="eyebrow">Калькулятор</p>
      <h2 id="calculator-title">Посчитайте своё место</h2>
      <p className="section-description">
        Подставьте данные из своего списка. Расчёт идёт по текущим цифрам.
      </p>
      <div className="calculator-grid">
        <Card
          as="form"
          className="calculator-form"
          id="calculator-form"
          noValidate
          onSubmit={(event) => event.preventDefault()}
        >
          <CalculationInputs
            values={values}
            onChange={setValues}
            error={error}
          />
          <p className="form-note">
            Значения — пример. Подставьте данные из своего списка. Учитывайте людей в одной
            конкурсной группе, без повторов между двумя вычитаемыми группами.
          </p>
          <Alert
            as="p"
            className="form-error"
            id="calculation-error"
            role="alert"
            hidden={!error}
          >
            {error?.error}
          </Alert>
        </Card>
        <CalculationOutput
          assessment={assessment}
          values={values}
        />
      </div>
    </section>
  );
}
