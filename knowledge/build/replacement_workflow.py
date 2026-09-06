#!/usr/bin/env python3
"""Generate the Phase 5.2 verified-source replacement worklist.

This is metadata and process tooling only. It neither copies source files nor
changes review/authority fields or the production knowledge database.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


TOP_PRIORITY = ["risala-amaliyya-shirazi", "risala-ilmiyya-sayyid-qaid"]

# These are evidence-backed acquisition outcomes, not religious review fields.
ACQUISITION_OUTCOMES = {
    "risala-amaliyya-shirazi": {
        "replacement_verification_status": "OFFICIAL_CANDIDATE_REJECTED_TECHNICAL_QUALITY",
        "identity_verification_status": "verified_official_same_work_manifest_identity_incorrect",
        "recommended_canonical_source_id": "masail-islamiyya-sadiq-al-shirazi",
        "acquisition_report": "knowledge/reports/phase5_4_masail_islamiyya_official_validation.json",
    },
}


def risk_score(source: dict) -> int:
    if source.get("category") == "fiqh":
        return 3
    if source.get("category") in {"aqidah", "kalam", "wilayah", "mahdawiyyah"}:
        return 2
    return 1


def build_records(manifest: dict, audit: dict) -> list[dict]:
    audit_by_id = {item["source_id"]: item for item in audit["sources"]}
    sources = [source for source in manifest["sources"] if source.get("enabled")]
    ordered = sorted(
        sources,
        key=lambda source: (
            TOP_PRIORITY.index(source["id"]) if source["id"] in TOP_PRIORITY else len(TOP_PRIORITY),
            -risk_score(source),
            -audit_by_id[source["id"]]["released_chunk_count"],
            -audit_by_id[source["id"]]["corruption_percentage"],
            source["id"],
        ),
    )
    records = []
    for position, source in enumerate(ordered, 1):
        audit_item = audit_by_id[source["id"]]
        record = {
            "priority": position,
            "source_id": source["id"],
            "current_title": source.get("title", ""),
            "current_author": source.get("author") or None,
            "old_source_file": source.get("path", ""),
            "proposed_replacement_file": None,
            "replacement_provenance": None,
            "edition": source.get("edition") or None,
            "version": source.get("version") or None,
            "language": source.get("language") or None,
            "category": source.get("category") or None,
            "subcategory": source.get("subcategory") or None,
            "marja": None,
            "official_source": None,
            "is_current": None,
            "review_status": None,
            "checksum": None,
            "replacement_verification_status": "awaiting_verified_file",
            "religious_risk_level": risk_score(source),
            "released_chunk_contribution": audit_item["released_chunk_count"],
            "corruption_percentage": audit_item["corruption_percentage"],
            "source_status": audit_item["source_status"],
            "notes": source.get("notes", ""),
        }
        record.update(ACQUISITION_OUTCOMES.get(source["id"], {}))
        records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="knowledge/manifest.json")
    parser.add_argument("--audit", default="knowledge/reports/phase5_1_source_audit.json")
    parser.add_argument("--output", default="knowledge/metadata/replacement_workflow.json")
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    records = build_records(manifest, audit)
    output = {
        "workflow_version": 1,
        "purpose": "Phase 5.2 verified source replacement tracking",
        "production_database_modified": False,
        "staging_progress": {
            "total_legacy_sources": len(records),
            "clean_replacements": 0,
            "awaiting_replacement": len(records),
            "safe_staging_chunks": 0,
        },
        "sources": records,
    }
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
