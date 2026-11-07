import { Alert, Input, Button, Card } from '@/shared/ui';
import { useEffect, useLayoutEffect, useRef } from 'react';
import { Link } from 'react-router';
import { SourceProvenance } from '@/entities/admission-source';
import type { SourceGroup } from '@/entities/admission-source';
import { useSourceLookup } from '../model/useSourceLookup';

export function SourceLookup({ group, onClose }: { group: SourceGroup; onClose: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const savedLink = useRef<HTMLAnchorElement>(null);
  const {
    code,
    preview,
    acknowledged,
    setAcknowledged,
    attempted,
    expired,
    saved,
    access,
    lookup,
    save,
    busy,
    validCode,
    changeCode,
    findRecord,
    saveRecord,
  } = useSourceLookup(group, () => requestAnimationFrame(() => savedLink.current?.focus()));
  useEffect(() => {
    input.current?.focus();
  }, []);
  useLayoutEffect(() => {
    if (preview) heading.current?.focus();
  }, [preview]);
  if (access !== 'active')
    return (
      <Alert role="alert">
        <p>Доступ изменился или закончился. Старое подтверждение скрыто.</p>
        <Link
          data-router-link
          to="/tracker"
        >
          Управление гостевым доступом
        </Link>
      </Alert>
    );
  return (
    <div className="source-lookup">
      <h4>Найти запись в этой группе</h4>
      <p className="small-copy">
        {group.lookupCodeHint ?? 'Введите публичный код из выбранного списка.'} ФИО, паспорт и СНИЛС
        не нужны. Код не сохраняется в браузере или в карточке направления.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          findRecord();
        }}
      >
        <label>
          Код поступающего
          <Input
            ref={input}
            autoComplete="off"
            spellCheck={false}
            maxLength={64}
            disabled={busy}
            value={code}
            onChange={(event) => changeCode(event.target.value)}
          />
        </label>
        <div className="direction-actions">
          <Button
            variant="primary"

            type="submit"
            disabled={busy || !validCode}
          >
            {lookup.isPending ? 'Ищем…' : 'Найти запись'}
          </Button>
          <Button
            variant="ghost"

            type="button"
            disabled={busy}
            onClick={onClose}
          >
            Закрыть поиск
          </Button>
        </div>
      </form>
      {lookup.isError && (
        <Alert
          as="p"
          role="alert"
        >
          {lookup.error.message}
        </Alert>
      )}
      {preview && (
        <Card className="source-candidate-preview">
          <h4
            ref={heading}
            tabIndex={-1}
          >
            {preview.found ? 'Проверьте выбранную запись' : 'Запись не найдена в выбранном снимке'}
          </h4>
          <p>
            {preview.group.universityName} · {preview.group.title} · сезон {preview.group.year}
          </p>
          <p>Архив. Это не текущая кампания и не гарантия зачисления.</p>
          {preview.candidate && (
            <>
              <p>
                Строка официального списка: <strong>{preview.candidate.officialRank}</strong>.
                Баллы: {preview.candidate.score ?? 'неизвестно'}.
              </p>
              <p>
                Согласие в источнике:{' '}
                {preview.candidate.consent === null
                  ? 'неизвестно'
                  : preview.candidate.consent
                    ? 'да'
                    : 'нет'}
                . Приоритет: {preview.candidate.priority ?? 'неизвестно'}.
              </p>
              <p>
                Статус в снимке:{' '}
                {preview.candidate.participation === 'enrolled'
                  ? 'источник отмечает зачисление'
                  : preview.candidate.participation === 'unknown'
                    ? 'не подтверждён'
                    : preview.candidate.participation}
                .
              </p>
              <SourceProvenance group={preview.group} />
              <label className="source-ack">
                <Input
                  type="checkbox"
                  checked={acknowledged}
                  disabled={busy}
                  onChange={(event) => setAcknowledged(event.target.checked)}
                />
                Подтверждаю: выбраны нужные мне группа и запись
              </label>
              <p className="small-copy">
                Подтверждение сохраняет направление для просмотра. Оно не подаёт согласие на
                зачисление и не меняет данные вуза.
              </p>
              {expired && (
                <p role="status">
                  Срок подтверждения истёк.{' '}
                  {attempted
                    ? 'Если ответ сохранения потерян, можно безопасно повторить ту же попытку.'
                    : 'Найдите запись снова перед сохранением.'}
                </p>
              )}
              <Button
                variant="primary"
                type="button"

                disabled={!acknowledged || busy || (expired && !attempted)}
                onClick={saveRecord}
              >
                {save.isPending
                  ? 'Сохраняем…'
                  : save.isError
                    ? 'Повторить сохранение записи'
                    : 'Сохранить эту запись'}
              </Button>
            </>
          )}
          {!preview.found && (
            <p>
              Сверьте код, сезон и группу на официальном сайте. Отсутствие записи не означает отказ
              или отзыв заявления.
            </p>
          )}
        </Card>
      )}
      {save.isError && (
        <Alert
          as="p"
          role="alert"
        >
          {save.error.message}
        </Alert>
      )}
      {saved && (
        <p role="status">
          Архивное направление сохранено.{' '}
          <Link
            ref={savedLink}
            data-router-link
            to="/tracker"
          >
            Открыть мои направления →
          </Link>
        </p>
      )}
    </div>
  );
}
