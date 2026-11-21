import { Action, EmptyMessage } from '../shared/UI';

export function NotFound() {
  return <EmptyMessage title="Такой страницы нет" description="Проверь адрес или перейди к каталогу." action={<Action to="/universities">Каталог ↗</Action>} />;
}
