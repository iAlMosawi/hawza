#!/usr/bin/env python3
"""Acquire registry-listed public HTML sources into an isolated cache.

This tool never edits the production database. It only downloads public
official/institutional pages and writes provenance plus semantic text files to
the caller-provided staging directory.
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
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SemanticText(HTMLParser):
    def __init__(self, site: str):
        super().__init__(convert_charrefs=True)
        self.site = site
        self.depth = 0
        self.parts: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title_meta = False

    def handle_starttag(self, tag, attrs):
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
                self.depth = 1
            elif self.depth:
                self.depth += 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth and data.strip():
            self.parts.append(data)


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
        "User-Agent": "Noor-AlHawza-authoritative-recovery/1.0",
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


def main() -> int:
    args = argparse.ArgumentParser()
    args.add_argument("--registry", type=Path, required=True)
    args.add_argument("--output", type=Path, required=True)
    args.add_argument("--interval", type=float, default=1.0)
    ns = args.parse_args()
    registry = json.loads(ns.registry.read_text(encoding="utf-8"))
    ns.output.mkdir(parents=True, exist_ok=True)
    (ns.output / "raw").mkdir(exist_ok=True)
    (ns.output / "text").mkdir(exist_ok=True)
    records: list[Record] = []

    for item in registry["sources"]:
        sid = item["source_id"]
        urls: list[str] = []
        if item.get("reader_url"):
            urls = [item["reader_url"]]
        elif item.get("volume_urls"):
            urls = list(item["volume_urls"])
        else:
            records.append(asdict(Record(sid, "BLOCKED_SOURCE_REPLACEMENT_REQUIRED", urls, error="No public reader URL in authoritative registry")))
            continue
        site = "sistani" if "sistani.org" in urls[0] else "almaaref"
        raw_files: list[str] = []
        raw_hashes: list[str] = []
        text_parts: list[str] = []
        title = ""
        try:
            for index, url in enumerate(urls):
                raw = fetch(url)
                raw_path = ns.output / "raw" / f"{sid}-{index + 1}.html"
                raw_path.write_bytes(raw)
                raw_files.append(str(raw_path))
                raw_hashes.append(hashlib.sha256(raw).hexdigest())
                parsed_title, text = semantic_text(raw, site)
                title = title or parsed_title
                if text:
                    text_parts.append(text)
                time.sleep(max(0.5, ns.interval))
            text = "\n\n".join(text_parts).strip()
            if len(text) < 500:
                raise RuntimeError(f"semantic text too short: {len(text)} characters")
            text_path = ns.output / "text" / f"{sid}.txt"
            text_path.write_text(text, encoding="utf-8")
            records.append(asdict(Record(sid, "ACQUIRED_PENDING_IDENTITY_AND_GATE_REVIEW", urls, title, str(text_path), raw_files, hashlib.sha256(text.encode()).hexdigest(), raw_hashes, len(text))))
        except Exception as error:
            records.append(asdict(Record(sid, "BLOCKED_SOURCE_REPLACEMENT_REQUIRED", urls, title, raw_files=raw_files, raw_sha256=raw_hashes, error=str(error))))

    report = {"registry_version": registry.get("registry_version"), "records": records}
    (ns.output / "recovery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"acquired": sum(r["status"].startswith("ACQUIRED") for r in records), "blocked": sum(r["status"].startswith("BLOCKED") for r in records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
