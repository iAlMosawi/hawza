# Hawza Knowledge Pipeline

This folder converts approved Hawza source documents into a local SQLite FTS5 database for the native iOS assistant.

## Build

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r knowledge/build/requirements.txt
python knowledge/build/build_knowledge.py
python knowledge/build/validate_knowledge.py --query "التوحيد"
```

Output:

```text
knowledge/output/hawza_knowledge.sqlite
```

## Supported source formats

- PDF (via PyMuPDF)
- TXT
- Markdown
- HTML
- JSON

Only files listed in `manifest.json` with `"enabled": true` are indexed.

## Phase 5 review and quality gates

The builder now creates schema v2 databases that are backward-compatible with
the v1 iOS and server readers. Existing released v1 sources remain
`legacy_trusted`; new sources are `pending` unless a human reviewer explicitly
approves them. Corrupt extraction is rejected rather than repaired by guesswork.

Each build writes a JSON quality report beside the database. Validate a new
database before release:

```bash
python knowledge/build/validate_knowledge.py \
  --db /tmp/hawza_knowledge.sqlite --require-phase5
```

See [PHASE5_OPERATIONS.md](PHASE5_OPERATIONS.md) for staged deployment,
rollback, and the remaining human-review work.

## Current approved source

The production manifest indexes the approved Noor library, including
`diyafa_ramadan.pdf`, the user-supplied Al-Shirazi practical treatise, and the
supplied educational, creed, fiqh, sirah, and Islamic-thought books. The
generated database preserves verified page metadata and must be rebuilt whenever
an approved source changes.

## Licensing

Do not commit copyrighted books to a public repository unless you have permission to redistribute them. The database contains extracted source text, so the same licensing concern applies to the generated database.
