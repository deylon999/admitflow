# KAN-214 — внешняя проверка доставки и HTTPS

Это процедура для владельца тестового окружения, а не выполненная проверка.
На S215 провайдер/ящик/domain не предоставлены; результат **NOT VERIFIED**.
Без реальной inbox-доставки либо отдельного явного документированного решения
владельца KAN-214 не получает полную приёмку. SMTP250, mock или зелёный CI недостаточны.

1. Подготовить отдельное staging HTTPS окружение и disposable аккаунт с адресом,
   которым владеет проверяющий. Production-пользователей/базу для теста не использовать.
   Настройки и credentials — в закрытом secret store окружения, не в Git/чате/логе.
2. Согласовать deployment с ответственным за CI/CD. Текущий compose.prod не
   передаёт AUTH_ENABLED/AUTH_RATE_KEY/SMTP_* backend и не предоставляет ему egress.
   Минимальный вариант: reviewed overlay только для backend; стабильный rate key,
   полная TLS SMTP конфигурация, allowlisted SMTP egress, HTTPS PUBLIC_ORIGIN и
   точные ALLOWED_HOSTS. Не менять worker/catalog/import или PostgreSQL volumes.
   Не включать auth простой заменой флага без полного deployment-контракта.
3. Проверить trusted-proxy границу: внешний клиент не может подделать адрес через
   X-Forwarded-For/X-Real-IP. Сейчас auth использует peer и за nginx видит агрегат.
   Это не настоящие независимые IP-лимиты и может блокировать других пользователей.
   До принятия реальной схемы proxy/лимитов включение production auth не подтверждено.
4. В приватном окне браузера убедиться в HTTPS и корректном Origin, CSP/Referrer-Policy
   и HSTS; access/refresh/context cookies должны иметь Secure, HttpOnly, Lax,
   точные Path, без Domain. Не экспортировать HAR, cookies, trace/video или скриншоты
   со ссылками/паролями. Не ослаблять production-настройки для smoke.
5. Зарегистрировать новый адрес с длинной уникальной фразой. UI202 означает только
   условно принятый запрос. Проверить и SMTP acceptance у провайдера, и фактическое
   письмо в контролируемом ящике (включая Спам). До подтверждения login запрещён.
   Провайдер/письмо не должны содержать пароль, access/refresh credentials.
6. Сверить origin и /auth/verify в письме. После открытия fragment должен исчезнуть
   из URL до auth API. Явно подтвердить email; затем login/reload должны показывать
   серверно подтверждённый аккаунт. Повтор ссылки отклоняется; авто-входа нет.
7. Проверить expiry/refresh в двух вкладках на тестовой сессии (обычный access15мин,
   без уменьшения security-параметров). Logout очищает состояние во второй вкладке,
   reload не восстанавливает отозванный аккаунт. Гостевые направления сохранены.
8. Запросить recovery. Проверить отдельную фактическую доставку. Открыть /auth/reset,
   установить новый пароль; автоматического входа нет. Новый пароль работает,
   старый и предыдущие сессии — нет; повтор recovery-ссылки отклоняется.
9. Проверить отказ провайдера на staging контролируемым способом: функция должна
   явно вернуть503 без утверждения об отправке/создании аккаунта. Восстановить
   конфигурацию; повторная отправка подчиняется лимитам. Production secrets не менять.
10. Сохранить только redacted результат: дата/версия/SHA/проверяющий, staging origin,
    transport mode, verification/recovery acceptance и inbox delivery отдельно,
    cookie/header checks и ссылки на закрытые подтверждения провайдера. Не публиковать
    recipient, message body/action URL, passwords, tokens или cookies в evidence.
    После review владелец принимает gate либо явно фиксирует исключение и его границы.

Шаблон итоговой записи (заполнять фактическими результатами):

```json
{
  "sourceSha": "<checked commit>",
  "environment": "isolated-staging",
  "verificationInboxDelivery": "NOT_VERIFIED",
  "recoveryInboxDelivery": "NOT_VERIFIED",
  "httpsCookieOriginChecks": "NOT_VERIFIED",
  "trustedProxyAndEgress": "NOT_VERIFIED",
  "evidenceReference": "<private redacted evidence reference>",
  "ownerDecision": "PENDING"
}
```

Этот шаблон не означает разрешения менять production secrets, networks или данные.
