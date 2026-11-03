# B12 — движение к зафиксированному рубежу70%

## T187 — семейство адаптеров и границы подключения

Registry разрешает одну версию parser с несколькими неизменяемыми Attestation. Каждый URL/year/kind имеет отдельный proof;неизвестный scope остаётся invalid_binding. Старый single-proof контракт сохранён для опубликованных версий. Повтор scope,чужой домен,неверная версия и отсутствие proof отвергаются. Это архитектурная возможность,а не новое покрытие сама по себе.

Проверка: `backend/.venv/bin/python -m pytest backend/tests/test_attestation.py backend/tests/test_registry_contract.py backend/tests/test_sgu_adapter.py -q` —38passed,exit0. Включён reuse одного callable для двух точных test scopes и отказ для неподтверждённого URL/сезона/live. Реальная проверка нескольких профилей — T188.
