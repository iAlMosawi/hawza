# Phase 5 22-Source Recovery Attempt

Date: 2026-09-06  
Branch: `codex/noor-phase5`  
Production database changed: **No**  
Production deployment: **No**

## Result

The requested 22-reviewed baseline was **not built**. Both remaining sources
must pass the existing extraction and corruption gates before they can move to
`reviewed`; neither source was changed to `approved`.

| Metric | Result |
|---|---:|
| Sources reviewed | 20 |
| Sources blocked | 2 |
| Sources approved | 0 |
| New staging database | Not created |

The previous isolated staging database remains the last known-good candidate:
`knowledge/output/phase5_final_isolated_candidate_20260906.sqlite`.

## Diyafa: `diyafa-bi-ayn-al-amin`

The repository-root PDF `diyafa_ramadan.pdf` exists and matches the requested
canonical SHA-256:

`1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa`

It reports 145 A4 pages. The requested path
`knowledge/sources/diyafa_ramadan.pdf` is not present in this checkout, so the
manifest still resolves the root copy. No alternate public PDF was used or
compared.

A page-by-page Poppler extraction was run for all 145 pages. Results:

| Statistic | Result |
|---|---:|
| Extracted characters | 363,846 |
| Pages inspected | 145 |
| Pages with no gate reason | 0 |
| Pages with gate reasons | 145 |
| Main rejection reason | `bidi_or_invisible_artifact` on 142 pages |
| Other reasons | malformed symbols: 2; very short: 9; malformed brace/pipe: 1; excessive punctuation: 10 |

Representative extracted page sizes were page 1: 29 characters, page 73:
5,783 characters, and page 145: 216 characters. The beginning and end pages
contain attribution/license or publisher material rather than usable book
passages. No heuristic repair or sacred-text reconstruction was performed.

Status: **blocked**. The source was not moved to `reviewed`.

## Shirazi: `risala-amaliyya-shirazi`

The provided `knowledge/build/recover_shirazi_static.py` was executed against
its configured official URL:

`https://www.alshirazi.org/library-item/203?langs=AR`

The official server currently returns HTTP 302 redirecting back to the same
URL. Python `urllib` terminates with an infinite redirect error, and direct
header inspection reproduces the same loop for both the library-item and
library-htmlItem URLs. No authoritative HTML, TOC, or book text was obtained.

The old PDF Unicode layer was not used, and OCR was not used.

Status: **blocked**. The source was not moved to `reviewed`.

## Validation

The pre-existing unit suite was run before recovery. It reported 24 tests with
1 failure and 1 error in `test_recover_shirazi_static.py`, caused by the
current parser fixture requiring the `كتب ذات صلة` end marker. This was not
worked around because doing so would risk accepting incomplete official text.

The new 22-source staging build, SQLite/FTS validation, retrieval regression
suite, and final staging SHA-256 were not run because the user-required gate
explicitly says to stop when either source fails.

## Required next evidence

1. Add or restore the canonical PDF at `knowledge/sources/diyafa_ramadan.pdf`
   or update the manifest deliberately while preserving its verified SHA.
2. Provide an official Shirazi endpoint that does not redirect to itself, or
   repair the official server-side route and rerun the existing static harvester.
3. Re-run the Phase 5 gates, then build the isolated 22-source reviewed
   staging database only if both sources pass.

