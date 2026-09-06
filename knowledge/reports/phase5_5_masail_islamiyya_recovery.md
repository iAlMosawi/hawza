# Phase 5.5: `المسائل الإسلامية` Authoritative Text Recovery

## Scope and safety boundary

This report covers only the canonical source `masail-islamiyya-sadiq-al-shirazi`
(legacy alias: `risala-amaliyya-shirazi`). No production database, staging
database, source PDF, or source #2 was modified. No religious text was
reconstructed or added as evidence.

## Corrected identity

| Field | Verified value |
| --- | --- |
| Canonical ID | `masail-islamiyya-sadiq-al-shirazi` |
| Legacy alias | `risala-amaliyya-shirazi` |
| Title | `المسائل الإسلامية` |
| Attribution | `السيد صادق الحسيني الشيرازي` |
| Official PDF | `https://alshirazi.org/data/library/pdf/1-1680299880-resaleh-web.pdf` |
| SHA-256 | `4d713eaa7fcb726eda8abae9f6b8abf99c96c31c138bff0201af0b0f2eb19cc7` |
| Pages | 668 |

## Extraction diagnosis

Rendered body pages are visually readable Arabic, but the embedded extraction
layer is unsafe. It uses Identity-H subset fonts and special Islamic fonts;
PyMuPDF emits private-use glyphs such as `U+F04B`, `U+F031`, and `U+F043`,
or only whitespace/dot leaders, for pages that visibly contain Arabic. This
is consistent with a missing or unreliable Unicode mapping for the displayed
glyphs. The current embedded text cannot become religious evidence.

## Official digital-text search

The official library has an indexed Arabic text page:
`https://www.alshirazi.org/library-item/203?langs=AR`. The official site also
announced publication of the complete text:
`https://alshirazi.org/news-item/21910?langs=AR`.

Automated access to these pages currently enters a redirect loop, so this
pilot could not establish a complete, stable machine-readable text endpoint.
They are leads, not accepted source replacements.

## OCR pilot

Apple Vision OCR was run on 17 representative pages: 1, 2, 3, 10, 15, 25,
50, 100, 150, 200, 250, 335, 420, 500, 600, 660, and 668. No second reliable
Arabic OCR engine was installed, so two-engine agreement could not be tested.

After the narrowly corrected technical gates, 15 pages pass those gates, page
25 is rejected for Latin text embedded in Arabic, and page 100 is rejected as
too short. This is **not** acceptance: visible-to-OCR comparison found
recognition errors even on readable pages. OCR output must not be used as
fatwa/ruling evidence until a second engine and page-level verification show
reliable agreement.

## Safe gate corrections

Two false-positive rules were corrected and regression-tested:

1. Normal whitespace controls (newlines/tabs) are no longer treated as corrupt
   controls; non-whitespace `Cc`/`Cs` characters remain blocked.
2. Arabic-Indic numerals in numbered rulings are no longer treated as embedded
   digit corruption. ASCII digits embedded within Arabic words remain blocked,
   including the known corrupt form `الأ6سباب`.

All existing corruption protections for replacement characters, Arabic/Latin
mixes, malformed markers, bidi artifacts, punctuation garbage, short passages,
and true control characters remain in force.

## Classification

| Class | Result |
| --- | --- |
| A. Official digital text | Candidate found; not yet verified as complete and extractable. |
| B. OCR recoverable | Technically possible, but not acceptable from a one-engine pilot. |
| C. Safe gate fix | Completed and covered by regression tests. |
| D. Current PDF embedded text | Not recoverable as evidence retrieval text. |

## Recommendation

First obtain a stable official HTML/text or e-book endpoint for the verified
work. If one is unavailable, run a two-engine Arabic OCR pilot and require
human page-level verification before building any source-only staging database.
Do not deploy or stage OCR-derived religious evidence yet.
