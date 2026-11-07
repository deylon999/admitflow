export class InvalidResponseError extends Error {
  constructor() {
    super('Сервер вернул некорректные данные. Расчёт не показан — попробуйте обновить страницу.');
  }
}

export class SessionExpiredError extends Error {
  constructor() {
    super(
      'Срок доступа истёк или данные браузера были удалены. Начните новую сессию, чтобы сохранять направления снова.',
    );
  }
}
export class SessionChangedError extends Error {
  constructor() {
    super('Доступ изменился во время запроса. Синхронизируйте текущую сессию.');
  }
}
