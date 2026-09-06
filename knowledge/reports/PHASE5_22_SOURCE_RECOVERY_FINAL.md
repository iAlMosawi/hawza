# Phase 5 22-Source Recovery Update

The latest run safely recovered a review candidate for Diyafa but did not
complete the 22-source baseline.

| State | Count |
|---|---:|
| Reviewed | 20 |
| Blocked | 2 |
| Approved | 0 |

## Diyafa

Status: **recovered pending human review**. The canonical PDF SHA remains
`1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa`.
Poppler page-wise extraction was used. Only Phase-5-defined non-semantic
format controls were removed. The recovery produced 157 accepted chunks and
34 rejected chunks; rejection reasons were 23 very-short passages, 10
excessive punctuation-garbage passages, and 1 malformed brace/pipe passage.

## Shirazi

Status: **blocked**. The official HTML response is incomplete and the official
PDF requires page-level Arabic OCR. No Arabic OCR engine is available in the
current environment, so the unsafe embedded Unicode layer was not used and no
source evidence was admitted.

## Staging

No new reviewed staging database was built because the required condition that
both remaining sources pass was not met. Production was not modified or
deployed.

