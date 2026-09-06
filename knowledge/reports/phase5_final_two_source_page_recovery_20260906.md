# Final Two-Source Recovery

No source was approved and production was not modified or deployed.

- Staging: 20 reviewed, 2 blocked, 2100 chunks, 2100 FTS rows.
- SQLite integrity: `ok`
- SHA-256: `bb358abc4273497a3e8e6d2d62535bdf0635fd63d2bb8956c5824b650acd6aca`
- Tests: 21 passed.

## Diyafa

- Page dimensions matched on all 21 requested pages.
- Average normalized visual pixel difference: `0.4692`.
- Both PDFs are 145 pages and have different binary hashes.
- Safe candidate text extraction failed on multiple pages, so content equivalence was not accepted for text ingestion.
- Final status: `BLOCKED`.

## Shirazi

- Official reader bootstrap timed out before CSRF/TOC acquisition.
- Harvested sections: 0; missing/expected sections cannot be determined without TOC.
- Cache/resume/SHA/state logic was implemented and tested.
- Final status: `BLOCKED`.

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

The isolated staging remains 20 reviewed / 2 blocked. No approved-only candidate or deployment was created.
