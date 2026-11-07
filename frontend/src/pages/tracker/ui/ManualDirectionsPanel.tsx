import { Card, Alert, Button } from '@/shared/ui';
import { DirectionForm } from '@/features/edit-manual-direction';
import { DirectionCard } from './DirectionCard';
import { requestErrorText } from '@/shared/api';
import type { TrackerModel } from '../model/useTrackerModel';

export function ManualDirectionsPanel({ model }: { model: TrackerModel }) {
  const {
    privateVisible,
    watches,
    count,
    directionTotal,
    busy,
    visible,
    sessionInfo,
    setNotice,
    editor,
    archive,
    directionsLoading,
    directionsError,
    directionsEmpty,
  } = model;
  const {
    form,
    restored,
    focusRequest,
    openForm,
    closeForm,
    canDiscard,
    addButton,
    setDraftDirty,
  } = editor;
  return (
    <>
      <div className={`tracker-layout ${form && privateVisible ? 'with-form' : ''}`}>
        <div className="directions-list">
          {!privateVisible ? null : directionsError ? (
            <Alert
              className="empty-state surface"
              role="alert"
            >
              <h2>Не удалось загрузить направления</h2>
              <p>{requestErrorText(watches.error ?? archive.error)}</p>
              <Button
                type="button"
                disabled={watches.isFetching || archive.isFetching}
                onClick={() => void model.refreshDirections()}
              >
                {watches.isFetching || archive.isFetching ? 'Повторяем загрузку…' : 'Повторить'}
              </Button>
            </Alert>
          ) : directionsLoading ? (
            <Card
              className="empty-state"
              role="status"
            >
              <h2>Загружаем направления…</h2>
              <p>Проверяем сохранённые данные.</p>
            </Card>
          ) : directionsEmpty ? (
            <Card className="empty-state">
              <span
                className="empty-mark"
                aria-hidden="true"
              >
                ＋
              </span>
              <h2>Направлений пока нет</h2>
              <p>
                Добавьте вуз, направление и ссылку на список. Введите текущие цифры — сервис
                сохранит расчёт и его историю.
              </p>
              <Button
                variant="primary"

                type="button"
                disabled={
                  directionTotal >= 20 || busy || model.budget.isPending || model.budget.isError
                }
                onClick={(event) => openForm('new', event.currentTarget)}
              >
                Добавить направление
              </Button>
            </Card>
          ) : count === 0 ? null : visible.length === 0 ? (
            <Card className="empty-state">
              <h2>Поиск не дал результатов</h2>
              <p>
                Измените запрос или сбросьте фильтры. Сохранённые направления остаются в кабинете.
              </p>
            </Card>
          ) : (
            visible.map((watch) => (
              <DirectionCard
                key={watch.id}
                watch={watch}
                disabled={busy}
                onEdit={(button) => openForm(watch, button)}
                beforeDelete={() =>
                  form === null || form === 'new' || form.id !== watch.id || canDiscard()
                }
                onRemoved={() => {
                  if (form && form !== 'new' && form.id === watch.id) closeForm(true);
                  setNotice('Направление удалено.');
                  requestAnimationFrame(() => addButton.current?.focus());
                }}
              />
            ))
          )}
        </div>
        {form && privateVisible && (
          <aside className="tracker-sidebar">
            <DirectionForm
              restored={restored}
              sessionInfo={sessionInfo.data}
              disabled={busy}
              key={form === 'new' ? 'new' : form.id}
              focusRequest={focusRequest}
              watch={form === 'new' ? undefined : form}
              onDirtyChange={setDraftDirty}
              onCancel={() => closeForm()}
              onDone={() => {
                closeForm(true);
                setNotice('Данные сохранены. Расчёт и история обновлены.');
              }}
            />
          </aside>
        )}
      </div>
    </>
  );
}
