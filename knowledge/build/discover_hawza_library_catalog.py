#!/usr/bin/env python3
"""Discover the dynamic catalogue source behind hawza.netlify.app/book/.

Metadata discovery only: this tool does not download books, alter review state,
or modify any knowledge database. It fetches the public library page and its
same-site JavaScript assets, then reports candidate cloud/API/JSON endpoints for
human verification before catalogue synchronization is enabled.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

DEFAULT_URL = "https://hawza.netlify.app/book/"


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.srcs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            src = dict(attrs).get("src")
            if src:
                self.srcs.append(src)


def fetch(url: str) -> bytes:
    request = Request(url, headers={
        "User-Agent": "Noor-AlHawza-library-catalog-discovery/1.0",
        "Accept": "text/html,application/javascript,text/javascript,*/*;q=0.5",
        "Accept-Encoding": "identity",
    })
    with urlopen(request, timeout=45) as response:
        return response.read()


def candidate_urls(text: str, base_url: str) -> list[str]:
    patterns = [
        r"https?://[^\"'\s<>]+",
        r"[\"']([^\"']+\.json(?:\?[^\"']*)?)[\"']",
        r"[\"']([^\"']*/api/[^\"']*)[\"']",
        r"[\"']([^\"']*/\.netlify/functions/[^\"']*)[\"']",
    ]
    values: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1) if match.lastindex else match.group(0)
            value = value.rstrip("),;]}")
            if value.startswith(("http://", "https://")):
                absolute = value
            else:
                absolute = urljoin(base_url, value)
            low = absolute.lower()
            if any(token in low for token in (
                ".json", "/api/", ".netlify/functions/", "firebase", "firestore",
                "supabase", "googleapis", "drive.google", "storage.googleapis",
            )):
                values.add(absolute)
    return sorted(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, default=Path("knowledge/catalog/hawza_library_discovery.json"))
    args = parser.parse_args()

    raw = fetch(args.url)
    html = raw.decode("utf-8", errors="strict")
    scripts = Scripts()
    scripts.feed(html)

    page_candidates = candidate_urls(html, args.url)
    script_reports = []
    all_candidates = set(page_candidates)
    page_host = urlparse(args.url).netloc

    for src in scripts.srcs:
        script_url = urljoin(args.url, src)
        report = {"url": script_url, "status": "not_fetched", "candidates": []}
        if urlparse(script_url).netloc != page_host:
            report["status"] = "skipped_cross_origin"
            script_reports.append(report)
            continue
        try:
            body = fetch(script_url).decode("utf-8", errors="replace")
            found = candidate_urls(body, script_url)
            report.update({"status": "fetched", "bytes": len(body.encode("utf-8")), "candidates": found})
            all_candidates.update(found)
        except Exception as exc:
            report.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        script_reports.append(report)

    result = {
        "source_library": args.url,
        "mode": "metadata_endpoint_discovery_only",
        "page_bytes": len(raw),
        "script_count": len(scripts.srcs),
        "page_candidates": page_candidates,
        "scripts": script_reports,
        "candidate_endpoints": sorted(all_candidates),
        "next_step": "Human-verify the catalogue endpoint, export normalized book metadata, then run classify_hawza_library.py. Do not auto-approve or add catalogue entries to AI evidence.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scripts": len(scripts.srcs), "candidate_endpoints": len(all_candidates)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
