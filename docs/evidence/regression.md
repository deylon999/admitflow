# T042 — регрессия доменных правил

Запуск: из `backend/`, `python -m pytest -q --require-postgres tests/test_domain_regression.py` плюс указанные файлы. Тест `test_regression_map_points_at_existing_tests` падает, если ссылка ниже устарела.

Ожидаемые результаты взяты из `docs/QUALITY.md` и `docs/DATA_RULES.md`. Это синтетические случаи и правила проекта. Сверка с настоящими архивами зафиксирована отдельно в T188/T031.

| Случай | Ожидаемый результат | Доказательство |
| --- | --- | --- |
| D01 Люди вне конкурса уже отсутствуют | Повторно не вычитаются | `test_domain_regression.py::test_d01_people_outside_competition_are_not_subtracted_again` |
| D02 Две причины у одного человека | Вычитается один раз | `test_domain_regression.py::test_d02_person_with_two_reasons_is_subtracted_once` |
| D03 Новое согласие | Меняет новый результат, прошлый неизменен | `test_domain_regression.py::test_d03_new_consent_changes_new_result_and_not_the_previous_one`, `test_source_history.py::test_archive_history_is_immutable_paginated_private_and_idempotent` |
| D04 Отзыв и отсутствие согласия | Разные состояния | `test_domain_regression.py::test_d04_withdrawn_and_missing_consent_are_different_states` |
| D05 Совпадающий публичный ID | Не объединяет людей между источником, группой и сезоном | `test_domain_regression.py::test_d05_same_public_id_does_not_merge_people_between_scopes`, `test_admissions.py::test_same_official_group_id_does_not_merge_seasons_or_branches` |
| D06 Приоритет неизвестен | Официальный результат не вычисляется | `test_domain_regression.py::test_d06_unknown_priority_never_produces_an_official_result`, `test_sgu_adapter.py::test_unknown_consent_priority_remain_null_and_do_not_become_negative_or_zero` |
| D07 Ошибочное число мест | Отказ или карантин | `test_domain_regression.py::test_d07_missing_or_zero_capacity_refuses_without_numbers`, `test_domain_regression.py::test_d07_erroneous_capacity_is_quarantined_against_previous`, `test_domain_regression.py::test_d07_first_publication_is_compared_with_reviewed_capacity` |
| D08 Последний запрос упал | Последнее корректное значение остаётся с меткой | `test_source_status.py::test_archive_and_failures_never_look_fresh`, `test_source_recovery.py::test_real_format_failure_quarantine_recovery_retains_history` |
| D09 Неполная пагинация | Latest не переключается | `test_domain_regression.py::test_d09_incomplete_pagination_is_refused`, `test_worker.py::test_synthetic_worker_success_then_quarantine_preserves_latest` |
| D10 Архив | Видна дата и метка архива | `test_source_status.py::test_archive_and_failures_never_look_fresh`, `test_group_catalog.py::test_archive_catalog_exposes_metadata_without_candidate_rows` |
| D11 Повтор POST | Дублей нет | `test_writes.py::test_create_retry_returns_original_response_without_duplicates`, `test_writes.py::test_snapshot_retry_does_not_extend_history_twice`, `test_subscriptions.py::test_repeated_confirmation_saves_once_and_other_owner_cannot_use_it` |
| D12 Конкурентные запросы | Лимиты 20/500 не обходятся | `test_writes.py::test_concurrent_creation_cannot_exceed_watch_limit`, `test_writes.py::test_concurrent_snapshots_cannot_exceed_history_limit`, `test_subscriptions.py::test_manual_and_archive_share_twenty_limit_under_concurrent_writes` |

Q03: равные баллы, неизвестное согласие, неподдержанный конкурс, неполные поля и отсутствие строки покрыты тестами `test_q03_*` в том же файле. Ноль мест покрыт D07.

## Найдено и исправлено

Проверка места только на падение пропускала завышенное число мест: 16000 вместо 16 давало любому абитуриенту `within`. Теперь такой снимок уходит в карантин `capacity_growth`, а первая публикация сверяется с проверенным значением группы (`capacity_mismatch`).

## Остаётся неизвестным

- Правила приоритетов и особых квот между группами не моделируются, результат всегда условный (`priorities_not_applied`).
- Сверка с живыми списками приёмной кампании невозможна вне сезона.
