#!/usr/bin/env python3
"""Extract only book sections from the official Leader.ir book page."""
from __future__ import annotations

from html.parser import HTMLParser
import re


class LeaderBookParser(HTMLParser):
    """Keep article headings/details; exclude the site's surrounding chrome."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0
        self._body = 0
        self._capture = 0
        self._heading = 0
        self._ui_skip = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
            return
        if self._skip:
            return
        ident = values.get("id", "")
        classes = set((values.get("class") or "").split())
        if self._heading and tag == "a" and ("pull-left" in classes or values.get("title") == "PDF"):
            self._ui_skip += 1
            return
        if ident == "body":
            self._body = 1
            return
        if not self._body:
            return
        self._body += 1
        if "article_heading" in classes:
            self._heading = self._body
        if "details" in classes:
            self._capture = self._body
        elif tag == "h6" and self._heading:
            self._capture = self._body

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
            return
        if self._ui_skip and tag == "a":
            self._ui_skip -= 1
            return
        if self._skip or not self._body:
            return
        if self._capture == self._body:
            self._capture = 0
        if self._heading == self._body:
            self._heading = 0
        self._body -= 1
        if self._body == 0:
            self._body = 0

    def handle_data(self, data):
        if self._capture and not self._skip and not self._ui_skip and data.strip():
            self.parts.append(data)


def extract_book(raw: bytes) -> str:
    parser = LeaderBookParser()
    parser.feed(raw.decode("utf-8", errors="strict"))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
