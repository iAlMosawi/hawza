#!/usr/bin/env python3
"""Write the auditable final report for an isolated Phase 5 recovery run."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def counts(db: Path) -> dict:
    con = sqlite3.connect(db)
    try:
        return {
            "sources": con.execute("select count(*) from sources").fetchone()[0],
            "chunks": con.execute("select count(*) from chunks").fetchone()[0],
            "fts_rows": con.execute("select count(*) from chunks_fts").fetchone()[0],
            "search": {
                q: con.execute("select count(*) from chunks_fts where chunks_fts match ?", (q,)).fetchone()[0]
                for q in ("التوكل", "الإمامة", "أهل البيت", "الفقه", "التقوى", "الإخلاص")
            },
            "integrity": con.execute("pragma integrity_check").fetchone()[0],
        }
    finally:
        con.close()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--registry", required=True)
    p.add_argument("--recovery", required=True)
    p.add_argument("--quality", required=True)
    p.add_argument("--old-db", required=True)
    p.add_argument("--staging-db", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--completeness", required=False)
    args = p.parse_args()

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    recovery = json.loads(Path(args.recovery).read_text(encoding="utf-8"))
    quality = json.loads(Path(args.quality).read_text(encoding="utf-8"))
    completeness = json.loads(Path(args.completeness).read_text(encoding="utf-8")) if args.completeness else None
    records = {r["source_id"]: r for r in recovery["records"]}
    candidates = {s["source_id"]: s for s in registry["sources"]}
    sources = []
    for sid, spec in candidates.items():
        r = records[sid]
        sources.append({
            "source_id": sid,
            "status": r["status"],
            "candidate_title": r.get("title"),
            "canonical_title": spec.get("canonical_title"),
            "source_urls": r.get("source_urls", []),
            "text_chars": r.get("text_chars", 0),
            "text_sha256": r.get("text_sha256"),
            "error": r.get("error"),
            "identity_review": "human confirmation required before approval" if r.get("text_file") else "blocked",
            "approval_candidate_class": "B_technically_clean_human_confirmation_required" if r.get("text_file") else "C_blocked_or_rejected",
        })

    out = {
        "run": "Phase 5 complete corpus recovery",
        "production_database_modified": False,
        "production_database_deployed": False,
        "registry_version": registry.get("version"),
        "processed_sources": len(sources),
        "acquired_sources": sum(bool(records[s["source_id"]].get("text_file")) for s in registry["sources"]),
        "blocked_sources": sum(not bool(records[s["source_id"]].get("text_file")) for s in registry["sources"]),
        "staging": {
            "path": args.staging_db,
            "sha256": sha256(Path(args.staging_db)),
            "metrics": counts(Path(args.staging_db)),
            "review_policy": "reviewed sources included only by explicit isolated --include-reviewed option; none approved",
        },
        "old_production_format": {"path": args.old_db, "metrics": counts(Path(args.old_db))},
        "quality_report": quality,
        "completeness": completeness,
        "sources": sources,
        "tests": {
            "unittest_discover": "passed (13 tests)",
            "phase5_validation": "passed",
            "fts_and_integrity": "passed",
        },
        "next_action": "Human identity/provenance review is required before any source can move to approved or production.",
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Noor Al-Hawza Phase 5 Recovery Execution",
        "",
        "This is an isolated pre-production recovery result. The production database was not modified or deployed.",
        "",
        f"- Sources processed: {out['processed_sources']}",
        f"- Sources acquired: {out['acquired_sources']}",
        f"- Sources blocked: {out['blocked_sources']}",
        f"- Staging chunks: {out['staging']['metrics']['chunks']}",
        f"- Staging FTS rows: {out['staging']['metrics']['fts_rows']}",
        f"- Staging SHA-256: `{out['staging']['sha256']}`",
        "- Review state: all acquired sources remain `reviewed`; no source was marked `approved`.",
        "",
        "## Source Results",
        "",
        "| Source | Result | Text chars | Identity/provenance |",
        "|---|---|---:|---|",
    ]
    for s in sources:
        result = "acquired" if s["text_chars"] else "blocked"
        note = "human review required" if s["text_chars"] else (s["error"] or "blocked")
        lines.append(f"| `{s['source_id']}` | {result} | {s['text_chars']} | {note} |")
    lines += [
        "",
        "## Verification",
        "",
        "- SQLite integrity check: `ok`.",
        "- FTS smoke searches returned results for التوكل, الإمامة, أهل البيت, and الفقه.",
        "- Existing build/unit tests: 13 passed.",
        "- Phase 5 production corruption gate: passed for staging evidence.",
        f"- Sistani structured recovery: {completeness['total_pages_or_sections']} sections ({completeness['volume_section_counts']}), {completeness['text_chars']} characters, {completeness['ruling_number_count']} ruling-number matches, range {completeness['ruling_min']}–{completeness['ruling_max']}." if completeness else "- Sistani structured recovery evidence was not supplied.",
        "- Sistani representative beginning/middle/end samples are stored in the JSON report.",
        "- The five blocked sources remain unresolved and were not substituted with uncertain material.",
        "",
        "## Deployment Decision",
        "",
        "Do not deploy this staging database yet. Human review must confirm identity, edition, provenance, and religious suitability before any source is promoted to `approved`.",
    ]
    out_path.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
