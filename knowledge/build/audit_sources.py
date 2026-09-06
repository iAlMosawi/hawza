#!/usr/bin/env python3
"""Read-only Phase 5.1 audit for released Hawza knowledge sources.

The tool compares PDF text layers but never modifies source files or attempts
to reconstruct damaged religious text.  Its staging manifest may be used only
for a temporary database build after human review.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sqlite3
import sys
from typing import Callable

import fitz
from pypdf import PdfReader
import pdfplumber

from build_knowledge import paragraph_chunks
from phase5 import corruption_reasons, json_ready_report, normalize_category, utc_now


def _fitz_pages(path: Path) -> list[str]:
    document = fitz.open(path)
    try:
        return [page.get_text("text") or "" for page in document]
    finally:
        document.close()


def _pypdf_pages(path: Path, limit: int | None = None) -> list[str]:
    pages = PdfReader(str(path)).pages
    return [page.extract_text() or "" for page in pages[:limit]]


def _pdfplumber_pages(path: Path, limit: int | None = None) -> list[str]:
    with pdfplumber.open(path) as document:
        pages = document.pages[:limit]
        return [page.extract_text() or "" for page in pages]


def _metrics(pages: list[str], chunking: dict) -> dict:
    target = int(chunking.get("target_chars", 1500))
    overlap = int(chunking.get("overlap_chars", 220))
    minimum = int(chunking.get("min_chars", 180))
    all_chunks: list[str] = []
    short_fragments = 0
    for page in pages:
        short_fragments += sum(
            1 for line in page.splitlines()
            if line.strip() and len(line.strip()) < minimum
        )
        all_chunks.extend(paragraph_chunks(page, target, overlap, minimum))

    reasons: dict[str, int] = {}
    usable = 0
    for chunk in all_chunks:
        found = corruption_reasons(chunk)
        if found:
            for reason in found:
                reasons[reason] = reasons.get(reason, 0) + 1
        else:
            usable += 1
    if short_fragments:
        reasons["unusably_short_fragments"] = short_fragments
    total = len(all_chunks)
    return {
        "pages_with_text": sum(1 for page in pages if page.strip()),
        "characters": sum(len(page) for page in pages),
        "chunk_count": total,
        "usable_chunk_count": usable,
        "rejected_chunk_count": total - usable,
        "corruption_percentage": round((100 * (total - usable) / total), 2) if total else 100.0,
        "corruption_reasons": reasons,
    }


def _best_method(methods: dict[str, dict]) -> str:
    return max(
        methods,
        key=lambda name: (
            methods[name].get("usable_chunk_count", 0),
            -methods[name].get("corruption_percentage", 100.0),
            methods[name].get("characters", 0),
        ),
    )


def _source_status(best: dict, pymupdf: dict) -> tuple[str, bool, bool]:
    if best["usable_chunk_count"] > 0:
        improved = best["usable_chunk_count"] > pymupdf["usable_chunk_count"]
        return "CLEAN_REBUILD_READY", improved, False
    if best["characters"] == 0:
        return "BLOCKED", False, True
    if best["characters"] > pymupdf["characters"]:
        return "NEEDS_BETTER_EXTRACTION", True, False
    return "NEEDS_REPLACEMENT_SOURCE", False, True


def _database_counts(connection: sqlite3.Connection, source_id: str) -> dict:
    row = connection.execute(
        "SELECT count(*) FROM chunks WHERE source_id = ?", (source_id,)
    ).fetchone()
    return {"released_chunk_count": int(row[0]) if row else 0}


def _metadata_worklist(source: dict) -> list[str]:
    fields = []
    for field in ("category", "subcategory", "author", "edition", "version", "marja", "official_source", "is_current", "review_status"):
        value = source.get(field)
        if value is None or value == "":
            fields.append(field)
    return fields


def _write_csv(path: Path, records: list[dict]) -> None:
    fields = [
        "source_id", "title", "author", "category", "original_path", "file_type", "pages",
        "released_chunk_count", "usable_chunk_count", "rejected_chunk_count", "corruption_percentage",
        "best_extraction_method", "clean_reextraction_possible", "better_source_required",
        "source_status", "human_metadata_review_required", "metadata_review_fields",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = {field: record.get(field, "") for field in fields}
            row["metadata_review_fields"] = ";".join(row["metadata_review_fields"])
            writer.writerow(row)


def _write_markdown(path: Path, report: dict) -> None:
    lines = [
        "# Phase 5.1 Existing Source Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Released sources: {report['released_database']['source_count']}",
        f"- Released chunks: {report['released_database']['chunk_count']}",
        f"- Staging-ready sources: {report['summary']['clean_rebuild_ready']}",
        f"- Sources needing replacement: {report['summary']['needs_replacement_source']}",
        f"- Sources requiring human metadata review: {report['summary']['human_metadata_review']}",
        "",
        "## Per-Source Status",
        "",
        "| Source | Title | File/pages | Status | Released chunks | Usable/rejected | Corruption | Best method | Metadata review |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for item in report["sources"]:
        lines.append(
            f"| `{item['source_id']}` | {item['title']} | `{item['original_path']}` / {item['pages']} | {item['source_status']} | {item['released_chunk_count']} | "
            f"{item['usable_chunk_count']}/{item['rejected_chunk_count']} | {item['corruption_percentage']}% | "
            f"{item['best_extraction_method']} | {', '.join(item['metadata_review_fields']) or 'none'} |"
        )
    lines.extend(["", "## Corruption Totals", ""])
    for reason, count in sorted(report["summary"]["corruption_reasons"].items()):
        lines.append(f"- `{reason}`: {count}")
    lines.extend(["", "## Per-Source Corruption Reasons", ""])
    for item in report["sources"]:
        reasons = ", ".join(f"{key}={value}" for key, value in sorted(item["corruption_reasons"].items())) or "none"
        lines.append(f"- `{item['source_id']}`: {reasons}")
    lines.extend(["", "## Safety Note", "", "No source text was changed. Damaged quotations remain excluded rather than reconstructed."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    source_root = Path(args.sources)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(f"file:{Path(args.db)}?mode=ro", uri=True)
    try:
        released = {
            "source_count": db.execute("SELECT count(*) FROM sources").fetchone()[0],
            "chunk_count": db.execute("SELECT count(*) FROM chunks").fetchone()[0],
            "integrity_check": db.execute("PRAGMA integrity_check").fetchone()[0],
        }
        records: list[dict] = []
        aggregate_reasons: dict[str, int] = {}
        for source in manifest.get("sources", []):
            if not source.get("enabled"):
                continue
            source_id = str(source["id"])
            path = source_root / source["path"]
            methods: dict[str, dict] = {}
            extractors = {
                "pymupdf": lambda: _fitz_pages(path),
                "pypdf_sample": lambda: _pypdf_pages(path, limit=args.alternate_page_sample),
                # pdfplumber is a diagnostic sample only: malformed PDFs can
                # make full traversal prohibitively slow. Full audit metrics
                # always come from PyMuPDF's complete page extraction.
                "pdfplumber_sample": lambda: _pdfplumber_pages(path, limit=args.alternate_page_sample),
            }
            for name, extractor in extractors.items():
                try:
                    methods[name] = _metrics(extractor(), manifest.get("chunking", {}))
                except Exception as exc:  # record a failed reader without modifying the input
                    methods[name] = {"error": f"{type(exc).__name__}: {exc}", "characters": 0, "chunk_count": 0, "usable_chunk_count": 0, "rejected_chunk_count": 0, "corruption_percentage": 100.0, "corruption_reasons": {"extractor_error": 1}}
            best_name = _best_method(methods)
            best = methods[best_name]
            status, reextractable, replacement_required = _source_status(best, methods["pymupdf"])
            worklist = _metadata_worklist(source)
            page_count = 0
            try:
                page_count = len(_fitz_pages(path))
            except Exception:
                pass
            for reason, count in best.get("corruption_reasons", {}).items():
                aggregate_reasons[reason] = aggregate_reasons.get(reason, 0) + count
            record = {
                "source_id": source_id,
                "title": source.get("title", ""),
                "author": source.get("author", ""),
                "category": normalize_category(source.get("category", "other")),
                "original_path": source.get("path", ""),
                "file_type": path.suffix.lower().lstrip("."),
                "pages": page_count,
                **_database_counts(db, source_id),
                "usable_chunk_count": best["usable_chunk_count"],
                "rejected_chunk_count": best["rejected_chunk_count"],
                "corruption_percentage": best["corruption_percentage"],
                "corruption_reasons": best.get("corruption_reasons", {}),
                "best_extraction_method": best_name,
                "extraction_methods": methods,
                "clean_reextraction_possible": reextractable,
                "better_source_required": replacement_required,
                "source_status": status,
                "human_metadata_review_required": bool(worklist),
                "metadata_review_fields": worklist,
            }
            records.append(record)
    finally:
        db.close()

    summary = {
        "clean_rebuild_ready": sum(item["source_status"] == "CLEAN_REBUILD_READY" for item in records),
        "needs_better_extraction": sum(item["source_status"] == "NEEDS_BETTER_EXTRACTION" for item in records),
        "needs_replacement_source": sum(item["source_status"] == "NEEDS_REPLACEMENT_SOURCE" for item in records),
        "blocked": sum(item["source_status"] == "BLOCKED" for item in records),
        "human_metadata_review": sum(item["human_metadata_review_required"] for item in records),
        "corruption_reasons": aggregate_reasons,
    }
    report = {"generated_at": utc_now(), "released_database": released, "summary": summary, "sources": records}
    (output_dir / "phase5_1_source_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_csv(output_dir / "phase5_1_source_audit.csv", records)
    _write_markdown(output_dir / "phase5_1_source_audit.md", report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="knowledge/manifest.json")
    parser.add_argument("--sources", default="knowledge/sources")
    parser.add_argument("--db", default="knowledge/output/hawza_knowledge.sqlite")
    parser.add_argument("--output-dir", default="knowledge/reports")
    parser.add_argument("--alternate-page-sample", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    report = run(parse_args())
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
