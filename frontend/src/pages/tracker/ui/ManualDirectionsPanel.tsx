import { DirectionForm } from '@/features/edit-manual-direction';
import { DirectionCard } from './DirectionCard';
import type { TrackerModel } from '../model/useTrackerModel';

function errorText(error: unknown) {
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.';
}

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
          {!privateVisible ? null : watches.isPending ? (
            <div
              className="empty-state surface"
              role="status"
            >
              <h2>Загружаем направления…</h2>
              <p>Проверяем сохранённые данные.</p>
            </div>
          ) : watches.isError && !watches.data ? (
            <div
              className="empty-state surface"
              role="alert"
            >
              <h2>Не удалось загрузить направления</h2>
              <p>{errorText(watches.error)}</p>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => void watches.refetch()}
              >
                Повторить
              </button>
            </div>
          ) : count === 0 ? (
            <div className="empty-state surface">
              <span
                className="empty-mark"
                aria-hidden="true"
              >
                ＋
              </span>
              <h2>{directionTotal ? 'Ручных направлений пока нет' : 'Направлений пока нет'}</h2>
              <p>
                Добавьте вуз, направление и ссылку на список. Введите текущие цифры — сервис
                сохранит расчёт и его историю.
              </p>
              <button
                className="button button-primary"
                type="button"
                disabled={directionTotal >= 20 || busy}
                onClick={(event) => openForm('new', event.currentTarget)}
              >
                Добавить первое направление
              </button>
            </div>
          ) : visible.length === 0 ? (
            <div className="surface empty-state">
              <h2>Поиск не дал результатов</h2>
              <p>
                Измените запрос или сбросьте фильтры. Сохранённые направления остаются в кабинете.
              </p>
            </div>
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
