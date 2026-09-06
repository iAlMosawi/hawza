"""Shared Phase 5 taxonomy, metadata, and evidence-quality helpers.

This module deliberately makes technical validation separate from religious
review. It can identify unsafe extraction, but it never declares a source
religiously authoritative.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
import unicodedata


SCHEMA_VERSION = 2
QUALITY_REPORT_VERSION = 1

REVIEW_STATES = frozenset({
    "legacy_trusted", "pending", "reviewed", "approved", "rejected",
})
PRODUCTION_REVIEW_STATES = frozenset({"legacy_trusted", "approved"})

CATEGORIES = frozenset({
    "quran-tafsir", "hadith", "aqeedah", "imamate", "ahl-al-bayt",
    "seerah", "karbala", "ashura", "arbaeen", "ethics", "spirituality",
    "dua-ziyarat", "dua-commentary", "hussaini-khitaba", "quran-sciences",
    "history", "hawza", "fiqh", "marja-specific", "bahraini-shia-heritage",
    "ramadan", "usul", "kalam", "mahdawiyyah", "tabligh",
    "islamic-thought", "wilayah", "other",
})

LEGACY_CATEGORY_MAP = {
    "aqidah-tafsir-sirah": "aqeedah",
    "aqidah": "aqeedah",
    "ethics-wilayah": "ethics",
    "hadith-ethics": "hadith",
    "islamic-thought": "hawza",
    "sirah": "seerah",
    "wilayah": "imamate",
}

_ARABIC = r"\u0600-\u06FF"
_EMBEDDED_DIGIT = re.compile(rf"(?<=[{_ARABIC}])[0-9]+(?=[{_ARABIC}])")
_ARABIC_LATIN = re.compile(rf"(?<=[{_ARABIC}])[A-Za-z]+(?=[{_ARABIC}])")
_MALFORMED_MARKER = re.compile(r"[{}|]")
_EXCESSIVE_GARBAGE = re.compile(r"[.\-_=*]{12,}")
_MALFORMED_SYMBOL = re.compile(r"[@#$~`]")

# These are Unicode formatting controls frequently emitted by PDF extractors.
# They change direction/joining presentation but do not introduce or replace
# Arabic letters. They are therefore diagnostic-only rather than a reason to
# reject an otherwise clean religious passage. Substantive corruption signals
# below remain blocking. No Arabic/Qur'an/hadith/fiqh wording is reconstructed.
_NONSEMANTIC_FORMAT_CONTROLS = frozenset({
    "\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\u202a", "\u202b",
    "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
    "\ufeff",
})

_WEB_ARTIFACT = re.compile(
    r"(?:\bvar\s+[A-Za-z_$]|\b(?:let|const)\s+[A-Za-z_$]|window\.(?:jQuery|\$)|"
    r"document\.write|\b(?:function|onclick|querySelector)\s*\(|<\s*/?script\b)",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_review_status(value: object, *, legacy: bool) -> str:
    if value is None or str(value).strip() == "":
        return "legacy_trusted" if legacy else "pending"
    state = str(value).strip()
    if state not in REVIEW_STATES:
        raise ValueError(f"Unknown review_status: {state}")
    return state


def normalize_category(value: object) -> str:
    category = str(value or "other").strip()
    category = LEGACY_CATEGORY_MAP.get(category, category)
    if category not in CATEGORIES:
        raise ValueError(f"Unknown controlled category '{category}'")
    return category


def validate_source_metadata(source: dict, *, legacy: bool) -> str:
    category = normalize_category(source.get("category", "other"))
    state = normalize_review_status(source.get("review_status"), legacy=legacy)
    for boolean_field in ("official_source", "is_current"):
        value = source.get(boolean_field)
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"{boolean_field} must be a boolean or null for source {source.get('id')}")
    if source.get("marja") and category not in {"fiqh", "marja-specific"}:
        raise ValueError(f"marja metadata is only valid for fiqh sources: {source.get('id')}")
    return state


def nonsemantic_format_control_count(text: str) -> int:
    """Count PDF/HTML direction-formatting controls for audit reporting only."""
    return sum(char in _NONSEMANTIC_FORMAT_CONTROLS for char in str(text or ""))


def strip_nonsemantic_format_controls(text: str) -> str:
    """Remove presentation-only Unicode controls without changing base text."""
    return "".join(
        char for char in str(text or "")
        if char not in _NONSEMANTIC_FORMAT_CONTROLS
    )


def corruption_reasons(text: str, *, minimum_chars: int = 80) -> list[str]:
    """Return objective extraction-risk indicators; never repair the text."""
    value = str(text or "")
    reasons: list[str] = []
    if "\ufffd" in value:
        reasons.append("replacement_character")
    if _EMBEDDED_DIGIT.search(value):
        reasons.append("arabic_embedded_digit")
    if _ARABIC_LATIN.search(value):
        reasons.append("arabic_latin_corruption")
    if _MALFORMED_MARKER.search(value):
        reasons.append("malformed_brace_or_pipe")
    if _WEB_ARTIFACT.search(value):
        reasons.append("website_or_javascript_artifact")
    if _EXCESSIVE_GARBAGE.search(value):
        reasons.append("excessive_punctuation_garbage")
    if _MALFORMED_SYMBOL.search(value):
        reasons.append("malformed_symbols")
    visible = "".join(char for char in value if not char.isspace() and char not in _NONSEMANTIC_FORMAT_CONTROLS)
    if len(visible) < minimum_chars:
        reasons.append("very_short_passage")
    if any(
        unicodedata.category(char) in {"Cc", "Cs"} and not char.isspace()
        for char in value
    ):
        reasons.append("unexpected_control_character")
    return reasons


def passage_quality(text: str) -> tuple[float, list[str]]:
    reasons = corruption_reasons(text)
    return max(0.0, 100.0 - (25.0 * len(reasons))), reasons


def fresh_quality_report() -> dict:
    return {
        "quality_report_version": QUALITY_REPORT_VERSION,
        "generated_at": utc_now(),
        "sources": Counter(),
        "chunks": Counter(),
        "corruption": Counter(),
        "categories": Counter(),
        "marja_sources": Counter(),
    }


def json_ready_report(report: dict) -> dict:
    return {
        **report,
        "sources": dict(sorted(report["sources"].items())),
        "chunks": dict(sorted(report["chunks"].items())),
        "corruption": dict(sorted(report["corruption"].items())),
        "categories": dict(sorted(report["categories"].items())),
        "marja_sources": dict(sorted(report["marja_sources"].items())),
    }
