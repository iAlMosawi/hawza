# Phase 5 Final Integration

Date: 2026-09-06  
Branch: `codex/noor-phase5`  
Production database changed: **No**  
Deployment: **No**

## Status

The supplied Shirazi recovery was imported and validated with the repository
Phase 5 gates. Diyafa’s committed recovery was validated again. The isolated
reviewed candidate contains all 22 sources:

| State | Count |
|---|---:|
| Reviewed | 22 |
| Blocked | 0 |
| Approved | 0 |

## Imported recovery results

### Diyafa

- Accepted: 157 recovery chunks; 116 searchable chunks after normal build chunking
- Rejected: 34 recovery chunks
- Method: Poppler page-wise extraction with approved non-semantic format-control stripping
- Canonical SHA-256: `1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa`
- No heuristic religious-text repair was used

### Shirazi

- Imported package SHA-256: `b39000094c64416010a00cfa45d07f5db241fe10e0b200f836a8e608dafd23bb`
- External candidate chunks: 677
- Repository-gated accepted chunks: 425
- Repository-gated rejected chunks: 252
- Final searchable chunks: 377
- Accepted pages after repository gates: 403
- Rejection reasons: Arabic embedded digits (238), malformed symbols (15)
- Official PDF SHA recorded by supplied report: `a5be33251efd39d22b5d3c782a050bc1c5d33ee0b05a363d17fe73ab4020f6eb`
- Embedded PDF Unicode layer and heuristic religious-text repair were not used

## Staging database

Path: `knowledge/output/phase5_22_reviewed_staging_20260906.sqlite`  
Size: 47,280,128 bytes  
Sources: 22  
Chunks: 3,233  
FTS rows: 3,233  
Schema: v2  
SHA-256: `d28a3d73f30104b1c3715970ea4dc38185a8d5f8bb15750c3b469aa146351f20`

Validation passed: SQLite `integrity_check = ok`, FTS integrity, zero orphan
chunks, zero orphan FTS rows, zero duplicate source IDs, zero U+FFFD evidence,
and the production evidence corruption gate.

Per-source searchable chunks are recorded in the machine-readable report.

## Tests and retrieval

The complete Phase 5 unit suite passed: **27/27**.

FTS retrieval returned evidence for: التوكل (11), الإخلاص (24), التقوى (29),
أهل البيت (147), الإمامة (98), الصلاة على محمد (35), الابتلاء (11), and
مرجع التقليد (4). The exact term التواكل returned 0 direct FTS rows and must
remain subject to the existing insufficient-evidence behavior rather than being
filled from unsupported model memory. No production answer API was invoked.
