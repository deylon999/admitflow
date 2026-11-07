import { Button, Alert } from '@/shared/ui';
import type { TrackerModel } from '../model/useTrackerModel';

export function TrackerHeading({ model }: { model: TrackerModel }) {
  const { expired, directionTotal, busy, privateVisible, editor } = model;
  return (
    <>
      <header className="tracker-page-heading">
        <div>
          <p className="eyebrow">Личный кабинет</p>
          <h1
            ref={editor.pageHeading}
            tabIndex={-1}
          >
            Мои направления
          </h1>
          <p className="section-description">Ваше место, последние изменения и следующий шаг.</p>
        </div>
        <Button
          variant="primary"
          ref={editor.addButton}
          type="button"
          disabled={
            expired ||
            directionTotal >= 20 ||
            busy ||
            model.budget.isPending ||
            model.budget.isError
          }
          onClick={(event) => editor.openForm('new', event.currentTarget)}
        >
          Добавить направление
        </Button>
      </header>
      {privateVisible && (
        <p className="tracker-safety-note">
          Направления доступны только в этом браузере до окончания гостевого доступа. Очистка
          cookies приведёт к потере доступа. Сохраните копию в «Дополнительных инструментах».
        </p>
      )}
      {privateVisible && directionTotal >= 20 && (
        <Alert
          as="p"
          tone="warning"
        >
          Сохранено 20 направлений — это максимум. Удалите ненужное, чтобы добавить новое.
        </Alert>
      )}
    </>
  );
}
