# B11 —30 задач,2026-11-03

Основа2c866bd, clean Git. Шесть подходов по5; отдельный Conventional Commit/acceptance/evidence на задачу. Первые5: T019,T007,T008,T013,T027. Дальнейший выбор по реальным зависимостям/оригиналам; release gates не сокращаются. Все source original bytes приватны в ignored backend/var, реальные публичные ID в Git не добавляются.

Новое основание исследований: capture СГУПС1348 успешен, attested=false/archive2026. Capture СГУ4588 отказал response_too_large; отдельное офлайн-исследование ограничено20MiB, production limit5MiB не меняется. Предыдущий preview остановлен вне этой сессии; новый изолированный admitflow-b11/8090 поднимается из B10 images, пользовательские volumes не переиспользуются.

## 1/30 T019

Ручная приёмка сведена в manual-acceptance.md. Текущий targeted Chromium10/10 на новом PostgreSQL/nginx8090,exit0; предыдущие native restart/ownership/limits/replay доказательства проверены и применимы к неизменённому коду. Не реализованные automatic карточки не закрыты. Плановые deliverables исправлены на реальные файлы тестов.

## 2/30 T007

Локально vendored13 variable normal WOFF2 subsets Inter/JetBrains Mono из Fontsource5.3.0,304756bytes, обе OFL лицензии, provenance и SHA256 manifest. Внешний Google CSS import удалён. Actual FontFace Latin/Cyrillic600 загружаются со своего origin с запретом всех внешних запросов; тест проверяет loaded,2+faces/family,manifest/лицензии200. Fresh preview build + fonts/landing:5 passed,exit0,7.5s. Четыре исходных PNG визуально прочитаны; tokens в styles.css используют правильные families и light/dark hierarchy. Визуальные расхождения/размеры подробно относятся к T008.

При завершении T019 validator поймал nextTask=T007 со старым blocked status. Устранён уже неактуальный font-network blocker, T007 назначена in_progress; приватный незапубликованный T019 commit исправлен до реализации fonts,render/check снова валидны. Опубликованная история не менялась.

## 3/30 T008

Все4 original/current PNG просмотрены, основные6 цветов каждой темы совпадают с измеренными пикселями originals.4 screenshots с actual local fonts сохранены; visual.md перечисляет отличия принятого copy/manual states/дополнительной высоты/видимого focus cue. Добавлена1024px проверка; landing+fonts6 passed,exit0,320–1440/две темы. Pixel-identical или вся T026/T045 не заявлены.

## 4/30 T013

Получены genuine SGU/STU originals. Derived SGU573-row DOM fixture с manifest,SHA256/OFL-neutral provenance и privacy transform; оригинальныеIDs не остались. Sanitizer сохранил все573retained non-identifier rows точно,deterministic rerun unchanged. Missing/login/header/encoding/oversize/capture corruption cases:9passed,exit0. Ошибка sanitizer при удалённом active ancestor исправлена до создания fixture; первичный test missing fixture зафиксирован как setup failure,после исправления9/9. Original dirs700/files600,raw не вGit. STU headers-only не выдан за confirmed-empty; registry остаётся пуст. Source passport обновлён. Offline8MiB inspection не меняет production5MiB limit.

## 5/30 T027

Контракт закрыт на genuine fixtures: frozen explicit Attestation привязывает паспорт/fixture+original hashes,exact URL/year/kind/version,date и минимум50проверенных строк(либо весь меньший непустой sample). Голый attested=true отвергается; test-only synthetic proof явно отделён от production. Unknown/null и HMAC scope сохраняются; scope mismatch не обходится allow_unattested. Registry/DTO/coverage/fixture/attestation regressions ниже; production пока не включает адаптер. Не добавлены выдуманные original pages или unsupported empty-STU.

T027 validation:33passed,exit0,0.80s (attestation,registry,DTO,coverage and real derived fixture). Первые5 завершены. Следующая пятёрка: T174 explicit8MiB policy,T029 real SGU adapter,T030 real-source quarantine,T032 actual worker,T033 actual atomic publication. Второй источник/STU и live-soak не будут отмечены done без данных.

## 6/30 T174

Default5MiB сохранён; frozen Adapter max_bytes имеет absolute8MiB cap. Worker передаёт declared policy в child,проверяет metadata against selected limit before payload read;raw/backup/restore cap8MiB. Initial transport/storage/backup suite71passed;added large referenced raw backup/verify/restore and size/envelope/worker boundary suite4passed,exit0. Отвергаются default5MiB для5851174byte sample,8MiB+1,hash/size mismatch. Actual pinned-DNS/TLS bounded_fetch8MiB successfully fetched SGU5851174bytes at2026-11-03T17:11:06Z,SHA256309968faf6ab11f172589adfe7f4a5fb43797b14c18c515055b206387dca4e9a;private600 file. Actual HTML hash differs from first capture although byte count same; adapter must normalize factual cells,not infer a list change from template hash. docs/api-contract.md consolidated adapter contract; duplicate newly-created API.md merged,old history retained in Git.
