# KAN-219: entrance test requirements from official documents

Date: 2026-11-11. Branch `zarbondo`.

## What is shipped

- `docs/sources/exam-rules/sgu-2026.json`: review of the SGU document "Информация о перечне и формах проведения вступительных испытаний ... в 2026 году" (dated 08.06.2026, sha256 `936121ed…6903`), pages 4 and 11.
- `scripts/build_exam_requirements.py`: builds `backend/app/data/exam-requirements.json` from the review and the original PDF. It refuses to write when the document hash differs, when a group anchor or an evidence line is not in the declared block, when a minimum score has no evidence line with that subject and number, or when a subject marked as conflicting has a score. The output depends only on the inputs: `--check` rebuilds and compares bytes.
- `backend/app/exam_requirements.py`: strict parser of the artifact (whole file rejected on any damage) and lookup by group. Rules are returned only when year, level, code and study form match the group exactly.
- API: `examRequirements` in `/api/v1/catalog/programs` and `/programs/{id}`. Fields: tests in the order of the document, options for "на выбор", `minScore` or null, `additionalTests` (`[]` means the document names none, null means not collected), `benefits` always null (not collected), `notes`, `source`.
- UI: the program page shows the tests, the choice, minimums, notes and links to the document and the cross-check table. Programs without reviewed rules keep the "Нет данных" card.
- Coverage dashboard: the EGE layer counts heads with reviewed rules: 1 of 785 (SGU).

## Data

| Group | Code, form | Tests (as in the document) |
| --- | --- | --- |
| sgu-2026-4588 | 09.03.04, очная | 1. математика (профильная) от 40; 2. информатика от 46 или физика (минимум не подтверждён); 3. русский язык от 40 |
| sgu-2026-4576 | 02.03.03, очная | same |

Cross-check: the table "Приёмная кампания 2026" at https://www.sgu.ru/cpk lists the same subjects for both directions (no minimums there).

## Inconsistent rule found

The SGU document gives physics 41 in the faculty table and 40 in item 18 (with reference to Minobrnauki order 881). The builder records the conflict, the minimum is null, and the note is shown on the page. Nothing is guessed.

## Not done

- Only the two SGU programs that are already published in the catalog. Other universities need their own documents and reviews; national coverage of this layer is 0.1%.
- Special rights, quotas and benefits are not collected (`benefits` is always null).
- 2027 rules: universities publish them by 1 November; none are reviewed yet.

## Tests

- `backend/tests/test_exam_requirements.py`: artifact validation (15 damage cases), exact matching (year, code, form, level), reproducible build from the document text excerpt `backend/tests/fixtures/exam-rules/sgu-2026-excerpt.txt`, 8 cases where the builder must refuse facts missing from the document, conflict note propagation.
- `backend/tests/test_product_catalog.py`, `test_national_coverage.py`: API values and the coverage layer.
- `frontend/tests/catalog.spec.ts`: the program page at 390 and 1440 shows the tests and the unconfirmed physics minimum; four damaged payloads (score above 100, numbering gap, extra field, benefits claimed) are shown as an error.
- Screenshots: `kan-219-program-1440.png`, `kan-219-program-390.png`.
