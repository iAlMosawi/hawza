#!/usr/bin/env python3
"""Acquire registry-listed public HTML sources into an isolated cache.

This tool never edits the production database. It only downloads public
official/institutional pages and writes provenance plus semantic text files to
the caller-provided staging directory.

For Sistani book roots, the reader is hierarchical: the root page is a table of
contents and the actual rulings live on child section URLs. This harvester
therefore expands each official book root into all same-book child sections
before extraction. This avoids silently treating a TOC-only download as a
complete book.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SISTANI_ROOT_RE = re.compile(r"^/arabic/book/(\d+)/?$")
SISTANI_SECTION_RE = re.compile(r"^/arabic/book/(\d+)/(\d+)/?$")


class SemanticText(HTMLParser):
    def __init__(self, site: str):
        super().__init__(convert_charrefs=True)
        self.site = site
        self.depth = 0
        self.parts: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._main_depth = 0
        self._capture_root_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        values = dict(attrs)
        if tag == "meta" and values.get("property") in {"og:title", "title"}:
            self.title = values.get("content", "")
        ident = values.get("id", "")
        classes = set((values.get("class") or "").split())
        if self.site == "almaaref":
            if ident.startswith("page-") and ident != "page-book-description":
                self.depth = 1
            elif self.depth:
                self.depth += 1
        elif self.site == "sistani":
            if ident == "main-book-content":
                self._main_depth = 1
            elif self._main_depth:
                self._main_depth += 1
                # Sistani places the actual content in book-text. The parent
                # container also contains search, pager, language, and book
                # recommendation UI, so those nodes are intentionally not
                # captured.
                if "book-text" in classes:
                    self._capture_root_depth = self._main_depth
                elif tag == "h1":
                    self._capture_root_depth = self._main_depth

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if self.site == "sistani" and self._main_depth:
            if self._capture_root_depth == self._main_depth:
                self._capture_root_depth = 0
            self._main_depth -= 1
            return
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if ((self.site == "sistani" and self._capture_root_depth and self._main_depth >= self._capture_root_depth) or
                (self.site != "sistani" and self.depth)) and not self._skip_depth and data.strip():
            self.parts.append(data)


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


@dataclass
class Record:
    source_id: str
    status: str
    source_urls: list[str]
    title: str = ""
    text_file: str | None = None
    raw_files: list[str] | None = None
    text_sha256: str | None = None
    raw_sha256: list[str] | None = None
    text_chars: int = 0
    error: str | None = None


def fetch(url: str) -> bytes:
    request = Request(url, headers={
        "User-Agent": "Noor-AlHawza-authoritative-recovery/1.1",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ar,en;q=0.8",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=30) as response:
        return response.read()


def semantic_text(raw: bytes, site: str) -> tuple[str, str]:
    parser = SemanticText(site)
    parser.feed(raw.decode("utf-8", errors="strict"))
    text = "\n".join(re.sub(r"\s+", " ", part).strip() for part in parser.parts)
    return parser.title.strip(), text.strip()


def sistani_section_urls(root_url: str, raw: bytes) -> list[str]:
    """Return deterministic same-book section URLs discovered on a Sistani TOC."""
    parsed = urlparse(root_url)
    root_match = SISTANI_ROOT_RE.match(parsed.path)
    if not root_match:
        return []
    book_id = root_match.group(1)
    collector = LinkCollector()
    collector.feed(raw.decode("utf-8", errors="strict"))
    found: dict[int, str] = {}
    for href in collector.hrefs:
        absolute = urljoin(root_url, href)
        candidate = urlparse(absolute)
        if candidate.netloc != parsed.netloc:
            continue
        match = SISTANI_SECTION_RE.match(candidate.path)
        if not match or match.group(1) != book_id:
            continue
        section_id = int(match.group(2))
        found[section_id] = f"{parsed.scheme}://{parsed.netloc}{candidate.path}"
    return [found[key] for key in sorted(found)]


def registry_urls(item: dict) -> list[str]:
    if item.get("reader_url"):
        return [item["reader_url"]]
    if item.get("volume_urls"):
        return list(item["volume_urls"])
    # The Shirazi source intentionally uses a specialized reader/POST workflow.
    # Do not silently ingest the dynamic reader shell as if it were the book.
    return []


def apply_registry_overrides(registry: dict, registry_path: Path) -> dict:
    """Merge optional source-field overrides without mutating the base registry."""
    override_path = registry_path.with_name("authoritative_source_recovery_overrides.json")
    if not override_path.exists():
        return registry
    overrides = json.loads(override_path.read_text(encoding="utf-8"))
    by_id = {item["source_id"]: item for item in registry.get("sources", [])}
    for patch in overrides.get("sources", []):
        sid = patch.get("source_id")
        if sid not in by_id:
            raise RuntimeError(f"override references unknown source_id: {sid}")
        for key, value in patch.items():
            if key != "source_id":
                by_id[sid][key] = value
    return registry


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--registry", type=Path, required=True)
    args.add_argument("--output", type=Path, required=True)
    args.add_argument("--interval", type=float, default=1.0)
    ns = args.parse_args()
    registry = apply_registry_overrides(json.loads(ns.registry.read_text(encoding="utf-8")), ns.registry)
    ns.output.mkdir(parents=True, exist_ok=True)
    (ns.output / "raw").mkdir(exist_ok=True)
    (ns.output / "text").mkdir(exist_ok=True)
    records: list[Record] = []

    for item in registry["sources"]:
        sid = item["source_id"]
        urls = registry_urls(item)
        if not urls:
            detail = "No static public reader URL in authoritative registry"
            if item.get("official_section_endpoint"):
                detail = "Requires specialized official reader harvester; static recovery intentionally skipped"
            records.append(asdict(Record(sid, "BLOCKED_SOURCE_REPLACEMENT_REQUIRED", [], error=detail)))
            continue

        site = "sistani" if "sistani.org" in urls[0] else "almaaref"
        raw_files: list[str] = []
        raw_hashes: list[str] = []
        text_parts: list[str] = []
        source_urls: list[str] = []
        title = ""
        try:
            queue = list(urls)
            seen: set[str] = set()
            index = 0
            while queue:
                url = queue.pop(0)
                if url in seen:
                    continue
                seen.add(url)
                raw = fetch(url)
                index += 1
                raw_path = ns.output / "raw" / f"{sid}-{index}.html"
                raw_path.write_bytes(raw)
                raw_files.append(str(raw_path))
                raw_hashes.append(hashlib.sha256(raw).hexdigest())
                source_urls.append(url)

                parsed_title, text = semantic_text(raw, site)
                title = title or parsed_title
                if text:
                    text_parts.append(text)

                if site == "sistani":
                    for child in sistani_section_urls(url, raw):
                        if child not in seen and child not in queue:
                            queue.append(child)
                time.sleep(max(0.5, ns.interval))

            text = "\n\n".join(text_parts).strip()
            if len(text) < 500:
                raise RuntimeError(f"semantic text too short: {len(text)} characters")
            if site == "sistani" and len(source_urls) <= len(urls):
                raise RuntimeError("Sistani TOC expansion found no child sections; refusing partial-book ingestion")

            text_path = ns.output / "text" / f"{sid}.txt"
            text_path.write_text(text, encoding="utf-8")
            records.append(asdict(Record(
                sid,
                "ACQUIRED_PENDING_IDENTITY_AND_GATE_REVIEW",
                source_urls,
                title,
                str(text_path),
                raw_files,
                hashlib.sha256(text.encode()).hexdigest(),
                raw_hashes,
                len(text),
            )))
        except Exception as error:
            records.append(asdict(Record(
                sid,
                "BLOCKED_SOURCE_REPLACEMENT_REQUIRED",
                source_urls or urls,
                title,
                raw_files=raw_files,
                raw_sha256=raw_hashes,
                error=str(error),
            )))

    report = {"registry_version": registry.get("registry_version"), "records": records}
    (ns.output / "recovery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "acquired": sum(r["status"].startswith("ACQUIRED") for r in records),
        "blocked": sum(r["status"].startswith("BLOCKED") for r in records),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
