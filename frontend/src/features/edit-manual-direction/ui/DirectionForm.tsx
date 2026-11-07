import { Card, Button, Input, Alert } from '@/shared/ui';
import { CalculationInputs } from '@/entities/manual-direction';
import { UniversityPicker } from '@/entities/university';
import { useDirectionForm } from '../model/useDirectionForm';
import type { DirectionFormProps } from '../model/useDirectionForm';

function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

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
      <fieldset
        className="direction-fields"
        disabled={save.isPending || disabled}
      >
        <legend className="visually-hidden">Данные направления</legend>
        {watch ? (
          <p className="small-copy">
            {watch.university} · {watch.title}
          </p>
        ) : (
          <>
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
              <label htmlFor="direction-title">Направление и конкурсная группа</label>
              <Input
                id="direction-title"
                value={title}
                required
                aria-invalid={Boolean(metadata.title) || undefined}
                aria-describedby={metadata.title ? 'direction-title-error' : undefined}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Например: информатика, общий конкурс"
              />
              {metadata.title && (
                <Alert
                  as="p"
                  id="direction-title-error"
                  className="form-error"
                  role="alert"
                >
                  {metadata.title}
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
                aria-describedby={metadata.sourceUrl ? 'source-url-error' : undefined}
                onChange={(event) => setSourceUrl(event.target.value)}
                placeholder="https://…"
              />
              {metadata.sourceUrl && (
                <Alert
                  as="p"
                  id="source-url-error"
                  className="form-error"
                  role="alert"
                >
                  {metadata.sourceUrl}
                </Alert>
              )}
            </div>
          </>
        )}
        <div className="tracker-number-fields">
          <CalculationInputs
            values={values}
            onChange={setValues}
            error={submitted ? error : undefined}
            prefix="tracker-"
          />
        </div>
      </fieldset>
      <p className="form-note">
        Берите данные одной конкурсной группы. Каждый человек выше вас учитывается только в одной из
        двух вычитаемых групп.
      </p>
      {!('error' in result) && (
        <div className="tracker-preview">
          <span>Место по введённым данным</span>
          <strong>
            {result.place} <small>из {result.seats}</small>
          </strong>
        </div>
      )}
      {submitted && error && (
        <Alert
          as="p"
          className="form-error"
          id="tracker-calculation-error"
          role="alert"
        >
          {error.error}
        </Alert>
      )}
      {save.isError && (
        <Alert
          as="p"
          className="form-error"
          role="alert"
        >
          {errorText(save.error)}
        </Alert>
      )}
      {save.isPending && (
        <p role="status">Дождитесь результата сохранения перед переходом на другую страницу.</p>
      )}
      {disabled && !save.isPending && (
        <p role="status">Дождитесь завершения текущей операции. Поля формы сохранены.</p>
      )}
      {localSaved === true && (
        <p
          className="form-note"
          role="status"
        >
          Черновик сохранён в этой вкладке на 30 минут, не дольше гостевого доступа. Это не
          подтверждение сохранения направления на сервере.
        </p>
      )}
      {localSaved === false && (
        <Alert
          as="p"
          className="form-error"
          role="status"
        >
          Не удалось сохранить черновик в этой вкладке. Сохраните направление перед уходом.
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
      <Button
        variant="primary"

        type="submit"
        disabled={save.isPending || disabled}
      >
        {save.isPending ? 'Сохраняем…' : watch ? 'Сохранить обновление' : 'Сохранить направление'}
      </Button>
      <p className="form-note">
        Числа сохраняются вручную. Сервис не запрашивает список по указанной ссылке.
      </p>
    </Card>
  );
}
