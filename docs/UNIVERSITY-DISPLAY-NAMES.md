# Verified university display names

T311 / S224. Base: `main@591fa99`, including merged university card redesign PR25.

## Architecture and compatibility

The real v3 catalog is a read facade over two versioned public artifacts, not a
1366-row PostgreSQL university table. `national-catalog.json` supplies 1257
monitoring organisations (521 branches); the accreditation artifact contributes
109 registry-only organisations. PostgreSQL stores the small reviewed programme
slice and operator-owned records. Adding columns to that table would not cover
the catalog and would unnecessarily change its import identity checks.

`app/university_names.py` resolves a separate UI projection. The existing
`name`, `legalName` (the full original), IDs, branch flags, accreditation, source
records, sort keys and programme DTOs are unchanged. No migration, backfill,
database write, network access, ML dependency or paid API call is introduced.

Additive product DTO fields:

- `displayName`: selected literal title, including original-name fallback.
- `displayNameSource`: kind, source URL, verification time, original artifact
  SHA256 and optional normalization rule version.
- `nameAliases`: explicitly reviewed aliases, never generated initials.
- `branchInfo`: optional confirmed parent/city with its own URL, timestamp and
  checksum. Existing `isBranch` remains the authority for branch identity.

Older clients can ignore the additions. The new decoder accepts an older server
without the projection and uses `legalName`; a malformed or partially supplied
projection is an error. Catalog search adds the selected title and reviewed
aliases to the existing full/name/region/ID/programme search text. Its token
semantics, 120-character query bound, filters, original name sort, pagination,
routes and IDs are unchanged. Sorting deliberately retains the old key rather
than silently reordering pages by the new titles. The legacy API is unchanged.

## Selection order

1. **Official short name.** A verified, identity-bound primary-source review has
   priority. Otherwise the register's explicit `shortName` is used for heads
   whose full names match strictly (case, whitespace and typographic quotes
   only), or for the register-only organisation itself. Domain/core/fuzzy
   affiliation is insufficient. Empty/dash/absence placeholders are rejected.
   Verification time is the stored registry build/review time, not today's
   request time; the registry archive checksum identifies the original source.
2. **Conservative normalization.** `legal-prefix-v1` checks a finite list of
   complete anchored legal/education wrappers, removes one matching wrapper,
   and optionally one enclosing quote pair around the entire remaining name.
   An institution noun and a nontrivial remainder are required. Nested/unmatched
   quotes or quoted text followed by another qualifier cause abstention.
   Every identifying word of the suffix is retained verbatim: geography,
   specialisation, federal/research designation, honorary names and affiliations.
   These are labelled normalized titles, never official abbreviations.
3. **Reviewed manual title.** A separately verified manual record is eligible
   only if no official title or safe rule applies.
4. **Original fallback.** Return the source's full `legalName` exactly, without
   generating an acronym or guessing a compact name.

No branch is normalized automatically or given its parent's official short name.
An unreviewed branch displays its full original title and the literal `Филиал`.
Region is not treated as city. Head/city information is never inferred at request
time from ambiguous strings or accreditation matching.

The register sometimes puts several official variants into a single short-name
field. The field is kept intact; commas inside names are not treated as a safe
list grammar. Search still finds an abbreviation contained in that field.
Selecting a single variant needs an explicit source review.

## Sources and reviewed maintenance

- Existing [MICCEDU monitoring](https://monitoring.miccedu.ru/iam/2025/_vpo/)
  snapshot, edition2025, checksum recorded in the generated coverage artifact.
- Existing [Rosobrnadzor public register](https://isga.obrnadzor.gov.ru/accredreestr/opendata/),
  dataset `7701537808-RAOO`, dated2026-11-10. Full/short names and archive/build
  provenance were already captured by the existing registry importer.
- [ADI official information page](https://xn--80aiap0aaf8aj.xn--p1ai/sveden/common/),
  reviewed2026-11-15. Its explicitly labelled short name is retained with the
  branch designation and ДонНТУ. The full-name field establishes the parent;
  the address confirms Горловка. The requested bare headline is **not** substituted
  for that official short name. [Captured facts and source checksum](evidence/university-names/adi-source-facts.json).

`backend/app/data/university-names.json` is an independently versioned review
overlay. A record contains stable ID, exact original full name, explicit branch
flag, `official` or `manual` kind, `candidate` or `verified` status, display name,
reviewed aliases, optional branch facts, source URL/checksum/time. Only verified
records with an exact identity match can publish. Candidate titles/aliases/branch
facts are never served. A source rename or changed branch flag invalidates
publication of that record until re-review; the record itself is not deleted.

To add an entry: inspect a labelled first-party field/document, check identity
against the catalog (including campus/branch), capture the actual source checksum
and verification time, record only facts supported by that source, and submit
the record plus evidence for code review. Validate the complete overlay, run
tests/report, then deploy it with the application. Imports of monitoring and
reviewed programmes never write this file. Runtime artifact caches refresh on
application restart, like the existing catalog cache.

No LLM process is required. Offline suggestions can be stored as `candidate`
records, but must not be promoted without primary-source verification. An alias
must be explicitly evidenced too; it is not an automatic acronym of a title.

## Measured quality on the real catalog

Reproduce from `backend/`:

```sh
python -m app.university_name_report --output ../docs/evidence/university-names/coverage.json
```

This creates a private temporary SQLite database, imports only the reviewed
programme metadata, reads the actual catalog facade and disposes the database.
It never connects to the configured application database. The checked-in
[coverage report](evidence/university-names/coverage.json) includes all IDs,
before/after titles, source provenance and the review queue, not sampled or
estimated figures.

| Selected source | Organisations |
| --- | ---: |
| Official short-name field | 688 |
| Safe normalized title | 85 |
| Manual title selected at priority3 | 0 |
| Full original fallback | 593 |
| Total | 1366 |

The manual-review queue contains those **593 original fallbacks**; it overlaps
that row rather than adding a fifth bucket. Of688 official fields,630 are
strictly shorter than the original;58 are not (including multi-variant fields).
This is not a claim that688 titles became shorter. All521 branch flags survive;
only1 branch has separately confirmed parent/city metadata. The remaining520
branches retain full names without inferred affiliations or cities.

Real examples (originals remain in the report and on university details):

| ID / case | Result | Basis |
| --- | --- | --- |
| `miccedu-1593`, communications university | МТУСИ | Explicit register short name, strict full-name identity |
| `miccedu-113416`, federal university | Крымский федеральный университет имени В.И.Вернадского | Legal wrapper removed; federal/name retained |
| `miccedu-127`, research university | Национальный исследовательский Мордовский государственный университет им. Н.П.Огарева | Research designation and honorary name retained |
| `miccedu-101`, academy | Ковровская государственная технологическая академия имени В.А. Дегтярева | Complete legal wrapper only |
| `miccedu-110135`, private institute | Институт международных связей | Complete legal wrapper only |
| `miccedu-140143824`, branch | Автомобильно-дорожный институт (филиал) ДонНТУ г.Горловка | Official branch page, separate confirmed parent/city |
| `miccedu-10006765`, unreviewed branch | Full Волго-Вятский филиал… original retained | No verified branch shortening or city guessed |

## UI and validation

University cards use the projection with a three-line CSS clamp only on the
title link. Complete text remains in the DOM/accessibility name and original
name in its title attribute; the existing footer link opens the full detail.
Details show the selected title and **unclamped full original**, plus labelled
name provenance and separately sourced branch information. No text slicing is
used for titles; the existing avatar prefix remains unchanged. All card-grid,
footer, source/status and keyboard styles from PR25 remain scoped to universities.

Local checks on2026-11-15:

| Check | Actual result |
| --- | --- |
| `npm run typecheck` / `npm run lint` / `npm run build` | Passed |
| `npm test` | 384 passed (1.4min), all370 previous tests retained plus14 new cases |
| Relevant backend suites, `--require-postgres` | 85 passed,0 skipped,49.17s; naming, product catalog, national catalog, legacy catalog/SQL search, import, accreditation registry |
| Firefox university suite | 25 passed,33.7s |
| WebKit university suite | 25 passed,34.7s |
| Responsive geometry | 320/375/390/768/1024/1440/1920px: max3 title lines, no horizontal overflow, aligned row/title/info/footer tracks, source/href/status preserved |
| Data/import | Every source ID and full original retained; strict identity/source priority; candidates and stale records unpublished; repeated monitoring/programme imports retain review records and DB names/search/parent fields |
| API/interaction | Additive DTO/older-server fallback, malformed projection errors, original/short/alias search, region/sort/pagination/history, Tab/Enter/focus/hover, empty/503/network/retry |

The first browser run identified obsolete `СГУ имени` text expectations (the
official register uses a different literal casing/variant field). Those checks
now assert exact DTO title plus original full text and unchanged href instead.
Two new test bugs (a partial ID matching3 universities, and reading a result
before the request finished) were corrected; no assertion was skipped or timeout
increased. Positive browser cases use the real local catalog API with reviewed
snapshots; only transport/invalid-contract/old-version cases intercept responses.
Synthetic rule/alias fixtures are unit-test inputs, never catalog data.

The PostgreSQL checks used a dedicated disposable database and isolated schemas,
not the user's database or Docker volumes. Backend warnings were existing
Starlette/httpx and Python3.12 SQLite datetime deprecations. The broader backend
suite and hosted CI are not represented by this85-test local selection.

Before/after screenshots use the PR25 baseline and the same reviewed API data:

| Width | Before | After |
| --- | --- | --- |
|390 |[Before](evidence/university-names/universities-390-before.png) |[After](evidence/university-names/universities-390-after.png) |
|1440 |[Before](evidence/university-names/universities-1440-before.png) |[After](evidence/university-names/universities-1440-after.png) |

## Limits

This is deliberately conservative coverage, not a claim of reviewed short names
for every organisation. The catalogue and register are dated snapshots; renames
need refreshed sources/review. No automatic Russian case inflection, city
extraction, multi-variant short-field splitting or fuzzy identity promotion.
Original sort keys remain, so visible short titles need not be alphabetically
ordered. Three-line clamping intentionally changes PR25's unbounded title
presentation; its data/geometry checks are retained and supplemented by clamp,
full-detail and provenance assertions. Hosted CI results are separate from local
test results. No automatic merge.
