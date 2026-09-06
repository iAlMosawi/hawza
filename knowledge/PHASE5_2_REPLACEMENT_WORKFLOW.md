# Phase 5.2 Verified Source Replacement Workflow

Do not replace `hawza_knowledge.sqlite` or change religious approval metadata
in this phase. Each replacement is validated in isolation before it can enter
the staging corpus.

## Required replacement package

For one existing `source_id`, provide:

1. A clean, verified Arabic digital source file.
2. Its provenance and permission/source link or supplier record.
3. Confirmed title, author, edition/version, and language.
4. For marja-specific fiqh only: a human confirmation of marja, whether it is
   official, and whether it is current.

Do not fill `approved`, `official_source`, `is_current`, or `marja` from a
filename, PDF metadata, or an AI inference.

## Isolated technical validation

Use a temporary manifest containing only the proposed replacement, then run:

```bash
python knowledge/build/audit_sources.py \
  --manifest /path/to/replacement-manifest.json \
  --sources /path/to/replacement-folder \
  --db knowledge/output/hawza_knowledge.sqlite \
  --output-dir /tmp/noor-replacement-audit

python knowledge/build/build_knowledge.py \
  --manifest /path/to/replacement-manifest.json \
  --sources /path/to/replacement-folder \
  --output /tmp/noor-replacement.sqlite \
  --quality-report /tmp/noor-replacement-quality.json

python knowledge/build/validate_knowledge.py \
  --db /tmp/noor-replacement.sqlite --require-phase5
shasum -a 256 /path/to/replacement.pdf
```

Only a file with zero unsafe production evidence may proceed to the separate
human approval checkpoint and then the Phase 5 staging corpus.

## First required replacement

`risala-amaliyya-shirazi` needs a clean verified Arabic edition of
**الرسالة العملية للسيد رضا الشيرازي**. The current repository file and the
available Downloads copy have identical SHA-256 values, so the Downloads copy
is not a replacement. Its edition/version, marja designation, official status,
current status, and approval status require human confirmation.
