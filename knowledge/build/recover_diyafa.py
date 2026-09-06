#!/usr/bin/env python3
"""Recover safe page-level evidence from the canonical ضيافة بعين الأمين PDF.

The canonical repository PDF has already been identity/hash verified. This
helper deliberately removes only Unicode presentation controls that Phase 5
classifies as non-semantic formatting. It never repairs, rewrites, or guesses
Arabic/Qur'an/hadith/dua text. Pages/chunks with substantive corruption remain
rejected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz

from build_knowledge import paragraph_chunks
from phase5 import (
    corruption_reasons,
    nonsemantic_format_control_count,
    strip_nonsemantic_format_controls,
)

SOURCE_ID = "diyafa-bi-ayn-al-amin"
EXPECTED_SHA256 = "1ce99056750e17938ebb2475214a56b0e6054b699925cc5931f811da576a1afa"
EXPECTED_PAGES = 145


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def recover(path: Path, *, target_chars: int = 1500, overlap_chars: int = 220, min_chars: int = 180) -> dict:
    digest = sha256_file(path)
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"canonical PDF SHA mismatch: {digest}")

    doc = fitz.open(path)
    try:
        if len(doc) != EXPECTED_PAGES:
            raise RuntimeError(f"unexpected canonical page count: {len(doc)}")

        accepted: list[dict] = []
        rejected: list[dict] = []
        page_stats: list[dict] = []
        total_format_controls = 0

        for page_index, page in enumerate(doc, start=1):
            raw = page.get_text("text") or ""
            format_controls = nonsemantic_format_control_count(raw)
            total_format_controls += format_controls
            cleaned = strip_nonsemantic_format_controls(raw)
            chunks = paragraph_chunks(cleaned, target_chars, overlap_chars, min_chars)
            page_accepted = 0
            page_rejected = 0

            for chunk_index, chunk in enumerate(chunks, start=1):
                reasons = corruption_reasons(chunk, minimum_chars=min_chars)
                record = {
                    "page": page_index,
                    "chunk_index": chunk_index,
                    "chars": len(chunk),
                    "text": chunk,
                }
                if reasons:
                    record["reasons"] = reasons
                    rejected.append(record)
                    page_rejected += 1
                else:
                    accepted.append(record)
                    page_accepted += 1

            page_stats.append({
                "page": page_index,
                "raw_chars": len(raw),
                "clean_chars": len(cleaned),
                "nonsemantic_format_controls_removed": format_controls,
                "accepted_chunks": page_accepted,
                "rejected_chunks": page_rejected,
            })
    finally:
        doc.close()

    return {
        "source_id": SOURCE_ID,
        "status": "RECOVERED_PENDING_REVIEW" if accepted else "BLOCKED_NO_SAFE_EVIDENCE",
        "canonical_path": str(path),
        "sha256": digest,
        "pages": EXPECTED_PAGES,
        "method": "pymupdf_pagewise_strip_nonsemantic_unicode_format_controls_then_phase5_gates",
        "heuristic_text_repair_used": False,
        "sacred_text_reconstruction_used": False,
        "nonsemantic_format_controls_removed": total_format_controls,
        "accepted_chunk_count": len(accepted),
        "rejected_chunk_count": len(rejected),
        "page_stats": page_stats,
        "accepted_chunks": accepted,
        "rejected_chunks": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=Path("diyafa_ramadan.pdf"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.pdf.exists():
        alternate = Path("knowledge/sources/diyafa_ramadan.pdf")
        if alternate.exists():
            args.pdf = alternate
        else:
            raise SystemExit(f"canonical Diyafa PDF not found: {args.pdf} or {alternate}")

    report = recover(args.pdf)
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "diyafa_recovery.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # A compact clean-evidence export is easier for the normal reviewed-source
    # ingestion path to consume while preserving page provenance in the report.
    evidence = "\n\n".join(
        f"[page {item['page']}]\n{item['text']}" for item in report["accepted_chunks"]
    )
    (args.output / "diyafa-bi-ayn-al-amin.txt").write_text(evidence, encoding="utf-8")

    print(json.dumps({
        "status": report["status"],
        "accepted_chunks": report["accepted_chunk_count"],
        "rejected_chunks": report["rejected_chunk_count"],
        "format_controls_removed": report["nonsemantic_format_controls_removed"],
    }, ensure_ascii=False))
    return 0 if report["accepted_chunk_count"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
