import { Card, Badge, Button } from '@/shared/ui';
import { SourceLookup } from '@/features/save-source-record';
import { SourceProvenance } from '@/entities/admission-source';
import type { SourceGroup } from '@/entities/admission-source';

const modes = {
  manual: 'Ручной режим',
  archive: 'Архив',
  automatic: 'Сбор данных',
  unsupported: 'Источник не подключён',
};
const studyForms: Record<string, string> = {
  'full-time': 'Очная форма',
  'part-time': 'Заочная форма',
  mixed: 'Очно-заочная форма',
};
type Props = {
  group: SourceGroup;
  selected: boolean;
  onSelect: () => void;
  onClose: () => void;
};

export function SourceGroupCard({ group, selected, onSelect, onClose }: Props) {
  return (
    <Card
      as="article"
      className="source-catalog-card"
    >
      <Badge>
        {modes[group.coverage]} · {group.year}
      </Badge>
      <h2>{group.title.replace(/ · (?:full-time|part-time|mixed)$/u, '')}</h2>
      <p>
        {group.universityName}
        {group.parentUniversityId ? ' · филиал' : ' · головной вуз'}
      </p>
      <p>
        {studyForms[group.studyForm] ?? group.studyForm} ·{' '}
        {group.funding === 'budget'
          ? 'Бюджет'
          : group.funding === 'contract'
            ? 'Платное обучение'
            : group.funding}{' '}
        ·{' '}
        {group.seats === null ? 'Число мест не подтверждено' : `${group.seats} мест в этой группе`}
      </p>
      {(group.dataKind === 'archive' || group.coverage === 'archive') && (
        <p>Архив {group.year} года. Это не текущая приёмная кампания.</p>
      )}
      {group.fetchedAt ? (
        <p>
          Снимок получен:{' '}
          <time dateTime={group.fetchedAt}>
            {new Date(group.fetchedAt).toLocaleString('ru-RU')}
          </time>
          . Строк: {group.rowCount ?? 'не подтверждено'}.
        </p>
      ) : (
        <p>Проверенный снимок ещё не получен.</p>
      )}
      {group.sourceUpdatedAt === null && (
        <p className="small-copy">Дата обновления самим источником не подтверждена.</p>
      )}
      {['source_error', 'quarantined', 'disabled'].includes(group.sourceState ?? '') && (
        <p role="status">
          Последняя проверка источника недоступна. Дата сохранённого снимка указана отдельно.
        </p>
      )}
      <p className="small-copy">
        {group.scenarioAvailable
          ? 'После сохранения доступен условный сценарий по согласиям.'
          : 'Для этой группы числовой сценарий не подключён.'}{' '}
        Официальный результат зачисления не рассчитывается.
      </p>
      {group.lookupAvailable && (
        <Button
          variant="secondary"
          id={`lookup-${group.id}`}

          type="button"
          aria-expanded={selected}
          onClick={onSelect}
        >
          Найти свою запись
        </Button>
      )}
      {selected && (
        <SourceLookup
          key={group.id}
          group={group}
          onClose={onClose}
        />
      )}
      <SourceProvenance group={group} />
    </Card>
  );
}
