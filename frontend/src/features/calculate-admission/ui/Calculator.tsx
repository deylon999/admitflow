import { Card } from '@/shared/ui';
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
          aria-label="Данные для расчёта"
          aria-describedby="calculator-input-note"
          noValidate
          onSubmit={(event) => event.preventDefault()}
        >
          <p
            className="calculator-note small-copy"
            id="calculator-input-note"
          >
            Сейчас заполнен пример. Подставьте свои четыре числа из одного конкурса. Каждого
            человека выше вас учитывайте только в одной из двух групп.
          </p>
          <CalculationInputs
            values={values}
            onChange={setValues}
            error={error}
            inlineErrors
          />
        </Card>
        <CalculationOutput
          assessment={assessment}
          values={values}
        />
      </div>
    </section>
  );
}
