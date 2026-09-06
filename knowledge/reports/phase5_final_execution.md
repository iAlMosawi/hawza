# Noor Al-Hawza Phase 5 Final Execution

## Outcome

All 22 existing sources were processed against the Phase 5 safety policy.
Production was not modified. No unsafe or unverified religious text was added
to evidence retrieval.

The validated staging artifact is:

`knowledge/output/phase5_staging.sqlite`

SHA-256:

`509fbbbbb34a5b4421392a16af655be2210210d4511ea02cb1200435d1e0ba6b`

## Final metrics

| Metric | Result |
| --- | ---: |
| Sources processed | 22 |
| Sources safely verified for production evidence | 0 |
| Sources in staging metadata | 22 |
| Sources blocked/rejected | 22 |
| Sources requiring human review | 22 |
| Searchable chunks | 0 |
| FTS rows | 0 |
| Staging schema | v2 |
| SQLite integrity | `ok` |
| Production database changed | No |

The empty staging database is intentional and validated only through the
explicit `--allow-empty-blocked-staging` audit mode. Normal validation still
rejects empty evidence databases.

## Source outcomes

The complete per-source inventory, extraction metrics, corruption reasons,
paths, and metadata worklist remain in
`knowledge/reports/phase5_1_source_audit.json` and the final status copy in
`knowledge/metadata/phase5_final_source_status.json`.

Every source is marked:

`BLOCKED_SOURCE_REPLACEMENT_REQUIRED`

The existing PDF extraction results were unsafe or insufficiently verified.
The first source, `masail-islamiyya-sadiq-al-shirazi`, has a verified official
reader candidate, but the deterministic public client timed out before the
required 25-section verification. It was therefore not admitted to staging.

## Identity and aliases

The corrected first-source identity is:

- Canonical ID: `masail-islamiyya-sadiq-al-shirazi`
- Legacy alias: `risala-amaliyya-shirazi`
- Title: `المسائل الإسلامية`
- Attribution: `السيد صادق الحسيني الشيرازي`

The old incorrect title/author metadata was not used as production evidence.

## Verification

Executed successfully:

- 13 knowledge/build tests.
- Legacy v1 database compatibility and FTS search validation.
- Phase 5 corruption-gate tests.
- Pending/rejected exclusion tests.
- Alias/source metadata architecture tests.
- SQLite `PRAGMA integrity_check` on final staging: `ok`.
- v2 schema and review-state validation.
- Empty blocked-staging validation.

The existing production-format database remains v1 with 22 sources and 6,515
legacy searchable chunks. Its known legacy extraction corruption remains
untouched because replacing production evidence was explicitly prohibited.

## Remaining human decisions

Before any source can be added to a future evidence corpus, human review is
required for source identity, edition, publisher, authority, category,
marja-specific status, official/current status, and review approval. The first
source additionally requires completion of the official-reader 25-passage
HTML-to-rendered-PDF comparison.

## Deployment and rollback guidance

No deployment commands were executed. The staging artifact must not replace
`/var/lib/noor/hawza_knowledge.sqlite` because it intentionally contains no
searchable evidence. Any future production deployment requires a separately
approved non-empty corpus, checksum verification, SQLite integrity validation,
atomic swap, and retention of the current v1 database for rollback.
