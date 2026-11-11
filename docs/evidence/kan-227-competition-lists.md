# KAN-227: competition lists, source parser → snapshots → API

Date: 2026-11-11. Branch `zarbondo`. This card is mostly covered by work that already exists; this note maps its acceptance to code and tests and says what is missing.

## Acceptance

| Acceptance | Where | Tests |
| --- | --- | --- |
| Official lists of selected universities through the common pipeline | 15 reviewed groups at 5 universities: SGU, GUAP, BGU, MIEPL, UIFR (`backend/app/sources/table_profiles.py`, `adapters/sgu2026.py`); JSON/CSV family ready without sources (KAN-220) | `test_sgu_adapter.py`, `test_filtered_table.py`, `test_section_family.py`, `test_structured_family.py` |
| Snapshots are published atomically | `sources/publishing.py`: one transaction for snapshot, rows, pointer and change events | `test_publishing.py::test_atomic_repeat_concurrency_and_new_parser_version`, `test_postgres_publishing.py::test_reader_sees_only_complete_snapshots_during_uncommitted_publication`, `test_changes.py::test_change_insert_failure_rolls_back_snapshot_and_scenarios` |
| Source, year and group are not mixed | Candidate keys are scoped by source, group and year; adapters check the binding | `test_adapter_contract.py::test_candidate_identity_is_scoped_and_unknown_is_preserved`, `test_domain_regression.py::test_d05_same_public_id_does_not_merge_people_between_scopes`, `test_admissions.py::test_assessment_cannot_mix_subscription_and_snapshot_groups` |
| Stale is shown | `sources/status.py` states fresh / stale / archive / source_error / quarantined; competition API warnings `source_stale` and others; v3 pages show them | `test_source_status.py` (4 tests), `test_competitions.py::test_list_metadata_marks_archive_and_unpublished_priorities` |
| Parser and API covered by fixtures | Reviewed fixtures per source; competition API on the SGU archive | adapter tests above, `test_competitions.py` (4), `frontend/tests/api.spec.ts` |
| Worker retry does not duplicate events | Replay after a crash reuses the snapshot; change feed is deduplicated | `test_worker.py::test_crash_after_publication_replays_without_second_snapshot`, `test_changes.py::test_changefeed_is_private_deduplicated_and_seen_is_idempotent`, `test_structured_family.py::test_worker_imports_once_and_a_bad_list_keeps_the_last_valid_snapshot` |
| Safe scheduled refresh | `SourceJob` with interval, backoff, one running job per domain; `enqueue-all` spreads same-domain starts (KAN-220) | `test_worker.py`, `test_structured_family.py::test_mass_enqueue_spreads_domains_and_never_duplicates` |
| API for the UI | `/api/v1/competitions/{id}`, `/rows`, `/summary` (KAN-228) | `test_competitions.py`, `frontend/tests/api.spec.ts` |
| No access to other people's private data | Rows never carry candidate keys or codes; own row only after confirmation; change feed private to the owner | `test_competitions.py::test_rows_follow_official_order_and_never_expose_identifiers`, `::test_only_the_guest_sees_their_own_row`, `test_subscriptions.py::test_repeated_confirmation_saves_once_and_other_owner_cannot_use_it` |

## What is missing and why

- **Scale.** Five universities, not "most of Russia". Each new source needs a review, a fixture and an attestation.
- **Legal basis.** Fixtures and git history already hold real ranks, scores and consents without codes (audit finding 4). Adding more real lists should wait for the owner's decision on the data operator, the legal basis and retention.
- **Live data.** The 2026 lists are archive now. Lists of the 2027 campaign appear from late July 2027, so a live refresh can only be verified then, on a server with access to Russian university sites (T046, T048).
