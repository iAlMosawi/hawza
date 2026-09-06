# Noor Al-Hawza Phase 5 — Corpus Recovery Execution Plan

This document supersedes any proposal to create Phase 5.8, 5.9, 5.10, etc.

## Current safety state

- Production `hawza_knowledge.sqlite` remains the legacy v1 database and MUST NOT be replaced by the empty Phase 5 staging database.
- The Phase 5 architecture and validation gates remain authoritative.
- `knowledge/output/phase5_staging.sqlite` is a blocked/metadata-only engineering artifact, not a deployment candidate.
- Source recovery must happen outside production and must preserve legacy source IDs as aliases where canonical identity changes.

## New authoritative recovery registry

Use:

`knowledge/metadata/authoritative_source_recovery.json`

The registry records authoritative or institutional digital-source candidates for all 22 legacy sources. It intentionally leaves unresolved identity/provenance fields unresolved instead of guessing them.

## Recovery strategy

For each source, use the following order:

1. Official structured HTML.
2. Official Word/EPUB/digital text.
3. Official clean Unicode PDF.
4. Verified institutional digital edition.
5. Controlled multi-engine OCR with deterministic comparison and human review.
6. Keep blocked if safe recovery is not possible.

Do not let one blocked source stop recovery of the others.

## Important source families

### مكتبة المعارف الإسلامية

A large part of the legacy corpus has an authoritative digital candidate in the Islamic Maaref library. Its reader pages expose Arabic HTML and often PDF/Word downloads. Prefer the reader HTML when identity comparison confirms the same work/edition.

Do not select a newer edition merely because it is newer. Compare legacy title page, table of contents, opening text, and representative internal sections first. If it is a different edition, record it explicitly and require review before replacing the legacy source.

### منهاج الصالحين 1445

Use the official website of the office of Sayyid Ali al-Husayni al-Sistani. The official fatwa-book index exposes the corrected 1445 edition and structured HTML for all three volumes. Preserve volume and section structure and numbered masāʾil.

### المسائل الإسلامية

The legacy `risala-amaliyya-shirazi` identity is incorrect. Preserve it only as a legacy alias. Canonical identity is `masail-islamiyya-sadiq-al-shirazi`, title `المسائل الإسلامية`, attribution `السيد صادق الحسيني الشيرازي`. Prefer the official HTML reader. Do not ingest the official PDF's broken embedded text layer.

## Sources that must remain blocked until identity is resolved

- `diyafa-bi-ayn-al-amin`: inspect title/copyright/provenance pages and establish an authoritative publisher/source. Do not use `Abrar ghkh` as trusted authorship metadata.
- `risala-ilmiyya-sayyid-qaid`: inspect the existing PDF and identify the exact work before assigning author, marja, official/current status, or a replacement URL.

The two Khamenei volumes have an authoritative Maaref collection identified, but the exact item URLs/edition mapping must be resolved before ingestion.

## Required final ingestion run

Once acquisition is possible from the execution environment, perform ONE continuous recovery run, not per-source phases:

1. Read `authoritative_source_recovery.json`.
2. Resolve exact edition identity against the legacy files.
3. Acquire only authoritative candidate material.
4. Cache raw responses/files with provenance URL, retrieval timestamp, content hash and HTTP metadata.
5. Extract clean Unicode text without heuristic reconstruction.
6. Preserve headings, page/section references where available, ruling numbers, volume information and source provenance.
7. Run existing Phase 5 corruption and quality gates.
8. Exclude unsafe chunks rather than repairing sacred/religious text heuristically.
9. Build a new staging database only from evidence that passes the gates.
10. Run SQLite integrity, FTS integrity, schema compatibility, checksum, retrieval, citation and regression tests.
11. Produce per-source accepted/rejected counts and a final release report.
12. STOP before production deployment.

## Deployment gate

A future staging database may be considered for production only after:

- it contains real searchable evidence;
- all included evidence passes corruption gates;
- source identity/provenance is recorded;
- marja-specific material is isolated correctly;
- current/official metadata is asserted only when supported;
- regression tests pass;
- retrieval and citation tests pass;
- SQLite/FTS integrity and checksum pass;
- rollback artifact is prepared.

Never deploy an empty evidence database.
