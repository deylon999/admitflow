import type { Watch } from '@/entities/manual-direction';

export function ManualReport({ watches, generatedAt }: { watches: Watch[]; generatedAt: string }) {
  return (
    <section
      className="print-report"
      aria-label="Отчёт ручных сценариев"
    >
      <h1>Абитуриент — ручные сценарии</h1>
      <p>
        Отчёт сформирован: {generatedAt}. Направлений: {watches.length}.
      </p>
      <p>
        Это расчёт по введённым данным. Он не гарантирует зачисление и не является вероятностью
        поступления. Даты сохранений не означают обновление официальных списков.
      </p>
      {watches.map((watch) => (
        <article key={watch.id}>
          <h2>
            {watch.university} · {watch.title}
          </h2>
          <p>
            Сохранено вручную: {watch.latest.capturedAt}. Модель: {watch.latest.modelVersion}.
          </p>
          <dl>
            <dt>Номер / бюджетных мест</dt>
            <dd>
              {watch.latest.values.rank} / {watch.latest.values.seats}
            </dd>
            <dt>Выше вне конкурса / без согласия</dt>
            <dd>
              {watch.latest.values.excluded} / {watch.latest.values.noConsent}
            </dd>
            <dt>Место по вводу / при согласии всех выше</dt>
            <dd>
              {watch.latest.calculation.place} / {watch.latest.calculation.worstPlace}
            </dd>
          </dl>
          <p>{watch.latest.calculation.status}</p>
          <p>Источник: {watch.sourceUrl}</p>
        </article>
      ))}
    </section>
  );
}
