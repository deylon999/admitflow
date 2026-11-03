# Контракт загрузки

`backend/app/sources/fetcher.py` возвращает ограниченный сырой ответ, а не готовый конкурсный список. Он пока не подключён к публичному endpoint и не запускает сбор кандидатов из аудита.

- Конструктор получает allowlist от доверенного registry, не из пользовательского запроса. Только HTTPS/443, без credentials/fragment/control characters.
- DNS проверяется перед каждым переходом. Смешанный ответ с приватным/служебным адресом отклоняется. Соединение идёт непосредственно на проверенный IP; TLS/SNI проверяет исходный официальный hostname. Повторного DNS lookup при соединении нет.
- Не более трёх redirect, каждый проходит ту же политику. HTTP downgrade, внешний домен и private-IP redirect запрещены.
- По умолчанию лимит 5 MiB, socket timeout 10 секунд и дедлайн чтения тела. DNS использует системный resolver; общий предел задания и повторы задаются worker отдельно. Сжатие отклоняется, чтобы исключить неограниченную распаковку.
- Ошибки 401/403, challenge, 429, 5xx, неподдержанный MIME и пустой ответ не превращаются в список. Retry-After ограничен 30 секундами–24 часами. Функция сама не повторяет запрос.
- Возвращаются bytes, MIME/charset, hash и fetchedAt. Это не sourceUpdatedAt. Адаптер обязан проверить заголовки таблицы, идентичность группы/сезона, полноту и отсутствие страницы авторизации, в том числе при HTTP 200.
- Исключение содержит безопасный код и задержку, без URL/тела. Dataclass repr не выводит тело и query. Полные raw сохранять только закрыто и с retention из data-policy.

Основания TLS/HTTP: [Python http.client](https://docs.python.org/3.12/library/http.client.html), [Python ssl](https://docs.python.org/3.12/library/ssl.html). Перед аттестацией адаптера всё ещё требуется реальная загрузка и сверка. Синтетический transport в тестах доказывает ограничения кода, не доступность внешнего сайта.

B11 measured size: genuine SGU4588 response5851174bytes exceeds5MiB. Default fetch/capture remains5MiB; a frozen trusted Adapter may explicitly request max_bytes up to8MiB. The selected cap is validated before process spawn and after exchange metadata, before reading payload; hard cap8MiB is shared by raw storage/backup recovery. HTTP API input limits are unchanged.8MiB+1 and mismatched envelope/hash are refused; SSRF/redirect/DNS/TLS policies are unchanged. This size exception is code-defined per adapter,not supplied by user URL or API input.
