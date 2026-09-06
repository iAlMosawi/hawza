#!/usr/bin/env python3
"""
Build a local Hawza SQLite + FTS5 knowledge database.

Supported source types:
  .pdf, .txt, .md, .html, .htm, .json

Run from repository root:
  python knowledge/build/build_knowledge.py

Optional:
  python knowledge/build/build_knowledge.py \
      --manifest knowledge/manifest.json \
      --sources knowledge/sources \
      --output knowledge/output/hawza_knowledge.sqlite
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unicodedata
from typing import Iterable, Iterator, Optional

from phase5 import (
    PRODUCTION_REVIEW_STATES,
    QUALITY_REPORT_VERSION,
    SCHEMA_VERSION,
    corruption_reasons,
    fresh_quality_report,
    json_ready_report,
    normalize_category,
    passage_quality,
    utc_now,
    validate_source_metadata,
)

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)
WHITESPACE = re.compile(r"\s+")


class TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(self.parts)


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u00ad", "")
    # PDF extractors can emit form-feed and other non-content separators.
    # Removing those control characters is not textual reconstruction; the
    # substantive corruption checks run later on the retained evidence.
    value = "".join(
        char for char in value
        if char in "\n\t" or unicodedata.category(char) not in {"Cc", "Cs"}
    )
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in value.splitlines():
        line = WHITESPACE.sub(" ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def normalize_for_search(value: str) -> str:
    """
    Search-only normalization. Original text remains untouched in `text`.
    """
    value = unicodedata.normalize("NFKC", value)
    value = ARABIC_DIACRITICS.sub("", value)
    value = value.replace("ـ", "")
    translation = str.maketrans({
        "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    })
    value = value.translate(translation)
    value = WHITESPACE.sub(" ", value).strip().lower()
    return value


def stable_id(*parts: str) -> str:
    raw = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def paragraph_chunks(
    text: str,
    target_chars: int,
    overlap_chars: int,
    min_chars: int,
) -> list[str]:
    text = clean_text(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for p in paragraphs:
        candidate = p if not current else current + "\n" + p
        if len(candidate) <= target_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        # Very long single paragraph: hard split.
        if len(p) > target_chars:
            start = 0
            step = max(1, target_chars - overlap_chars)
            while start < len(p):
                piece = p[start:start + target_chars].strip()
                if len(piece) >= min_chars:
                    chunks.append(piece)
                start += step
            current = ""
        else:
            current = p

    if current and len(current) >= min_chars:
        chunks.append(current)

    # Add textual overlap between ordinary chunks when useful.
    if overlap_chars > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = chunks[i - 1][-overlap_chars:].strip()
            combined = (tail + "\n" + chunks[i]).strip() if tail else chunks[i]
            overlapped.append(combined)
        chunks = overlapped

    return chunks


def extract_pdf(path: Path) -> Iterator[tuple[Optional[int], str]]:
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF is required for PDF extraction. "
            "Install: pip install -r knowledge/build/requirements.txt"
        )

    doc = fitz.open(path)
    try:
        for idx, page in enumerate(doc):
            text = clean_text(page.get_text("text"))
            if text:
                yield idx + 1, text
    finally:
        doc.close()


def extract_text_file(path: Path) -> Iterator[tuple[Optional[int], str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = clean_text(text)
    if text:
        yield None, text


def extract_html_file(path: Path) -> Iterator[tuple[Optional[int], str]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parser = TextHTMLParser()
    parser.feed(raw)
    text = clean_text(parser.text())
    if text:
        yield None, text


def flatten_json_strings(obj, path: str = "") -> Iterator[tuple[str, str]]:
    """
    Conservative JSON extraction:
    - emits string values with their JSON key path
    - does not attempt to infer religious metadata
    """
    if isinstance(obj, str):
        value = clean_text(obj)
        if value:
            yield path or "$", value
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from flatten_json_strings(item, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from flatten_json_strings(value, child)


def extract_json_file(path: Path) -> Iterator[tuple[Optional[int], str]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    blocks = []
    for key_path, value in flatten_json_strings(obj):
        blocks.append(f"{key_path}\n{value}")
    if blocks:
        yield None, "\n\n".join(blocks)


def extract_source(path: Path) -> Iterator[tuple[Optional[int], str]]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        yield from extract_pdf(path)
    elif ext in {".txt", ".md"}:
        yield from extract_text_file(path)
    elif ext in {".html", ".htm"}:
        yield from extract_html_file(path)
    elif ext == ".json":
        yield from extract_json_file(path)
    else:
        raise ValueError(f"Unsupported source type: {path}")


SCHEMA = """
PRAGMA journal_mode = DELETE;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS build_meta;
DROP TABLE IF EXISTS chunks_fts;
DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS sources;

CREATE TABLE sources (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'other',
    version TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    sha256 TEXT NOT NULL,
    subcategory TEXT,
    edition TEXT,
    language TEXT,
    marja TEXT,
    official_source INTEGER,
    is_current INTEGER,
    review_status TEXT NOT NULL DEFAULT 'pending',
    quality_score REAL,
    created_at TEXT,
    updated_at TEXT,
    CHECK (review_status IN ('legacy_trusted', 'pending', 'reviewed', 'approved', 'rejected'))
);

CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page INTEGER,
    chapter TEXT,
    topic TEXT,
    text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    quality_score REAL,
    UNIQUE(source_id, chunk_index)
);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id UNINDEXED,
    source_id UNINDEXED,
    title,
    author,
    category,
    text,
    normalized_text,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TABLE build_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX idx_chunks_source ON chunks(source_id);
CREATE INDEX idx_chunks_page ON chunks(page);
CREATE INDEX idx_sources_category ON sources(category);
CREATE INDEX idx_sources_review_status ON sources(review_status);
CREATE INDEX idx_sources_marja ON sources(marja);
CREATE INDEX idx_sources_current ON sources(is_current);
"""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def build(args: argparse.Namespace) -> None:
    manifest_path = Path(args.manifest)
    sources_root = Path(args.sources)
    output_path = Path(args.output)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunk_cfg = manifest.get("chunking", {})
    target = int(chunk_cfg.get("target_chars", 1500))
    overlap = int(chunk_cfg.get("overlap_chars", 220))
    min_chars = int(chunk_cfg.get("min_chars", 180))

    enabled_sources = [s for s in manifest.get("sources", []) if s.get("enabled", False)]
    if not enabled_sources:
        raise SystemExit(
            "No enabled sources found in manifest.json. "
            "Add approved sources and set enabled=true."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=output_path.name + ".building-",
        suffix=".sqlite",
        dir=output_path.parent,
    )
    # SQLite can initialise a new schema in this unique empty staging file.
    # Do not alter any pre-existing build artifact while preparing a release.
    temporary_output = Path(temporary_name)
    import os
    os.close(descriptor)
    # Build into a sibling file.  A failed build never damages the current
    # known-good database; a successful build is atomically swapped at the end.
    phase5_manifest = manifest.get("phase5")
    legacy_source_ids = set((phase5_manifest or {}).get("legacy_source_ids", []))
    # A v1 manifest describes only released sources, so it remains readable as
    # legacy trusted.  Once a manifest opts into Phase 5, every newly added
    # source must explicitly pass review or it remains pending.
    legacy_manifest = phase5_manifest is None
    report = fresh_quality_report()
    con = sqlite3.connect(temporary_output)
    try:
        con.executescript(SCHEMA)
        total_chunks = 0

        for source in enabled_sources:
            required = {"id", "path", "title"}
            missing = required - set(source)
            if missing:
                raise ValueError(f"Source missing required fields {missing}: {source}")

            src_path = sources_root / source["path"]
            if not src_path.is_file():
                raise FileNotFoundError(
                    f"Manifest source not found: {src_path}"
                )

            sid = str(source["id"])
            review_status = validate_source_metadata(
                source,
                legacy=legacy_manifest or sid in legacy_source_ids,
            )
            title = str(source["title"])
            author = str(source.get("author", ""))
            category = normalize_category(source.get("category", "other"))
            version = str(source.get("version", ""))
            notes = str(source.get("notes", ""))
            sha = file_sha256(src_path)
            timestamp = utc_now()

            con.execute(
                """
                INSERT INTO sources
                (id, path, title, author, category, version, notes, sha256,
                 subcategory, edition, language, marja, official_source,
                 is_current, review_status, quality_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid, source["path"], title, author, category, version, notes, sha,
                    source.get("subcategory"), source.get("edition"), source.get("language"),
                    source.get("marja"), source.get("official_source"), source.get("is_current"),
                    review_status, None, timestamp, timestamp,
                ),
            )

            report["sources"][review_status] += 1
            report["categories"][category] += 1
            if source.get("marja"):
                report["marja_sources"][str(source["marja"])] += 1

            # Pending, reviewed, and rejected sources are recorded for audit
            # but never become searchable production evidence.
            if review_status not in PRODUCTION_REVIEW_STATES:
                print(f"[SKIP] {title}: review_status={review_status}")
                continue

            chunk_index = 0
            source_quality_scores = []
            for page, block in extract_source(src_path):
                for piece in paragraph_chunks(block, target, overlap, min_chars):
                    quality, reasons = passage_quality(piece)
                    if reasons:
                        report["chunks"]["rejected"] += 1
                        report["corruption"].update(reasons)
                        continue
                    cid = stable_id(sid, str(page or 0), str(chunk_index), piece[:200])
                    normalized = normalize_for_search(piece)
                    chapter = source.get("chapter")
                    topic = source.get("topic")

                    con.execute(
                        """
                        INSERT INTO chunks
                        (id, source_id, chunk_index, page, chapter, topic, text, normalized_text, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cid, sid, chunk_index, page,
                            chapter, topic, piece, normalized, quality
                        ),
                    )
                    con.execute(
                        """
                        INSERT INTO chunks_fts
                        (chunk_id, source_id, title, author, category, text, normalized_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cid, sid, title, author, category, piece, normalized
                        ),
                    )
                    chunk_index += 1
                    total_chunks += 1
                    source_quality_scores.append(quality)
                    report["chunks"]["usable"] += 1

            if chunk_index == 0:
                # Legacy sources remain visible in metadata for gradual human
                # review, but unsafe extraction must not become evidence.  An
                # explicitly approved source failing this gate is a release
                # failure because it was expected to provide production text.
                report["sources"]["technical_blocked"] += 1
                con.execute(
                    "UPDATE sources SET quality_score = 0 WHERE id = ?",
                    (sid,),
                )
                if review_status == "approved":
                    raise RuntimeError(f"No usable, safe text found in approved source: {src_path}")
                print(f"[BLOCKED] {title}: no usable safe extraction; human review required")
                continue

            con.execute(
                "UPDATE sources SET quality_score = ? WHERE id = ?",
                (sum(source_quality_scores) / len(source_quality_scores), sid),
            )

            print(f"[OK] {title}: {chunk_index} chunks")

        build_meta = {
            "manifest_version": str(manifest.get("version", "unknown")),
            "knowledge_version": str(manifest.get("knowledge_version", manifest.get("version", "unknown"))),
            "build_timestamp": utc_now(),
            "source_count": str(len(enabled_sources)),
            "chunk_count": str(total_chunks),
            "schema_version": str(SCHEMA_VERSION),
            "quality_report_version": str(QUALITY_REPORT_VERSION),
        }
        for state in ("legacy_trusted", "pending", "reviewed", "approved", "rejected"):
            build_meta[f"{state}_source_count"] = str(report["sources"][state])
        con.executemany(
            "INSERT INTO build_meta(key, value) VALUES (?, ?)",
            build_meta.items(),
        )
        con.commit()

        # Compact DB and ensure FTS integrity.
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('optimize')")
        con.commit()
        con.execute("VACUUM")
        con.commit()

    finally:
        con.close()

    report_path = Path(args.quality_report) if args.quality_report else output_path.with_suffix(".quality.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(json_ready_report(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_output.replace(output_path)

    print(f"\nBuilt: {output_path}")
    print(f"Sources: {len(enabled_sources)}")
    print(f"Chunks: {total_chunks}")
    print(f"Quality report: {report_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="knowledge/manifest.json")
    p.add_argument("--sources", default="knowledge/sources")
    p.add_argument("--output", default="knowledge/output/hawza_knowledge.sqlite")
    p.add_argument("--quality-report", help="Write a Phase 5 JSON quality report here")
    return p.parse_args()


if __name__ == "__main__":
    build(parse_args())
