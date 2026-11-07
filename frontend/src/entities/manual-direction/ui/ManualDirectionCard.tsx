import { Card, Badge } from '@/shared/ui';
import type { ReactNode } from 'react';
import type { Watch } from '../model/types';
import { ScenarioExplanation } from './ScenarioExplanation';

const dateFormat = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});
function date(value: string) {
  return dateFormat.format(new Date(value));
}

export function ManualDirectionCard({
  watch,
  children,
  positionChange,
}: {
  watch: Watch;
  children: ReactNode;
  positionChange?: ReactNode;
}) {
  const { calculation } = watch.latest;
  const old = Date.now() - new Date(watch.latest.capturedAt).getTime() > 86400_000;
  return (
    <Card
      as="article"
      className="direction-card"
    >
      <div className="direction-top">
        <span className="eyebrow">{watch.university}</span>
        <Badge>Ручной ввод</Badge>
      </div>
      <h3>{watch.title}</h3>
      <div className="direction-result">
        <strong>{calculation.place}</strong>
        <span>
          расчётное место
          <br />
          <b>{calculation.seats}</b> бюджетных мест
        </span>
      </div>
      {positionChange}
      <p
        className="result-status"
        data-state={calculation.state}
      >
        {calculation.status}
      </p>
      <p className="small-copy">По вашим цифрам, без автоматического обновления.</p>
      <div className="direction-source">
        <a
          href={watch.sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          Проверить список ↗
        </a>
        <span>
          Ваше обновление:{' '}
          <time dateTime={watch.latest.capturedAt}>{date(watch.latest.capturedAt)}</time>
        </span>
      </div>
      {old && (
        <p className="stale-note">Цифры сохранены больше суток назад. Проверьте свежий список.</p>
      )}
      {children}
      <details className="direction-details">
        <summary>Подробнее о расчёте</summary>
        <p className="direction-worst">
          Если все выше вас подадут согласие: <b>{calculation.worstPlace}-е место</b>.
        </p>
        <ScenarioExplanation values={watch.latest.values} />
        <p className="small-copy">
          Модель: {watch.latest.modelVersion}. Дата сохранения — время вашего ввода, обновление
          источника не проверено.
        </p>
      </details>
    </Card>
  );
}
