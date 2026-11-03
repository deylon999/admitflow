# B12 — движение к зафиксированному рубежу70%

## T187 — семейство адаптеров и границы подключения

Registry разрешает одну версию parser с несколькими неизменяемыми Attestation. Каждый URL/year/kind имеет отдельный proof;неизвестный scope остаётся invalid_binding. Старый single-proof контракт сохранён для опубликованных версий. Повтор scope,чужой домен,неверная версия и отсутствие proof отвергаются. Это архитектурная возможность,а не новое покрытие сама по себе.

Проверка: `backend/.venv/bin/python -m pytest backend/tests/test_attestation.py backend/tests/test_registry_contract.py backend/tests/test_sgu_adapter.py -q` —38passed,exit0. Включён reuse одного callable для двух точных test scopes и отказ для неподтверждённого URL/сезона/live. Реальная проверка нескольких профилей — T188.

## T188 — один parser для двух настоящих форматов

Один parse_table декодирует SGU573строки и GUAP581строку через JSONпрофили backend/app/sources/profiles/reviewed.json. Отличия rowselector,labels/positions,headers,metadata,codecприоритета и enrollment suffix заданы данными;новый алгоритм на вуз не написан. LegacySGUparser/version сохранены для старых снимков. Профили пока не включены автоматически в Source/worker.

Независимые stdlib HTMLParser audit обоих приватных оригиналов сверили все1154строки,порядок/баллы/согласие/приоритет/статус/HMAC и границы16/17 и0/1. Reports b12-sgu-family-audit.json,b12-guap-family-audit.json. GUAP:платный конкурс,явные0мест,581unknownconsent,92явныхenrolled;договор/оплата не трактуются как согласие. DerivedDOM180023bytes заменяет только ID,сохраняет остальные14cells/статусы;manifest содержит hashes/преобразования. Реальные коды не включены вGit.

Текущие targetedchecks:22passed (7family+15attestation),exit0. Проверены source/year/group/URL/kind scope,два макета,одинаковые FIXTUREкоды в разных источниках,обрезанная таблица,неверный HTMLсезон и duplicateidentity. Более ранний registry/legacy набор38passed. Отдельные SGU4570/4576 иGUAPphysics вернули только заголовки,не подтверждены как пустые и не подключаются. Два доступных оригинала относятся к разным университетам;структурный reuse доказан ими,национальное покрытие не заявлено.
