#!/usr/bin/env python3
"""Classify discovered hawza.netlify.app library entries into Noor categories.

This script is intentionally metadata-first. It does not download books, mark
sources reviewed/approved, or modify the production knowledge database.

Input JSON may be either a list of entries or {"books": [...]} where entries
contain any of: title, author, subject/category, description, url, download_url,
path. The upstream dynamic catalogue endpoint still needs to be discovered and
wired separately; once available its normalized export can be fed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse


def normalize(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def load_taxonomy(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entry_text(entry: dict) -> str:
    fields = (
        "title", "author", "subject", "category", "description", "keywords",
        "path", "url", "download_url",
    )
    return " ".join(normalize(entry.get(field)) for field in fields)


def stable_catalog_id(entry: dict) -> str:
    key = "\x1f".join([
        normalize(entry.get("title")),
        normalize(entry.get("author")),
        normalize(entry.get("download_url") or entry.get("url")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def classify(entry: dict, taxonomy: dict) -> list[dict]:
    haystack = entry_text(entry)
    matches = []
    for category in taxonomy["requested_categories"]:
        keywords = category.get("include_keywords", [])
        matched = [kw for kw in keywords if normalize(kw) in haystack]
        if not matched:
            continue
        excludes = [kw for kw in category.get("exclude_when_only", []) if normalize(kw) in haystack]
        score = len(matched) * 10 - len(excludes) * 3
        matches.append({
            "category": category["id"],
            "category_ar": category["name_ar"],
            "score": score,
            "matched_keywords": matched,
        })
    return sorted(matches, key=lambda item: (-item["score"], item["category"]))


def canonical_url(entry: dict) -> str | None:
    for field in ("download_url", "url"):
        value = str(entry.get(field) or "").strip()
        if value.startswith(("https://", "http://")):
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--taxonomy", type=Path,
        default=Path("knowledge/catalog/hawza_library_taxonomy.json"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("knowledge/catalog/hawza_library_candidates.json"),
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    books = payload.get("books", []) if isinstance(payload, dict) else payload
    if not isinstance(books, list):
        raise SystemExit("Input must be a list or an object containing a books list")

    taxonomy = load_taxonomy(args.taxonomy)
    candidates = []
    seen = set()
    for raw in books:
        if not isinstance(raw, dict):
            continue
        cid = stable_catalog_id(raw)
        if cid in seen:
            continue
        seen.add(cid)
        matches = classify(raw, taxonomy)
        if not matches:
            continue
        url = canonical_url(raw)
        candidates.append({
            "catalog_id": cid,
            "title": str(raw.get("title") or "").strip(),
            "author": str(raw.get("author") or "").strip(),
            "upstream_category": str(raw.get("category") or raw.get("subject") or "").strip(),
            "source_url": url,
            "source_host": urlparse(url).netloc if url else None,
            "classification": matches,
            "proposed_category": matches[0]["category"],
            "review_status": "pending",
            "provenance_status": "unverified",
            "ai_evidence_eligible": False,
        })

    output = {
        "source_library": taxonomy["source_library"],
        "parent_library_ar": taxonomy["parent_library_ar"],
        "input_count": len(books),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"input": len(books), "candidates": len(candidates)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
