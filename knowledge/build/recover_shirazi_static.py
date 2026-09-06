#!/usr/bin/env python3
"""Recover the official Arabic text of المسائل الإسلامية from alshirazi.org.

This is an isolated Phase-5 recovery helper. It never edits or deploys the
production database. The official library item is now server-rendered with the
book text, so this path deliberately avoids the older dynamic TOC/CSRF reader
and the unsafe embedded Unicode layer of the PDF.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

SOURCE_ID = "masail-islamiyya-sadiq-al-shirazi"
LEGACY_ALIAS = "risala-amaliyya-shirazi"
OFFICIAL_URL = "https://www.alshirazi.org/library-item/203?langs=AR"
START_MARKERS = ("مقدمة المسائل الاسلامية", "مقدمة المسائل الإسلامية")
END_MARKER = "كتب ذات صلة"


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(re.sub(r"\s+", " ", data).strip())


def extract_book_text(html: str) -> str:
    parser = VisibleText()
    parser.feed(html)
    parts = parser.parts
    start = None
    for index, part in enumerate(parts):
        if any(marker in part for marker in START_MARKERS):
            start = index
            break
    if start is None:
        raise RuntimeError("official book start marker not found")
    end = None
    for index in range(start + 1, len(parts)):
        if END_MARKER in parts[index]:
            end = index
            break
    if end is None:
        raise RuntimeError("official book end marker not found; refusing partial extraction")
    selected = parts[start:end]
    text = "\n".join(selected).strip()
    if len(text) < 100_000:
        raise RuntimeError(f"official structured text unexpectedly short: {len(text)} chars")
    required = ("أصول الدين", "أحكام التقليد", "أحكام الطهارة", "أحكام الصلاة", "أحكام الصوم", "أحكام الإرث")
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError("missing expected book sections: " + ", ".join(missing))
    forbidden = ("�", "javascript:")
    if any(marker in text for marker in forbidden):
        raise RuntimeError("unsafe/corrupt content marker in extracted official text")
    return text


def fetch() -> bytes:
    req = Request(OFFICIAL_URL, headers={
        "User-Agent": "Noor-AlHawza-authoritative-recovery/1.2",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ar,en;q=0.7",
        "Accept-Encoding": "identity",
    })
    with urlopen(req, timeout=60) as response:
        return response.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = fetch()
    html = raw.decode("utf-8", errors="strict")
    text = extract_book_text(html)
    raw_path = args.output / "shirazi-library-item-203.html"
    text_path = args.output / f"{SOURCE_ID}.txt"
    raw_path.write_bytes(raw)
    text_path.write_text(text, encoding="utf-8")
    report = {
        "status": "ACQUIRED_PENDING_GATE_REVIEW",
        "source_id": SOURCE_ID,
        "legacy_alias": LEGACY_ALIAS,
        "canonical_title": "المسائل الإسلامية",
        "attribution": "السيد صادق الحسيني الشيرازي",
        "official_source": True,
        "official_url": OFFICIAL_URL,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "text_chars": len(text),
        "method": "official_server_rendered_library_item",
        "pdf_unicode_layer_used": False,
        "ocr_used": False,
    }
    (args.output / "shirazi_static_recovery.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
