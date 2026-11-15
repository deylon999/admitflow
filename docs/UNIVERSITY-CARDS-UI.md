# University catalog card/grid redesign

Baseline:main8f6f3b0. TaskT310. The screenshot referred to in the prompt was not attached in the accessible message; a reference link was requested but not received. Implementation follows the explicit written structure and existing AdmitFlow tokens. Exact visual correspondence to the unseen image is not claimed.

## Changes and boundaries

- UniversityCatalog has the requested h1 and lime count badge from the existing decoded resource.data.total; no count constant or fake zero while loading. Existing request path/query/debounce/filter/sort/offset/state are untouched.
- Scoped af-university-catalog/af-university-card styles provide two columns above930px and one below,24px desktop/20px mobile gaps, blue logo, full untouched names, source/status column, separators and right-aligned footer link. Original avatar prefix calculation is retained; no name-abbreviation algorithm.
- Growing cards have no clipping/fixed height. Desktop subgrid shares metadata/title/info/footer tracks between a pair, so legal-name and region lengths do not move corresponding elements out of alignment. @supports fallback keeps the base growing layout for older engines.
- All name/source/year/status expressions and universityPath/RouteLink hrefs are unchanged. Explicit tabIndex0 on university title/footer links supports standard keyboard navigation in the tested WebKit build; program links omit the attribute and retain their existing behavior. Focus ring/hover and48px footer target are scoped to this page.
- Program card/component styles and all other pages are untouched; internal.css, API/decoder/types/state helpers, routes, backend, data and dependencies are unchanged.
- The two forbidden demo/real-catalog links were not present in this real catalog. They remain in their unrelated existing Unsupported component; nothing was removed from other sections. Only real pagination follows successful results.

## Validation - 2026-11-15

| Check | Actual result |
| --- | --- |
| npm run typecheck | exit0 |
| npm run lint | exit0 |
| npm run build | exit0, production Vite build |
| npm test | exit0,370passed (1.4min); existing359 retained +11 university UI checks |
| Firefox university suite |11passed,20.6s |
| WebKit university suite |11passed,24.0s |
| Widths |320/375/390/768/1024/1440/1920 |
| Layout/data checks |real local catalog API; actual total and unchanged names/regions/source editions/statuses/hrefs; no horizontal overflow, full title visibility, equal pair heights/title/info/footer positions, intact source word/number |
| Interaction/edge checks |empty response from actual search, actual pagination/history/region/sort journeys, initial loading without invented count,503/network+real retry, Tab/focus/hover/Enter |
| Other-page pixel guards |program listing, university detail and auth login are byte-identical before/after at1440 |
| Source/data preservation |before/after API DTOs equal; ProgramsCatalog and Pagination source tails identical; no changes to state/decode/types/backend/internal.css |
| Repository checks |git diff --check and roadmap --render --check pass |

Positive cases use the existing ephemeral catalog runtime with reviewed public source snapshots through actual endpoints, not injected university lists or invented statuses. Test names include real short31-character and long190-character names. Negative transport tests intentionally intercept503/network errors only; positive retry returns to the real API. No user DB or Docker volumes changed. Existing tests/assertions remain intact; testMatch only adds the new file.

Visual review caught a split source value and uneven title starts at1024: reserved source width/nowrap and subgrid fixed those, with stricter tests. Initial Firefox44px floating-point measurement was43.9998; the actual touch target was enlarged to48 rather than relaxing its assertion. WebKit keyboard investigation showed default link traversal skipped native links: explicit tabIndex0 fixes standard Tab while retaining strict focus+Enter assertions. No browser-specific skips, synthetic focus on the footer, longer timeouts or reduced thresholds were used.

## Screenshots

Before is the baseline build; after is the final source. Same Chromium/900px viewport height, locale/fonts and reviewed local API data. Seven full-page+viewport captures per revision are under ignored .qa-tools/university-{before,after}; new seven-width screenshots are attached to Playwright outputs. Manually inspected all widths and full/legal-name cards; final desktop pair alignment rechecked. Committed pairs:

| Width | Before | After |
| --- | --- | --- |
|390 |[Before](evidence/university-cards-ui/universities-390-before.png) |[After](evidence/university-cards-ui/universities-390-after.png) |
|1440 |[Before](evidence/university-cards-ui/universities-1440-before.png) |[After](evidence/university-cards-ui/universities-1440-after.png) |

## Limits

The requested reference image is unavailable, so comparison is before/after against the existing site, not a claim of matching that image. Full legal names intentionally produce tall rows; nothing is abbreviated or clipped. Older engines without CSS subgrid use the base grid fallback; current Chromium/Firefox/WebKit were checked. Broader hosted CI is separate from the local results above and its exact outcome is maintained in the PR checks/description. No automatic merge.
