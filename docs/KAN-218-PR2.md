# KAN-218 PR2: проверенный импорт программ

Работа начата2026-11-21 от `main@46adc5b` после owner merge
[PR27](https://github.com/deylon999/admitflow/pull/27). PR1 принят; вся KAN-218
остаётся открытой. Ветка `feat/kan-218-verified-program-import`.

Пятёрка T322–T326: официальные документы → независимая сверка и конкретный
DTO proposal → provenance/revisions → атомарный импорт и API → nativePG/CI/PR.
Acceptance записаны до реализации в реестре задач. Общая карточка T317
остаётся незавершённой до выполнения её критериев.

Цель2027 сохраняется; архив2026 не переносится. Первое исследование источников
начато, доступность/достоверность и результат сбора ещё не приняты. Существующие
две reviewed программы СГУ/API и все идентификаторы сохраняются.

## T322: источники захвачены

Оба оригинала получены через существующий pinned HTTPS fetcher после robots:
ВШЭ396192байта, SHA256`8518a05c7a817ae2a69f2f3a8f32810a97ffca8fa59b618a7e3a9cd935fc6609`;
СГУ286243байта, SHA256`61f7c938d2d11cc815cf591482e82a2ecd79557e62db32796af82fdb47c3821d`.
Точные URL, даты UTC, robots hashes и политика ограниченного чтения:
[паспорта](sources/program-catalog/README.md),
[метаданные](sources/program-catalog/captures.json).

Добавлен воспроизводимый CLI `scripts/capture_program_catalog.py`; default
cache вне Git, явный source key, один документ после robots, finite delay,
нет retries/обхода запретов. Прежний документ сохраняется при ошибке.
`cd backend; .venv/Scripts/python.exe -m pytest -q tests/test_program_catalog_capture.py`:
**5 passed,0skip,exit0**; проверены serial capture, повтор без дублей raw,
disallow, HTML вместо robots, большой crawl-delay, отказ источника и сохранность.
Это ещё не публикация программ. T323 проверяет факты и конкретный DTO proposal.
