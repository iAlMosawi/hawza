# Final Last-Two Source Recovery

Production was not modified or deployed. No source was approved automatically.

- Sources: 22 total, 20 reviewed, 2 blocked, 0 approved.
- Staging: 20 sources, 2100 chunks, 2100 FTS rows.
- SQLite integrity: `ok`.
- Staging SHA-256: `bb358abc4273497a3e8e6d2d62535bdf0635fd63d2bb8956c5824b650acd6aca`.
- Tests: 21 passed.

## Retrieval

- التوكل: 7
- التواكل: 0
- الإخلاص: 19
- التقوى: 24
- الإمامة: 79
- أهل البيت: 122
- الفقه: 101
- الصلاة على محمد وآل محمد: 1
- الابتلاء: 8

## Diyafa

- Status: `BLOCKED`.
- Legacy SHA-256: `1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa`; candidate SHA-256: `dae41b5ca2e15147c5749e3455245b43dad124292da1a31c84caca680adb6abe`.
- Both files report 145 pages and matching title metadata.
- Content equivalence was not established because safe candidate text extraction stalled. The old `Abrar ghkh` attribution is rejected. No text was staged.

## Shirazi

- Status: `BLOCKED`.
- Official harvester was hardened for persistent cache, SHA validation, resume, bounded retries, state persistence, and incomplete-harvest blocking.
- Official reader timed out before TOC/CSRF acquisition; no sections were harvested and no PDF Unicode layer was used.

## Decision

The current isolated corpus remains a 20-source reviewed candidate with these two sources blocked. Human approval is still required; no production candidate or deployment was created.
