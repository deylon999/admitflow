# KAN-220: source adapters through one interface, mass queue

Date: 2026-11-11. Branch `zarbondo`.

## What the card asks and where it is covered

| Acceptance | Status | Where |
| --- | --- | --- |
| At least 3 different source types through one interface | Done | `Adapter` / `Registry` in `backend/app/sources/registry.py`. Families: SGU pilot HTML (`sgu-2026-4588-v1`), reviewed HTML tables in 4 variants (`reviewed-html-table-v1`, `-v2`, `reviewed-section-table-v1`, `reviewed-filtered-table-v1`), and new reviewed JSON (`reviewed-json-list-v1`) and CSV (`reviewed-csv-list-v1`) in `backend/app/sources/structured_family.py`. All return the same `ParsedList` and go through the same worker, publisher and status code. |
| Re-import does not duplicate data | Done | Same payload gives the same snapshot: `test_worker_imports_once_and_a_bad_list_keeps_the_last_valid_snapshot` (JSON and CSV, PostgreSQL), plus the existing replay tests in `test_worker.py`. |
| A failure does not overwrite verified records | Done | Same test: a list with a wrong row count fails with `invalid_format`, and the published snapshot and its 4 rows stay. Existing quarantine and integrity tests cover HTML. |
| Error log | Done | Worker writes `source_run_finished` JSON events with a stable code, `SourceJob.last_error_code`, `SourceOperation` history; dashboard `/app/coverage` lists problem sources (KAN-221). |
| Load limits | Done | One running job per domain (advisory lock in the claim step), retry with backoff, timeouts and size caps in the fetcher, and now `enqueue_all` spreads first runs of the same domain by 60 s. |
| Mass jobs without manual upload per university | Done for registered sources | `python -m app.sources.cli enqueue-all` queues every enabled source whose adapter is attested. Missing or unattested adapters are counted by reason and never queued. |
| SSRF protection, respect source limits | Existing | `backend/app/sources/fetcher.py`: https only, port 443, resolved address checks, redirect checks, byte limit per adapter. JSON/CSV adapters cap a list at 8 MiB and 100 000 records. |
| PostgreSQL integration tests | Done | `backend/tests/test_structured_family.py` (18 tests, worker and queue tests on PostgreSQL), `test_worker.py` CLI check. |
| PDF lists | Not done | No PDF decoder. A PDF list needs a reviewed source and an extraction check against the original; none is in hand. |

## Strict decoding rules (JSON and CSV)

- A profile names the field for rank and public code (required) and optionally score, consent, priority, status. Unknown field names in a profile are rejected at start.
- Rows must follow the official order 1..N and N must equal the declared row count. Codes must match the profile pattern and be unique; they are hashed into scoped keys immediately and never stored or returned.
- CSV: the header must equal the reviewed header exactly; wrong delimiter, short rows or a cut file fail. Charset comes from the fetch result (cp1251 tested).
- JSON: the path to the records must exist; NaN, nested values, HTML instead of JSON fail.
- Unknown consent or status values fail the whole list instead of being guessed.
- Any failure is `invalid_format`; nothing partial is published.

## Production state

`PROFILES` in `structured_family.py` is empty. No official JSON or CSV list has passed the review (passport, original, independent row check), so the runtime registry adds no JSON/CSV adapter yet. Adding one is a profile plus an attestation, without code changes.

## Manual check

Fresh PostgreSQL database, migrations applied, 6 reviewed sources registered from `table_profiles.py`:

```
$ python -m app.sources.cli enqueue-all          # empty database
{"sources": 0, "queued": 0, "deferred": 0, "skipped": {}, "domains": 0}
$ python -m app.sources.cli register-reviewed <id> --enable   # x6
$ python -m app.sources.cli enqueue-all
{"sources": 6, "queued": 6, "deferred": 0, "skipped": {}, "domains": 5}
$ python -m app.sources.cli enqueue-all          # repeat
{"sources": 6, "queued": 0, "deferred": 6, "skipped": {}, "domains": 5}
```

Two sources on `uifr.ru` got start times 60 s apart; other domains start at once. One worker pass from the cloud container (no route to Russian sites) failed with `dns_unavailable`, the job was kept with attempt 1 and a retry time, and nothing was published.

## Tests

- Backend on PostgreSQL: 724 passed.
- New: `backend/tests/test_structured_family.py`; CLI `enqueue-all` in `test_worker.py`.
