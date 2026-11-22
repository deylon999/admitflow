# Новые записи по backend и KAN-218

## S240 — 2026-11-22 — Backend organization: catalog

Catalogue package, old CLIs and resource paths verified. 107 focused tests pass. Parent comparison preserves contracts, with five callable names relocated. Full Linux and browser results are tracked in the stage evidence.

## S241 — 2026-11-22 — Backend organization: competitions

Competition and scenario package implemented. 68 focused tests pass. Parent comparison matches all 26 items, including dependency layout and schema. Full Linux and browser results are tracked in the stage evidence.

## S242 — 2026-11-22 — Backend organization: watchlist

Watchlist and guest ORM implemented, with existing paths, cookie, owner lock and clock hooks. 88 focused tests pass. 26 parent comparisons match, with route and owner callable relocations recorded.

## S243 — 2026-11-22 — Backend organization: operations and final verification

All five implementation stages are ready for review. Final code 8b4d481: Linux PostgreSQL 1278 passed, 387 native cases and one inherited MICCEDU skip. Frontend 387 and PostgreSQL browser auth 6/6/6. Final comparisons, Compose and CLI verified. Hosted runs and PR links are recorded in the organization report.

## S244 — 2026-11-22 — публикация организации backend

PR #38, #39, #40, #41 и #42 открыты с последовательными базами. Полный backend-прогон на финальном дереве дал 1278 passed, 387 native PostgreSQL cases и тот же пропуск MICCEDU. 387 frontend checks, по шесть native auth checks в Chromium, Firefox и WebKit, плюс 32 автоматизированных auth controls.

На исходных опубликованных SHA каждого PR оба события Checks прошли 4/4. Итоговый отчёт фиксирует SHA реализации, сравнение с базами и ссылки на прогоны. SHA финального отчётного коммита проверяется отдельным прогоном. Статус задач T336–T340 остаётся review до проверки владельцем.

## S239 / T319 — 2026-11-22 — PR4 audit and measured plan

Fresh main1e7693e includes merged PR31 and architecture PRs through37. Separate
worktree/branch avoids parallel work. Current projection hydrates only selected
facts, but computes global collision windows before filters three times per page.
Baseline/EXPLAIN and Python memory/ORM counts required before optimization.
Acceptance and five-step checklist in docs/KAN-218-PR4.md. T319 in_progress,
T320 national coverage not started. No runtime/schema change in this step.

## S239 / T319 — 2026-11-22 — PostgreSQL scale baseline

Benchmark7dcd24f, clean start, PG17.11:100000 current synthetic programmes and
200000 old facts across785heads/215branches/four campaigns. Normal guards on.
Nine timing samples per case: p95 1118–1408ms, Python peak about1.77MB, page-only
fact hydration. EXPLAIN shows repeated global window sorts spilling to disk.
Full original report archived losslessly with SHA; compact metrics in
docs/evidence/kan-218-pr4-baseline.json. Prototype query consolidation follows;
no index/migration justified yet. T319 remains in_progress.

## S239 / T319 — 2026-11-22 — measured SQL and regression handoff

Code b19dd7a: global current-publication anti joins, one statement for facets/
count/page, aggregated university search tokens; no DTO/migration/frontend/CI
changes. Nine samples on100k current/200k old synthetic facts: p95first1196→661ms,
university1174→259ms;8response hashes identical, Python peak1.77→1.49MB.
Local500ms target remains unmet for broad/deep cases; not a staging gate pass.
Native extended selection138passed/1failed115.01s: failed national coverage test
imports existing Linux-only resource on Windows. Full Linux CI retained.
Official-original rehearsal b19dd7a passed; repeated import unchanged and SGU
IDs/exams/16seats preserved,2027 pilot1/785. T319 review pending owner/CI; T320
not started. Final CI/exact SHA recorded in PR metadata; no automatic merge.

## S239 / T319 — 2026-11-22 — expanded owner performance acceptance

Prior d9636b2 push/PR CI8/8 success. Owner explicitly rejects treating relative
speedup as final. New per-case targets and50+ warmed samples/concurrency10–50,
PostgreSQL memory/load/temp metrics and architecture comparison recorded in
KAN-218-PR4-READ-MODEL.md. T319 back in_progress; PR43 returned to draft.
PR39–42 merged into parent feature branches, not main; full backend9ad69c6
available for independent adaptation. Main at6fdafc9 contains onlyPR38.
No owner PRs merged by agent; historical measurements preserved.

## S239 / T319 — 2026-11-22 — separate backend adaptation and transactional read model

Merged prior PR43 work into the independent full-backend branch; no GitHub/main
merge. Compatibility aliases retained, implementation in app/catalog. New0015
adds synchronous derived read facts/policy with global conflict checks at pointer
publication, epoch serialization, immutable-history FK and exact SQL fallback on
policy mismatch. Source migrations0001–0014 unchanged. Native140pass/1offline
JSON compilation failure corrected; focused14pass verifies fix and backfill/
downgrade, concurrent writes, stale-RR failure, corruption guards and policy changes.
Experimental frozen direct-projection p95 (50samples):69/17/74/270ms; not yet
final production metrics. Ten-second concurrency10/25/50 run saved separately;
64MB shared-memory failures retained, controlled1GB profile has no HTTP failures.
T319 remains in_progress, PR43 draft, adaptation separate per owner response.

S239 continuation: replaced correlated eligibility maintenance with set-based
global counts for affected identities after the231s bulk-seed observation.
Native PostgreSQL selection33passed/0skip46.80s (projection/publication/metadata/
migration offline SQL). f100f5c Linux CI44999820936 green; final new SHA pending.
Target-year100k comparative read trial is running; preliminary production-only
facade p95 56/15/117/134ms, exact source response hashes equal. Not final acceptance.

Added an isolated loopback Uvicorn1/4-worker benchmark to distinguish Python
TestClient contention from PostgreSQL load, record seed statement timings and
50 committed100-program revision replacements before50 read samples. Captures
every measured SELECT plan, including prepared pagination/totals. Compile/help
checks pass; full execution follows the running architecture comparison.

S239 further profiling: preceding transactional deep-page load wrote30.2GB
temporary data. Added exact bidirectional OFFSET with bounded indexed source
prefix before archive UNION; no DTO/order/count change. Native PostgreSQL57pass
56.89s verifies both sort directions, duplicate titles, legacy interleaving,
filters, partial/empty pages, existing campaign immutability and snapshots.
The campaign identity guard already exists in0014 and is reused unchanged.
Overloaded prepared-current trial stopped with saved500/503 logs; remaining
alternatives use serial-only comparison to avoid repeating resource pressure.

S239 profiling continuation: cold read statistics estimated209 year rows vs
100000 and one code hit vs64500. New0015 ANALYZE after backfill/large statements,
document deletion index, literal substring predicate (independent source LIKE
oracle retained). PG75passed84.34s verifies metadata/migrations/API/pagination/
literal Unicode search. f467103c serving baseline completed45047 HTTP requests,
zero failures, zero read temp writes; worker4 code p95 at50concurrency708ms.
Final statistics/substring run adds midpoint pagination and1/4/8-worker comparison.

## S239 / T319 — 2026-11-22 — separate adaptation performance evidence

Pinned `cc86e5814e1b8bc13aa3a750361110335cb2e4d3`. The 100,000-program 2027
fixture also includes 75,000 archived programs and 350,000 previous fact
versions. The read harness saved 50 warm facade samples per scenario and
59,830 real HTTP requests across 40 phases. Verified exact totals in every
phase and no HTTP or transport errors. PostgreSQL wrote no temporary files
during HTTP reading. Four workers p95 at 50 requests was 233/296/646/284 ms
for first/university+year/code/tail and 322 ms for midpoint. All targets pass
at 10 requests. Three miss at 50. The code count reaches 1408% PG CPU.

Populated 0015 backfill took 141.8 s and incremental publication of a
100-program revision took 83.3 ms p95 across 50 transactions. Linux CI on
that code is green (run 45015752335, backend 1248, frontend 387, migrations
and ETL green). The [results](KAN-218-PR4-RESULTS.md) compare source CTE,
extra source indexes, frozen candidates, frozen eligible keys and the
transactional projection. Raw samples and plan archives retain original
path, tested SHA and checksums. T319 remains in progress, with PR #43 draft
and the adaptation kept on its own branch pending integration and review.


## S239 / T319 — 2026-11-22 — repeated 50-request load verification

Two warmed 7e00bf3 Windows runs used four Uvicorn workers and the same PG17.11 settings.
63,723 requests, no failures. Both runs meet p95 targets including OFFSET 50,000
and 99,988. Report preserves initial stalls, failed alternatives and different
Linux p95. Exact code count p95 37.4→0.76 ms with atomic 0016 counters, collision
checks, rollback, and measured writer cost. Independent full JSON and official
original replay passed. Application 1b2aff3 CI 1254 backend tests, four green jobs.
PR #44 synced with main documentation without changing tested application code.
T319 moves to review. No PR merge or national-coverage claim. [Report](KAN-218-PR4-P95.md).
