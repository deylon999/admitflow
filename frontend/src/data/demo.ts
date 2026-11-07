/** Demonstration fixture. None of these forecasts are trained model outputs. */
export type ChanceLabel = 'Высокие' | 'Средние' | 'Низкие';
export type Program = {
  id: string;
  university: string;
  universityFull: string;
  program: string;
  code: string;
  city: string;
  budget: number;
  score2025: number;
  expected: [number, number];
  chance: number;
  position: number;
  applicants: number;
  color: 'blue' | 'orange' | 'violet' | 'lime';
  subject: string;
  status: ChanceLabel;
};

export const programs: Program[] = [
  { id: 'mtuci-se', university: 'МТУСИ', universityFull: 'Московский технический университет связи и информатики', program: 'Программная инженерия', code: '09.03.04', city: 'Москва', budget: 90, score2025: 288, expected: [276, 284], chance: 74, position: 90, applicants: 128, color: 'blue', subject: 'Информатика', status: 'Высокие' },
  { id: 'mirea-cs', university: 'РТУ МИРЭА', universityFull: 'МИРЭА — Российский технологический университет', program: 'Информатика и вычислительная техника', code: '09.03.01', city: 'Москва', budget: 120, score2025: 283, expected: [272, 289], chance: 67, position: 93, applicants: 184, color: 'violet', subject: 'Информатика', status: 'Средние' },
  { id: 'mei-ai', university: 'НИУ МЭИ', universityFull: 'Национальный исследовательский университет «МЭИ»', program: 'Прикладная информатика', code: '09.03.03', city: 'Москва', budget: 80, score2025: 268, expected: [254, 267], chance: 91, position: 22, applicants: 110, color: 'orange', subject: 'Информатика', status: 'Высокие' },
  { id: 'itmo-se', university: 'ИТМО', universityFull: 'Национальный исследовательский университет ИТМО', program: 'Программная инженерия', code: '09.03.04', city: 'Санкт-Петербург', budget: 46, score2025: 301, expected: [293, 305], chance: 32, position: 143, applicants: 329, color: 'blue', subject: 'Информатика', status: 'Низкие' },
  { id: 'hse-cs', university: 'НИУ ВШЭ', universityFull: 'Национальный исследовательский университет «Высшая школа экономики»', program: 'Компьютерные науки и анализ данных', code: '01.03.02', city: 'Москва', budget: 70, score2025: 306, expected: [298, 310], chance: 19, position: 180, applicants: 402, color: 'lime', subject: 'Информатика', status: 'Низкие' },
  { id: 'bmstu-ib', university: 'МГТУ им. Баумана', universityFull: 'Московский государственный технический университет имени Н. Э. Баумана', program: 'Информационная безопасность', code: '10.03.01', city: 'Москва', budget: 100, score2025: 290, expected: [275, 292], chance: 58, position: 104, applicants: 210, color: 'orange', subject: 'Информатика', status: 'Средние' },
];

export const reviews = [
  { at: '11:20, сегодня', title: 'Позиция улучшилась', detail: 'Позиция в списке: 94 → 90', kind: 'up' },
  { at: '19:40, вчера', title: 'Новые заявления', detail: 'В источнике добавлены участники', kind: 'new' },
  { at: '3 дня назад', title: 'Обновились показатели ЕГЭ', detail: 'Изменился сценарный диапазон', kind: 'model' },
  { at: '7 дней назад', title: 'Добавлено направление', detail: 'Началось отслеживание', kind: 'save' },
];

/** Illustration only: each year's group shares add to 100%. Not official EGE data. */
export const examDistributionBySubject = {
  'Информатика': [
    { group: '0–20', previous: 5, current: 3 },
    { group: '21–40', previous: 10, current: 7 },
    { group: '41–60', previous: 18, current: 13 },
    { group: '61–70', previous: 25, current: 21 },
    { group: '71–80', previous: 22, current: 23 },
    { group: '81–90', previous: 14, current: 23 },
    { group: '91–100', previous: 6, current: 10 },
  ],
  'Математика': [
    { group: '0–20', previous: 3, current: 4 },
    { group: '21–40', previous: 8, current: 11 },
    { group: '41–60', previous: 16, current: 20 },
    { group: '61–70', previous: 22, current: 24 },
    { group: '71–80', previous: 27, current: 22 },
    { group: '81–90', previous: 17, current: 13 },
    { group: '91–100', previous: 7, current: 6 },
  ],
  'Русский язык': [
    { group: '0–20', previous: 1, current: 1 },
    { group: '21–40', previous: 4, current: 5 },
    { group: '41–60', previous: 13, current: 14 },
    { group: '61–70', previous: 23, current: 22 },
    { group: '71–80', previous: 29, current: 29 },
    { group: '81–90', previous: 22, current: 22 },
    { group: '91–100', previous: 8, current: 7 },
  ],
} as const;

export const applicantRows = Array.from({ length: 13 }, (_, i) => ({
  position: 84 + i,
  id: i === 6 ? 'ВЫ' : `ID-${String(8024 + i * 37)}`,
  score: i === 6 ? 285 : 291 - Math.floor(i / 2),
  priority: 1 + (i % 3),
  status: i === 6 ? 'Ваше заявление' : i % 4 === 0 ? 'Есть подтверждение' : 'В конкурсе',
}));
