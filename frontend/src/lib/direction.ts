import { calculatePlace } from './calculator';
import type { CalculationForm } from './calculator';

export type DirectionDraft = { university: string; title: string; sourceUrl: string; values: CalculationForm };
export type MetadataErrors = Partial<Record<'university' | 'title' | 'sourceUrl', string>>;
const inputIds = { rank: 'tracker-rank', seats: 'tracker-seats', excluded: 'tracker-excluded', noConsent: 'tracker-no-consent' } as const;

export function draftSignature(draft: DirectionDraft): string {
  return JSON.stringify([draft.university, draft.title, draft.sourceUrl, ...(['rank', 'seats', 'excluded', 'noConsent'] as const).map(field => String(draft.values[field]))]);
}

export function validateDirection(draft: DirectionDraft, editing = false) {
  const metadata: MetadataErrors = {};
  if (!editing) {
    if (!draft.university.trim() || draft.university.trim().length > 160) metadata.university = 'Введите название вуза, до 160 символов.';
    if (!draft.title.trim() || draft.title.trim().length > 200) metadata.title = 'Введите направление и конкурсную группу, до 200 символов.';
    try {
      const url = new URL(draft.sourceUrl.trim());
      if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password || url.href.length > 2048 || /[\u0000-\u001f\u007f]/.test(draft.sourceUrl)) throw new Error();
    } catch { metadata.sourceUrl = 'Введите ссылку http:// или https:// без логина и пароля, до 2048 символов.'; }
  }
  const result = calculatePlace(draft.values);
  const calculation = 'error' in result ? result : undefined;
  const firstInvalidId = metadata.university ? 'university' : metadata.title ? 'direction-title' : metadata.sourceUrl ? 'source-url' : calculation ? inputIds[calculation.fields[0]] : undefined;
  return { metadata, calculation, firstInvalidId };
}
