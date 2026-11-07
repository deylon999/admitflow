import type { ReactNode } from 'react';
import type { Watch } from '../model/types';
import { ScenarioExplanation } from './ScenarioExplanation';

const dateFormat = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
});
function date(value: string) {
  return dateFormat.format(new Date(value));
}

export function ManualDirectionCard({ watch, children }: { watch: Watch; children: ReactNode }) {
  const { calculation } = watch.latest;
  const old = Date.now() - new Date(watch.latest.capturedAt).getTime() > 86400_000;
  return (
    <article className="direction-card surface">
      <div className="direction-top">
        <span className="eyebrow">{watch.university}</span>
        <span className="tag">Ручной ввод</span>
      </div>
      <h2>{watch.title}</h2>
      <div className="direction-result">
        <strong>{calculation.place}</strong>
        <span>
          по вашему вводу
          <br />
          <b>{calculation.seats}</b> бюджетных мест
        </span>
      </div>
      <p
        className="result-status"
        data-state={calculation.state}
      >
        {calculation.status}
      </p>
      <p className="direction-worst">
        Если все выше вас подадут согласие: <b>{calculation.worstPlace}-е место</b>.
      </p>
      <ScenarioExplanation values={watch.latest.values} />
      <p className="small-copy">
        Модель ручного сценария: {watch.latest.modelVersion}. Дата сохранения — время вашего ввода,
        обновление источника не проверено.
      </p>
      <div className="direction-source">
        <a
          href={watch.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          Открыть источник ↗
        </a>
        <span>
          Сохранено <time dateTime={watch.latest.capturedAt}>{date(watch.latest.capturedAt)}</time>
        </span>
      </div>
      {old && (
        <p className="stale-note">Цифры сохранены больше суток назад. Проверьте свежий список.</p>
      )}
      {children}
    </article>
  );
}
