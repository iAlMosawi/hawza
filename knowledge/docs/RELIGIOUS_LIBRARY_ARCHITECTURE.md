# Noor Religious Library Architecture

The approved Noor corpus and the browsable electronic library are separate
layers. Catalogue availability never grants AI evidence eligibility.

## Lifecycle

`pending` -> `reviewed` -> `approved` is an explicit human-review workflow.
`blocked` and `rejected` records are never AI evidence. New catalogue records
default to `pending`, `provenance_status=unverified`, and
`ai_evidence_eligible=false`. Only approved records may enter an approved-only
database build.

## Knowledge and catalogue layers

- `hawza_knowledge.sqlite` remains the production-compatible knowledge DB.
- `knowledge/output/hawza_knowledge_phase5_approved.sqlite` is the isolated
  approved-only Phase 5 candidate.
- `knowledge/catalog/` contains metadata-only library discovery output.
- `knowledge/recovery/` contains source acquisition and quality evidence.

Catalogue records may have multiple taxonomy matches, but one canonical record
is retained using provider ID, canonical URL, hash, normalized title/author,
and edition. Unknown metadata remains null or unverified.

## Safety

Extraction preserves page provenance and uses the Phase 5 corruption gates.
Only proven non-semantic format controls may be removed. Sacred text, fiqh
rulings, hadith, duas, and ziyarat are never reconstructed heuristically.
Scanned sources may remain `ocr_required` without entering AI evidence.

Fiqh retrieval must preserve `marja`, edition, official-source, and currentness
metadata. It must not silently combine rulings from different maraji.

## Release and rollback

Build a candidate, validate SQLite/FTS/counts/corruption/citations, generate a
checksum and release manifest, then atomically swap only through the existing
deployment process. Keep the previous known-good DB for rollback. This run
does not modify or deploy the production DB.
