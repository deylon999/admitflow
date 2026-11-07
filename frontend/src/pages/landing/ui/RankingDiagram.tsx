import { Card } from '@/shared/ui';
const excludedIndices = new Set(
  Array.from({ length: 119 }, (_, index) => index + 1)
    .filter((index) => index % 5 === 0 || index % 3 === 0)
    .slice(0, 46),
);
function Cells({ start, end, after = false }: { start: number; end: number; after?: boolean }) {
  return (
    <>
      {Array.from({ length: end - start + 1 }, (_, index) => index + start).map((index) => (
        <span
          key={index}
          className={`rank-cell ${after ? (index === 74 ? 'yours' : index > 74 ? 'vacant' : '') : index === 120 ? 'yours' : excludedIndices.has(index) ? 'excluded' : ''}`}
        />
      ))}
    </>
  );
}
export function RankingDiagram() {
  return (
    <Card
      className="ranking-card"
      role="img"
      aria-label="Ручной сценарий: номер 120 минус две непересекающиеся группы, всего 46 человек выше; расчётное место 74 при 90 местах"
    >
      <p className="eyebrow">Как в списке</p>
      <div
        className="ranking-grid"
        id="ranking-before"
        aria-hidden="true"
      >
        <Cells
          start={1}
          end={90}
        />
      </div>
      <p className="ranking-boundary">Граница: 90 бюджетных мест</p>
      <div
        className="ranking-grid ranking-tail"
        id="ranking-tail"
        aria-hidden="true"
      >
        <Cells
          start={91}
          end={120}
        />
      </div>
      <p className="eyebrow second-ranking-title">В ручном сценарии</p>
      <div
        className="ranking-grid"
        id="ranking-after"
        aria-hidden="true"
      >
        <Cells
          start={1}
          end={90}
          after
        />
      </div>
      <div className="legend">
        <span>
          <i className="swatch competitor" />
          Конкурируют с вами
        </span>
        <span>
          <i className="swatch excluded" />
          Вне конкурса или без согласия
        </span>
        <span>
          <i className="swatch yours" />
          Вы
        </span>
        <span>
          <i className="swatch vacant" />
          Свободные места
        </span>
      </div>
    </Card>
  );
}
