import { Button } from '@/shared/ui';
import { ChangeFeed } from '@/features/review-source-changes';
import { ImportData } from '@/features/import-manual-directions';
import { WatchComparison } from '@/features/compare-manual-directions';
import { ManualReport } from '@/features/print-manual-directions';
import { useTrackerModel } from '../model/useTrackerModel';
import { ArchiveDirections } from './ArchiveDirections';
import { CoverageSummary } from './CoverageSummary';
import { TrackerHeading } from './TrackerHeading';
import { TrackerAccess } from './TrackerAccess';
import { TrackerFeedback } from './TrackerFeedback';
import { TrackerFilters } from './TrackerFilters';
import { ManualDirectionsPanel } from './ManualDirectionsPanel';

export default function TrackerPage() {
  const model = useTrackerModel();
  const { privateVisible, watches, budget, directionTotal, busy, count, visible, report } = model;
  return (
    <main
      className="container tracker-page"
      id="top"
    >
      <TrackerHeading model={model} />
      <TrackerAccess model={model} />
      <TrackerFeedback model={model} />
      <CoverageSummary />
      {privateVisible && (
        <>
          <ChangeFeed />
          <ArchiveDirections />
        </>
      )}
      {privateVisible && watches.data && budget.data && (
        <p className="small-copy">
          Всего направлений: {directionTotal} из 20 (ручные и архивные вместе). JSON, сравнение и
          печать ниже включают только ручные направления.
        </p>
      )}
      {privateVisible && (
        <ImportData
          count={directionTotal}
          disabled={
            busy || watches.isPending || watches.isError || budget.isPending || budget.isError
          }
          onDone={(result) =>
            model.setNotice(
              result.replayed
                ? 'Этот файл уже импортирован. Повтор не создаёт копий и не восстанавливает удалённое.'
                : `Импортировано направлений: ${result.importedCount}; сохранений: ${result.snapshotCount}.`,
            )
          }
        />
      )}
      {privateVisible && !watches.isError && watches.data && (
        <WatchComparison watches={watches.data} />
      )}
      <TrackerFilters model={model} />
      <ManualDirectionsPanel model={model} />
      {privateVisible && count > 0 && (
        <Button
          variant="ghost"
          className="print-action"
          type="button"
          disabled={visible.length === 0 || busy}
          onClick={report.print}
        >
          Распечатать выбранный список ({visible.length})
        </Button>
      )}
      {privateVisible && (
        <ManualReport
          watches={visible}
          generatedAt={report.generatedAt}
        />
      )}
      <p className="tracker-disclaimer">
        Расчёт описывает положение по введённым данным в одной конкурсной группе. Он не учитывает
        все правила и приоритеты конкретного вуза и не гарантирует зачисление.
      </p>
    </main>
  );
}
