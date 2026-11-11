# KAN-218: programmes, campaigns and seats at national scale — status

Date: 2026-11-11. The card is not done. This note records where the data can come from and what blocks it.

## Current coverage

Programs layer of `/app/coverage`: 1 of 785 head organisations (SGU, two reviewed programmes, archive 2026). The 60% target needs about 471 universities with verified current-year programmes.

## Official sources checked

| Source | What it gives | State on 2026-11-11 |
| --- | --- | --- |
| Minobrnauki, «Информация о правилах приема в вузы» (minobrnauki.gov.ru/abitur/) | For each university (state and private, about 610 entries on 61 pages): links to its admission page, admission rules and number of places | Page 1 opens. Every page with query parameters (pagination, region filter, search) redirects to `noaccess.minobrnauki.gov.ru/maintenance_minobrnauki/` («Ведутся технические работы»). Not worked around. |
| Minobrnauki open data (minobrnauki.gov.ru/opendata/) | 6 data sets: inspections, student numbers, territorial bodies, vacancies | No admission targets or programmes. |
| Budget places (КЦП) for 2027/28 | Structure approved by the Government council in October 2026; distribution between universities by contest until 29 December 2026 (news of 27.10.2026) | Distribution by university is not published yet. |
| University sites | Programmes, forms, entrance tests; seats after the КЦП distribution. Example: SGU table «Приёмная кампания 2026» at sgu.ru/cpk (167 rows: code, programme, form, tests) | Needs one reviewed adapter per site family. Reachable only from a Russian network (the user's PC, not the cloud runner). |

## Plan when unblocked

1. When the directory pages open again, import it as a source map: university → official admission page, rules and seats links, matched to the accreditation register by name (the KAN-217 matcher). This gives a measured "official links known" layer, not programme coverage.
2. Group the linked pages by site platform and build reviewed adapters per family (KAN-220 interface: HTML, JSON, CSV; PDF still missing).
3. Seats for 2027 only after the КЦП distribution (after 29.12.2026) and the universities' own publications; until then seats stay null and the campaign is marked as archive 2026.

Nothing in this plan fills programmes or seats from forecasts or third-party aggregators.
