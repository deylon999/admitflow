import { Card, Button, Input, Alert } from '@/shared/ui';
import { requestErrorText } from '@/shared/api';
import { CalculationInputs } from '@/entities/manual-direction';
import { UniversityPicker } from '@/entities/university';
import { useDirectionForm } from '../model/useDirectionForm';
import type { DirectionFormProps } from '../model/useDirectionForm';

export function DirectionForm(props: DirectionFormProps) {
  const { watch, disabled, onCancel } = props;
  const {
    heading,
    values,
    setValues,
    university,
    setUniversity,
    title,
    setTitle,
    sourceUrl,
    setSourceUrl,
    submitted,
    result,
    error,
    metadata,
    save,
    localSaved,
    submit,
  } = useDirectionForm(props);
  return (
    <Card
      as="form"
      className="direction-form"
      noValidate
      aria-labelledby="direction-form-heading"
      aria-describedby="direction-form-intro"
      aria-busy={save.isPending}
      onKeyDown={(event) => {
        if (event.key === 'Escape' && !event.defaultPrevented && !save.isPending) {
          event.preventDefault();
          onCancel();
        }
      }}
      onSubmit={submit}
    >
      <div className="tracker-form-heading">
        <h2
          id="direction-form-heading"
          ref={heading}
          tabIndex={-1}
        >
          {watch ? 'Обновить цифры' : 'Добавить направление'}
        </h2>
        <Button
          variant="ghost"
          type="button"
          onClick={onCancel}
          aria-label="Закрыть форму"
          disabled={save.isPending}
        >
          ✕
        </Button>
      </div>
      <p
        id="direction-form-intro"
        className="direction-form-intro"
      >
        {watch
          ? 'Введите свежие числа из списка. Новый расчёт добавится в историю, прежние сохранятся.'
          : 'Перенесите данные из конкурсного списка вуза. Сохраним направление и расчёт, чтобы вы могли следить за изменениями.'}
      </p>
      <p className="form-note direction-required-note">
        Все поля обязательны.{!watch && ' Выбор вуза из подсказок можно пропустить.'}
      </p>
      <fieldset
        className="direction-fields"
        disabled={save.isPending || disabled}
      >
        <legend className="visually-hidden">Данные направления</legend>
        {watch ? (
          <div className="direction-context">
            <dl>
              <dt>Вуз</dt>
              <dd>{watch.university}</dd>
              <dt>Направление</dt>
              <dd>{watch.title}</dd>
            </dl>
            <a
              href={watch.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              Открыть список вуза ↗
            </a>
          </div>
        ) : (
          <fieldset className="direction-section">
            <legend>Вуз и направление</legend>
            <UniversityPicker
              value={university}
              onChange={setUniversity}
              error={metadata.university}
              onSelect={(item) => {
                setUniversity(item.name);
                setSourceUrl(item.catalogOrigin === 'monitoring' ? '' : item.provenanceUrl);
              }}
            />
            <div className="field">
              <label htmlFor="direction-title">Направление</label>
              <Input
                id="direction-title"
                value={title}
                required
                aria-invalid={Boolean(metadata.title) || undefined}
                aria-describedby={`direction-title-hint${metadata.title ? ' direction-title-error' : ''}`}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Например: программная инженерия, очно, общий конкурс"
              />
              <p
                id="direction-title-hint"
                className="form-note"
              >
                Укажите название, форму обучения и конкурс из списка вуза. Общий конкурс и квота —
                разные группы.
              </p>
              {metadata.title && (
                <Alert
                  as="p"
                  id="direction-title-error"
                  className="form-error"
                  role="alert"
                >
                  Укажите направление и условия конкурса в одну строку, до 200 символов.
                </Alert>
              )}
            </div>
            <div className="field">
              <label htmlFor="source-url">Ссылка на конкурсный список</label>
              <Input
                id="source-url"
                type="url"
                value={sourceUrl}
                maxLength={2048}
                required
                aria-invalid={Boolean(metadata.sourceUrl) || undefined}
                aria-describedby={`source-url-hint${metadata.sourceUrl ? ' source-url-error' : ''}`}
                onChange={(event) => setSourceUrl(event.target.value)}
                placeholder="https://example.ru/abiturient/lists"
              />
              <p
                id="source-url-hint"
                className="form-note"
              >
                Скопируйте адрес списка из браузера. Цифры по ссылке автоматически не загружаются.
              </p>
              {metadata.sourceUrl && (
                <Alert
                  as="p"
                  id="source-url-error"
                  className="form-error"
                  role="alert"
                >
                  Введите ссылку http:// или https:// без логина и пароля, до 2048 символов.
                </Alert>
              )}
            </div>
          </fieldset>
        )}
        <CalculationInputs
          values={values}
          onChange={setValues}
          error={submitted ? error : undefined}
          prefix="tracker-"
          withGuidance
        />
      </fieldset>
      {!('error' in result) && (
        <div className="direction-preview-block">
          <div className="tracker-preview">
            <span>Расчётное место</span>
            <strong>
              {result.place} <small>из {result.seats}</small>
            </strong>
          </div>
          <p className="form-note">По введённым цифрам. Расчёт не гарантирует зачисление.</p>
        </div>
      )}
      {save.isError && (
        <Alert
          className="form-error direction-save-error"
          role="alert"
        >
          <p>
            <strong>Не удалось подтвердить сохранение.</strong> {requestErrorText(save.error)}
          </p>
          <p>Введённые данные остались в форме. Проверьте сообщение и повторите сохранение.</p>
        </Alert>
      )}
      {save.isPending && (
        <p
          className="form-note"
          role="status"
        >
          Сохраняем направление… Дождитесь результата перед уходом со страницы.
        </p>
      )}
      {disabled && !save.isPending && (
        <p
          className="form-note"
          role="status"
        >
          Дождитесь завершения текущей операции. Введённые данные сохранены в форме.
        </p>
      )}
      <div className="direction-form-actions">
        <Button
          variant="primary"
          type="submit"
          disabled={save.isPending || disabled}
        >
          {save.isPending ? 'Сохраняем…' : watch ? 'Сохранить обновление' : 'Сохранить направление'}
        </Button>
        <Button
          variant="ghost"
          type="button"
          disabled={save.isPending}
          onClick={onCancel}
        >
          Отмена
        </Button>
      </div>
      <p className="form-note direction-save-note">
        {watch
          ? 'Обновим карточку направления и добавим запись в историю.'
          : 'Создадим карточку направления с первым расчётом и историей обновлений.'}{' '}
        Дальше цифры обновляете вы — по списку вуза.
      </p>
      {localSaved === true && (
        <p
          className="form-note direction-draft-note"
          role="status"
        >
          Черновик сохранён в этой вкладке на 30 минут, не дольше срока доступа. Чтобы сохранить
          направление, нажмите кнопку выше.
        </p>
      )}
      {localSaved === false && (
        <Alert
          as="p"
          className="form-error"
          role="status"
        >
          Не удалось сохранить черновик в этой вкладке. Ввод остаётся в форме. Сохраните направление
          перед уходом.
        </Alert>
      )}
      {localSaved === 'clear-failed' && (
        <Alert
          as="p"
          className="form-error"
          role="status"
        >
          Не удалось удалить черновик в этой вкладке. Сохраните направление перед уходом.
        </Alert>
      )}
    </Card>
  );
}
