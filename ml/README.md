# ML data

## miccedu-admission-history (KAN-232)

**Status 2026-11-11:** the pipeline and tests are in the repository; the dataset files are not built yet. The capture (7360 pages) needs a Russian network and was interrupted; nothing in `data/` is committed until a full capture is built.

`data/miccedu-admission-history.csv` holds historical admission indicators of Russian universities from the official monitoring of higher education (MICCEDU), editions 2016–2025. `data/miccedu-admission-history.passport.json` describes coverage, gaps and bias.

**Grain.** One row per university (head organisation of the 2025 monitoring catalog) and admission year. The monitoring has no competition-group cutoffs, so there are no group-level labels here.

**Columns.**

| Column | Meaning |
| --- | --- |
| `registry_id` | MICCEDU institution id, stable across editions |
| `ogrn`, `departmental` | From the accreditation register match (KAN-217); empty when not matched |
| `region`, `ownership` | Region from the 2025 catalog; ownership `state` / `non_state` / `unknown` from the legal form in the name (an autonomous non-profit organisation is `non_state` even when founded by the state) |
| `edition`, `admission_year` | Monitoring edition E describes the campaign of year E-1 |
| `avg_ege_budget` | Average EGE of students admitted full-time on budget places |
| `avg_ege_budget_excl_special` | Same, excluding special rights and the target quota |
| `avg_ege_paid` | Average EGE of students admitted full-time on paid places |
| `avg_min_ege` | Minimum EGE of admitted students, averaged over the university's programmes. Closest university-level analogue of a passing score; not a group cutoff |
| `olympiad_final_stage`, `olympiad_other`, `target_admitted` | Counts of admitted olympiad winners and target-quota students |
| `source_url`, `page_sha256`, `fetched_at` | Provenance of each row |

Empty cell means the page did not publish the value.

**No future leakage.** Data of the campaign of year Y appears in edition Y+1, which is published the following year (edition 2025 with 2024 data was published on 03.02.2026). A model for campaign T may use only `admission_year <= T - 2`: `build_admission_history.training_rows(rows, T)`.

**Rebuild.**

```
python scripts/capture_admission_history.py --output capture.jsonl.gz   # from a Russian network, ~2 h
python scripts/build_admission_history.py capture.jsonl.gz [--check]
```

The capture itself is not committed; its SHA-256 is in the passport.
