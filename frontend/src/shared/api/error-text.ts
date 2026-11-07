import { ApiError, InvalidResponseError } from './errors';
import { RequestTimeoutError } from './transport';

/** Safe display copy for read failures; field validation stays with its form. */
export function requestErrorText(error: unknown) {
  if (error instanceof InvalidResponseError)
    return 'Не удалось проверить полученные данные. Попробуйте ещё раз.';
  if (error instanceof RequestTimeoutError)
    return 'Ответ занимает слишком много времени. Попробуйте ещё раз.';
  if (error instanceof ApiError) {
    if (error.status === 429) return 'Слишком много запросов. Подождите немного и повторите.';
    if (error.status >= 500) return 'Сервис временно недоступен. Попробуйте ещё раз чуть позже.';
  }
  return error instanceof Error ? error.message : 'Проверьте соединение и попробуйте ещё раз.';
}
