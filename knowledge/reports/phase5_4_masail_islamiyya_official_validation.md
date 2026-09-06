# Phase 5.4 Official Validation: `risala-amaliyya-shirazi`

## Decision

The existing manifest title and author are incorrect. The verified work is:

- Title: `المسائل الإسلامية`
- Rulings attributed on the title page to: `السيد صادق الحسيني الشيرازي`
- Category safely retained: `fiqh`

The direct official-domain candidate was downloaded from:

`https://alshirazi.org/data/library/pdf/1-1680299880-resaleh-web.pdf`

It is byte-for-byte identical to the current repository PDF. Both files have
SHA-256:

`4d713eaa7fcb726eda8abae9f6b8abf99c96c31c138bff0201af0b0f2eb19cc7`

They are 36 MB and 668 pages. Therefore they are the same work and the same
edition/content, not merely related editions. This establishes official
distribution provenance, but does not make the file technically usable.

## Validation

The official candidate was built in isolation only. It produced 108 candidate
chunks, 0 safe chunks, and 108 rejected chunks (100%). The Phase 5 release
validator failed as expected because the temporary database contained zero FTS
chunks.

Detected extraction issues:

- `unexpected_control_character`: 108
- `arabic_embedded_digit`: 42
- `excessive_punctuation_garbage`: 79
- `unusably_short_fragments`: 4,073

Manual extraction spot checks were also unusable: the first pages returned
private-use glyphs rather than Arabic text, a middle page returned dot leaders,
and the final page returned no text. The rendered title page was readable to a
human but is not a reliable embedded Arabic text layer.

No text was reconstructed or added to staging.

## Canonical ID and compatibility

Recommended future canonical source ID:

`masail-islamiyya-sadiq-al-shirazi`

Keep `risala-amaliyya-shirazi` only as a legacy citation/history alias mapped
to the canonical ID. Do not reuse the legacy ID as primary metadata because it
encodes the misidentified author/work.

## Metadata boundary

Evidence safely supports the corrected title, author attribution, `fiqh`
category, direct official-domain distribution, checksum, and page count.

Human confirmation is still required before setting `official_source=true`,
`is_current=true`, a normalized `marja`, or `review_status=approved`.
`is_current` is specifically not established by the downloaded file.

## Next input

Provide a newer or cleaner official Arabic digital edition of `المسائل
الإسلامية` whose Arabic text passes the unchanged Phase 5 corruption gates.
Only then should the isolated validation be repeated and presented for staging
approval.
