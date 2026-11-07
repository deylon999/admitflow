import { Card, Alert, Button } from '@/shared/ui';
import type { StoredDraft } from '../model/draft-store';

export function DraftRecovery({
  record,
  disabled,
  blockedReason,
  onRestore,
  onDiscard,
}: {
  record: StoredDraft;
  disabled: boolean;
  blockedReason?: string;
  onRestore: () => void;
  onDiscard: () => void;
}) {
  return (
    <Card
      as="section"
      className="draft-recovery"
      aria-labelledby="draft-recovery-heading"
    >
      <h2 id="draft-recovery-heading">Есть несохранённый черновик</h2>
      <p>
        Из этой вкладки: {record.draft.university || 'Вуз ещё не указан'} ·{' '}
        {record.draft.title || 'Направление ещё не указано'}.
      </p>
      <p className="small-copy">
        Доступен до{' '}
        <time dateTime={new Date(record.expiresAt).toISOString()}>
          {new Date(record.expiresAt).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </time>
        . Восстановление заполнит форму. Направление сохранится только после нажатия кнопки
        сохранения.
      </p>
      {record.intent && (
        <p className="small-copy">
          Прошлое сохранение могло завершиться даже без ответа. Повторите сохранение с теми же
          данными — повтор не создаст копию.
        </p>
      )}
      {blockedReason && (
        <Alert
          as="p"
          className="form-error"
          role="status"
        >
          {blockedReason} Поля доступны для просмотра ниже.
        </Alert>
      )}
      <details>
        <summary>Посмотреть поля черновика</summary>
        <dl>
          <dt>Ссылка</dt>
          <dd>{record.draft.sourceUrl || 'Не указана'}</dd>
          <dt>Номер в списке / бюджетных мест</dt>
          <dd>
            {record.draft.values.rank || '—'} / {record.draft.values.seats || '—'}
          </dd>
          <dt>Выше вне конкурса / без согласия</dt>
          <dd>
            {String(record.draft.values.excluded) || '—'} /{' '}
            {String(record.draft.values.noConsent) || '—'}
          </dd>
        </dl>
      </details>
      <div className="direction-actions">
        <Button
          variant="primary"

          type="button"
          disabled={disabled || Boolean(blockedReason)}
          onClick={onRestore}
        >
          Восстановить черновик
        </Button>
        <Button
          variant="ghost"

          type="button"
          disabled={disabled}
          onClick={onDiscard}
        >
          Удалить черновик
        </Button>
      </div>
    </Card>
  );
}
