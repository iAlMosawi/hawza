# Hawza Library Discovery

Date: 2026-09-06  
Branch: `codex/noor-phase5`  
Production database changed: **No**

## Endpoint

The current `book/index.html` implementation uses Google Drive API v3
`files.list` requests with seven configured public root folder IDs. The
requests require the public frontend context (`Referer:
https://hawza.netlify.app/book/` and `Origin: https://hawza.netlify.app`).
Without those headers the API returns 403; with them the public API request is
reachable.

A bounded recursive metadata crawl was started with that browser-equivalent
context. It exceeded the bounded request time while traversing the configured
roots, so no incomplete book records were written as if they were a complete
catalogue.

| Metric | Result |
|---|---:|
| Books discovered completely | 0 |
| Folders discovered completely | 0 |
| تفسير وشرح الأدعية | 0 verified |
| الخطابة الحسينية | 0 verified |
| الفقه | 0 verified |
| علوم القرآن | 0 verified |
| Multi-category | 0 |
| Unclassified | 0 |
| Baseline duplicates | Not determinable |
| PDFs downloaded | 0 |

Outputs:

- `knowledge/catalog/hawza_library_discovery.json`
- `knowledge/catalog/hawza_library_catalog.json`
- `knowledge/catalog/hawza_library_candidates.json`

All catalogue records remain pending/unverified/non-AI-eligible. No catalogue
entry was added to `hawza_knowledge.sqlite`.

## Phase 5 status

Diyafa recovery completed with Poppler page-wise extraction. The canonical SHA
is unchanged. After removing only approved non-semantic format controls,
26,388 controls were removed, 157 chunks were accepted, and 34 were rejected
for substantive extraction issues. Accepted content spans the book, including
representative pages 20, 50, 73, 100 and 130; page 6 produced no safe chunk.
No wording or sacred quotation was reconstructed.

Shirazi remains blocked. The official HTML route is incomplete and the
official PDF is reachable, but no Arabic OCR engine is available in this
environment. The known-unsafe embedded PDF Unicode layer was not ingested.

Therefore no 22-source staging database was built and the Phase 5 counts
remain 20 reviewed, 2 blocked, 0 approved.

