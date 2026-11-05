# B17/T207 — независимая аттестация БГУ

2026-11-05. Все109оригинальных строк exact GET scope сверены вторым parser
на stdlib.HTMLParser. Он отдельно читает физические TD/внутренние spans,
проверяет109уникальных минимальных номеров, HMAC source/group/year по первым
5цифрам, полный порядок, общие баллы, null consent/priority,14явных enrollment
и программу. План20/объявленное число109 сверены независимо от основного decoder.

Evidence: `b17-bgu-audit.json`. Паспорт: `docs/sources/bgu2026.md`.
Новый immutable shard добавляет один профиль;14прежних profiles/proofs/shards
остаются неизменными. В runtime manifest теперь15scopes четырёх версий.
Это аттестация одного URL/настройки/архива2026, не всего сайта или POST.
Source в БД этим действием не включается, покрытие опубликованных импортов
ещё не изменено. Подготовительная scope-конфигурация сохраняет attested=false
как исторический вход, актуальное доказательство — паспорт/manifest/audit.

Оригинал private; fixture полностью synthetic для всех candidate values.
Повтор review/publish даёт прежние hashes/configuration, существующий профиль
нельзя незаметно заменить. Ни один минимальный номер, прочая часть кода,
scoped key или индивидуальные баллы не экспортированы в tracked audit.

46native targeted passed/0skipped(8.23s): новый proof/closed registry и тест
независимого обнаружения неверного score/key/enrollment/capacity; старые
профили/manifest, filtered отказы и atomic batch на расширенном реестре.
Проверки batch теперь используют длину manifest вместо прежней константы14.
