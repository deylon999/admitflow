# T197 — масштабируемый реестр проверенных профилей

2026-11-05. Один reviewed.json с пределом100 заменён активным catalog.json manifest и content-addressed JSON shards по версиям parser. Текущие3 проверенных профиля находятся в2 shards. Legacy reviewed.json сохранён; все прежние TableProfile/Attestation/binding значения совпадают до и после упаковки.

Manifest публикуется атомарно после валидации всех профилей и записи файлов. Старые shards не удаляются, проверенные профили нельзя потерять или переписать при повторной публикации. Hash не является внешней подписью или заменой независимой аттестации: это проверка целостности доверенного deployment artifact. Corrupt manifest не приводит к fallback на старый файл. Legacy fallback доступен только при отсутствии manifest.

Ограничения: до20000профилей,512shards,100профилей/1MiB на shard,64MiB суммарно,256KiB manifest. Escape paths, symlinks, duplicate JSON keys/IDs/URLs одной версии, wrong counts, hash corruption, отсутствующие/несовместимые proofs и попытки удалить старый scope отклоняются. Старые версии V1/V2 сохраняются. Это проверенный шаг масштабирования, не утверждение неограниченной нагрузки или20000подключённых источников.

Проверки:1001 synthetic fixtures.invalid profiles в11shards успешно загружены; repeat packaging идентичен. Linux/native PostgreSQL target run `pytest -q --require-postgres tests/test_profile_catalog.py tests/test_table_family.py tests/test_attestation.py tests/test_reviewed_sources.py tests/test_next_scope.py`: **48 passed,0skipped,14.64s**. Native worker/owner API проверили прежние источники обоих вузов и новый scope после загрузки manifest. Реальных источников этим шагом не добавлено.

Команда из корня: `backend/.venv/Scripts/python.exe scripts/pack_profiles.py`. По умолчанию переупаковывается текущий active catalog, не устаревший legacy. scripts/review_sgu_scope.py также сохраняет новый профиль через manifest, не теряя другие семейства. Применение к работающему API/worker требует перезапуска с новой поставкой.
