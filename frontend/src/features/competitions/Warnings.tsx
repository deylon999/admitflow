import { Surface } from '../../shared/UI';

const warningText: Record<string, string> = {
  archive: 'Архивный список прошлой кампании, не текущая ситуация.',
  incomplete_list: 'Список неполный: позиции могут быть неточными.',
  priorities_not_published: 'Источник не публикует приоритеты, поэтому они не показаны и не учитываются.',
  consent_unknown_rows: 'У части строк неизвестно согласие на зачисление.',
  rules_not_modelled: 'Для этого типа конкурса правила согласий и мест не моделируются: только факты списка.',
  seats_unknown: 'Источник не указал число мест.',
  source_stale: 'Источник давно не обновлялся.',
  source_source_error: 'Последняя загрузка источника завершилась ошибкой; показан последний корректный снимок.',
  source_quarantined: 'Новый снимок источника отклонён проверкой; показан последний корректный.',
};

export function Warnings({ codes }: { codes: string[] }) {
  if (!codes.length) return null;
  return <Surface tone="soft" title="Что важно знать об этом списке" className="af-competition-warnings">
    <ul>{codes.map(code => <li key={code}>{warningText[code] ?? code}</li>)}</ul>
  </Surface>;
}
