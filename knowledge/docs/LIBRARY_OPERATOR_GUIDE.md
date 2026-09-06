# Library Operator Guide

Metadata discovery is safe and does not download books or add evidence:

```sh
python3 knowledge/build/discover_hawza_library_catalog.py \
  --output knowledge/catalog/hawza_library_discovery.json
python3 knowledge/build/classify_hawza_library.py \
  --input knowledge/catalog/hawza_library_catalog.json \
  --taxonomy knowledge/catalog/hawza_library_taxonomy.json \
  --output knowledge/catalog/hawza_library_candidates.json
```

Source acquisition must record provenance, hash, extraction method, page
coverage, accepted/rejected chunks, and quality reasons. Build review
candidates with `--include-reviewed` only for isolated validation. A
production build must be approved-only and must not use that flag.

Validate a candidate with:

```sh
python3 knowledge/build/validate_knowledge.py \
  --db knowledge/output/hawza_knowledge_phase5_approved.sqlite \
  --require-phase5
```

Approval is a human action recorded in an audit manifest. Never promote a
catalogue record automatically because extraction succeeded.
