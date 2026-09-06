#!/usr/bin/env python3
"""Recover the official Arabic text of المسائل الإسلامية from alshirazi.org.

This is an isolated Phase-5 recovery helper. It never edits or deploys the
production database. The official library item is server-rendered with the book
text. This path avoids the unsafe embedded Unicode layer of the old PDF.
"""
from __future__ import annotations

import argparse
from http.cookiejar import CookieJar
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

SOURCE_ID = "masail-islamiyya-sadiq-al-shirazi"
LEGACY_ALIAS = "risala-amaliyya-shirazi"
OFFICIAL_URLS = (
    "https://www.alshirazi.org/library-item/203?langs=AR",
    "https://alshirazi.org/library-item/203?langs=AR",
)
HOME_URLS = (
    "https://www.alshirazi.org/",
    "https://alshirazi.org/",
)
START_MARKERS = ("مقدمة المسائل الاسلامية", "مقدمة المسائل الإسلامية")
END_MARKER = "كتب ذات صلة"
REQUIRED_SECTIONS = (
    "أصول الدين",
    "أحكام التقليد",
    "أحكام الطهارة",
    "أحكام الصلاة",
    "أحكام الصوم",
    "أحكام الإرث",
    "مسائل حديثة",
    "الفهرس",
)


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

    missing = [marker for marker in REQUIRED_SECTIONS if marker not in text]
    if missing:
        raise RuntimeError("missing expected book sections: " + ", ".join(missing))

    forbidden = ("�", "javascript:", "document.write", "querySelector(")
    if any(marker in text for marker in forbidden):
        raise RuntimeError("unsafe/corrupt content marker in extracted official text")
    return text


def _headers(referer: str) -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0 Safari/537.36 Noor-AlHawza-Recovery/1.3"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en;q=0.7",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": referer,
        "Upgrade-Insecure-Requests": "1",
    }


def fetch() -> tuple[str, bytes]:
    """Fetch with a real cookie jar; alshirazi may bootstrap a session by 302."""
    errors: list[str] = []
    for home_url, official_url in zip(HOME_URLS, OFFICIAL_URLS):
        jar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(jar))
        try:
            # Warm the official domain first so session/CSRF cookies survive the
            # redirect chain. Failure of the warm-up is non-fatal.
            try:
                opener.open(Request(home_url, headers=_headers(home_url)), timeout=30).read(256)
            except Exception:
                pass

            request = Request(official_url, headers=_headers(home_url))
            with opener.open(request, timeout=60) as response:
                raw = response.read()
                final_url = response.geturl()
            if len(raw) < 100_000:
                raise RuntimeError(f"official response unexpectedly short: {len(raw)} bytes")
            return final_url, raw
        except (HTTPError, URLError, RuntimeError) as exc:
            errors.append(f"{official_url}: {type(exc).__name__}: {exc}")

    raise RuntimeError("all official Shirazi fetch routes failed: " + " | ".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    final_url, raw = fetch()
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
        "requested_urls": list(OFFICIAL_URLS),
        "final_url": final_url,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "text_chars": len(text),
        "method": "official_server_rendered_library_item_cookie_session",
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
