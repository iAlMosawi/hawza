#!/usr/bin/env python3
"""Bounded, read-only client for the official alshirazi.org book reader.

The client only caches public HTML responses locally. It does not modify the
knowledge database and refuses to treat a partial harvest as complete.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import random
import re
import time
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener
from http.cookiejar import CookieJar


READER_URL = "https://www.alshirazi.org/library-htmlItem/203?langs=AR"
ENDPOINT = "https://www.alshirazi.org/esteftatreatiseBook"
CANONICAL_ID = "masail-islamiyya-sadiq-al-shirazi"
LEGACY_ALIAS = "risala-amaliyya-shirazi"
DEFAULT_INTERVAL = 1.25


class ReaderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.csrf = ""
        self.toc: list[dict[str, str]] = []
        self._span: dict[str, str] | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta" and values.get("name") == "csrf-token":
            self.csrf = values.get("content") or ""
        if tag == "input" and values.get("name") in {"_token", "csrf-token"}:
            self.csrf = values.get("value") or self.csrf
        if tag == "span" and values.get("class", "").find("acar_span") >= 0:
            rel = values.get("rel") or ""
            if rel:
                self._span = {"id": rel, "title": ""}
                self._parts = []

    def handle_data(self, data: str) -> None:
        if self._span is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._span is not None:
            self._span["title"] = " ".join("".join(self._parts).split())
            if self._span["title"]:
                self.toc.append(self._span)
            self._span = None
            self._parts = []


class FragmentParser(HTMLParser):
    """Extract only the reader's semantic `.rtl` content, not navigation."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if "rtl" in classes:
            self.depth = 1
        elif self.depth:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.parts.append(data)


@dataclass
class HarvestRecord:
    section_id: str
    title: str
    params: dict[str, str]
    retrieved_at: str
    raw_html_sha256: str | None = None
    text_sha256: str | None = None
    text_chars: int = 0
    status: str = "pending"
    error: str | None = None


class OfficialReaderClient:
    def __init__(self, output: Path, *, interval: float = DEFAULT_INTERVAL, retries: int = 3) -> None:
        self.output = output
        self.output.mkdir(parents=True, exist_ok=True)
        self.cache = self.output / "html"
        self.cache.mkdir(exist_ok=True)
        self.interval = max(0.5, interval)
        self.retries = max(0, retries)
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def _request(self, url: str, *, data: dict[str, str] | None = None) -> str:
        body = urlencode(data).encode() if data is not None else None
        request = Request(url, data=body, headers={
            "User-Agent": "Noor-AlHawza-knowledge-validation/5.7",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": READER_URL,
            "Content-Type": "application/x-www-form-urlencoded" if body else "text/html",
        })
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with self.opener.open(request, timeout=25) as response:
                    return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="strict")
            except (HTTPError, URLError, UnicodeError) as error:
                last_error = error
                if attempt < self.retries:
                    time.sleep((2 ** attempt) + random.random() / 4)
        raise RuntimeError(f"official reader request failed: {last_error}")

    def load_toc(self) -> tuple[str, list[dict[str, str]]]:
        page = self._request(READER_URL)
        parser = ReaderParser()
        parser.feed(page)
        if not parser.csrf:
            raise RuntimeError("reader page did not expose a CSRF token")
        if len(parser.toc) < 25:
            raise RuntimeError(f"reader exposed only {len(parser.toc)} TOC entries")
        return parser.csrf, parser.toc

    def fetch_section(self, csrf: str, item: dict[str, str]) -> HarvestRecord:
        params = {
            "itemId": item["id"],
            "langs": "AR",
            "catIdCur": "",
            "ShareTreatiseRoot": "",
            "_token": csrf,
        }
        record = HarvestRecord(section_id=item["id"], title=item["title"], params=params,
                               retrieved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        cache_path = self.cache / f"{item['id']}.html"
        try:
            raw = cache_path.read_text(encoding="utf-8") if cache_path.exists() else self._request(ENDPOINT, data=params)
            if not cache_path.exists():
                cache_path.write_text(raw, encoding="utf-8")
            parser = FragmentParser()
            parser.feed(raw)
            text = "\n".join(part.strip() for part in parser.parts if part.strip())
            record.raw_html_sha256 = hashlib.sha256(raw.encode()).hexdigest()
            record.text_sha256 = hashlib.sha256(text.encode()).hexdigest()
            record.text_chars = len(text)
            record.status = "ok" if text else "empty"
        except Exception as error:
            record.status = "failed"
            record.error = str(error)
        return record


def select_sample(toc: list[dict[str, str]], count: int = 25) -> list[dict[str, str]]:
    if len(toc) < count:
        raise ValueError("TOC is smaller than the required sample")
    indexes = sorted({round(i * (len(toc) - 1) / (count - 1)) for i in range(count)})
    return [toc[index] for index in indexes]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    client = OfficialReaderClient(args.output, interval=args.interval, retries=args.retries)
    try:
        csrf, toc = client.load_toc()
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error), "reader_url": READER_URL}, ensure_ascii=False))
        return 2
    selected = select_sample(toc) if args.sample else toc
    records = []
    for index, item in enumerate(selected):
        records.append(asdict(client.fetch_section(csrf, item)))
        if index + 1 < len(selected):
            time.sleep(client.interval)
    result = {
        "status": "complete" if len(records) == len(selected) and all(r["status"] == "ok" for r in records) else "partial",
        "canonical_source_id": CANONICAL_ID,
        "legacy_alias": LEGACY_ALIAS,
        "reader_url": READER_URL,
        "endpoint": ENDPOINT,
        "toc_count": len(toc),
        "selected_count": len(selected),
        "records": records,
    }
    (args.output / "harvest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "toc_count", "selected_count")}, ensure_ascii=False))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
