# Phase 5 Baseline and Hawza Catalogue Run

Date: 2026-09-06  
Branch: `codex/noor-phase5`  
Production database changed: **No**  
Production deployment: **No**

## Phase 5 result

The 22-book baseline was not built because both remaining sources failed
before safe reviewed-source integration.

| State | Count |
|---|---:|
| Reviewed | 20 |
| Blocked | 2 |
| Approved | 0 |
| Staging database | Not created |

### Diyafa

`python3 knowledge/build/recover_diyafa.py --pdf diyafa_ramadan.pdf --output knowledge/recovery/diyafa-final`

The canonical PDF is present at the repository root and has the expected SHA:
`1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa`.
The helper could not execute because PyMuPDF (`fitz`) is not installed in the
environment. The earlier independent page-wise Poppler inspection found 145
pages and 363,846 extracted characters, but every page triggered at least one
existing gate reason. No text was repaired and the source remains blocked.

### Shirazi

`python3 knowledge/build/recover_shirazi_static.py --output knowledge/recovery/shirazi-final`

The official route did not yield the required structured book. The helper
received only 10,605 characters and rejected the response as unexpectedly
short, below the required 100,000-character threshold. No old PDF Unicode
layer or OCR fallback was used. The source remains blocked.

### Tests

The complete unit suite passed: **27/27**. No staging, retrieval, SQLite or
FTS release validation was run because the source gate requires stopping when
either remaining source fails.

## Hawza catalogue discovery

The catalogue page is backed by Google Drive API v3 file listings. The live
frontend exposes these seven root folder IDs and the API key/configuration.
The metadata-only API request was attempted for all seven roots and returned
HTTP 403 Forbidden for each one.

| Result | Count |
|---|---:|
| Books discovered | 0 (access denied) |
| تفسير وشرح الأدعية | 0 verified |
| الخطابة الحسينية | 0 verified |
| الفقه | 0 verified |
| علوم القرآن | 0 verified |
| Unclassified | 0 verified |
| Baseline duplicates | Not determinable |

No PDFs were downloaded. No catalogue entry was marked reviewed or approved;
the generated catalogue is explicitly empty because the upstream metadata
endpoint denied access.

Outputs:

- `knowledge/catalog/hawza_library_discovery.json`
- `knowledge/catalog/hawza_library_catalogue.json`
- `knowledge/catalog/hawza_library_candidate.json`

The catalogue discovery report records the endpoint candidates and the exact
HTTP 403 errors for each root.

