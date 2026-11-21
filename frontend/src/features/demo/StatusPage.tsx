import { Action, PageTitle, Surface } from '../../shared/UI';

export function StatusPage({ variant }: { variant: 'empty' | 'error' | 'success' }) {
  const map = {
    empty: ['Нет конкурсных списков', 'По выбранному направлению ещё не опубликованы данные.', '◎', 'soft' as const],
    error: ['Источник временно недоступен', 'Показываем дату последнего успешного обновления. Точный прогноз сейчас недоступен.', '!', 'orange' as const],
    success: ['Направление сохранено', 'Теперь ты можешь отслеживать программу в своём кабинете.', '✓', 'lime' as const],
  } as const;
  const [title, description, symbol, tone] = map[variant];
  return (
    <>
      <PageTitle kicker="СОСТОЯНИЕ ИНТЕРФЕЙСА" title={title} description={description} />
      <Surface tone={tone} className="af-state-panel"><div className="af-state-panel__symbol">{symbol}</div><h2>{title}</h2><p>{description}</p><Action to={variant === 'success' ? '/app/watchlist' : '/universities'}>{variant === 'success' ? 'Мои направления ↗' : 'Вернуться к каталогу ↗'}</Action></Surface>
    </>
  );
}
