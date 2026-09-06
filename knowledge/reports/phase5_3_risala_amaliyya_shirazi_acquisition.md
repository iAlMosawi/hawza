# Phase 5.3 Acquisition Result: `risala-amaliyya-shirazi`

## Result

`VERIFIED_REPLACEMENT_NOT_FOUND`. No source was added to staging or production.

## Identity check

The manifest identifies this source as **الرسالة العملية للسيد رضا الشيرازي**
by **السيد رضا الشيرازي**. The title page of the current 668-page PDF instead
visibly reads **المسائل الإسلامية** and states that it is matched to the fatwas
of **السيد صادق الحسيني الشيرازي**. Its PDF metadata is not reliable identity
evidence: it says title `السيد رضا الشيرازي` and author `shafaee`.

Therefore the current file cannot be accepted as verified evidence for the
manifest target, independently of its failed extraction quality.

## Candidates inspected

1. `/Users/almosawi/Downloads/AlResala AlAmaleia - AlShirazi.pdf` was rejected.
   Its SHA-256 is identical to the current file:
   `4d713eaa7fcb726eda8abae9f6b8abf99c96c31c138bff0201af0b0f2eb19cc7`.
2. An official-domain search result from
   `alshirazi.org/data/library/pdf/1-1680299880-resaleh-web.pdf` was rejected
   without download. Its publisher description identifies `المسائل الإسلامية`
   associated with السيد محمد الحسيني الشيرازي and additions from السيد صادق
   الحسيني الشيرازي, not the requested work by السيد رضا الشيرازي.

## Required verified replacement

Provide an official author/institution/publisher file or a documented,
high-quality scan whose title page explicitly identifies:

- `الرسالة العملية للسيد رضا الشيرازي`
- `السيد رضا الشيرازي`

It must include verifiable provenance, edition/version, publisher or
institution, page count/completeness, and clean Arabic extraction. Phase 5
validation will then calculate its checksum, run corruption gates, inspect
samples, and test FTS in isolation before any staging decision.

## Human decision required first

Confirm whether the manifest target identity is correct. If it is not, the
existing source must be reclassified through a separate human review process;
this task did not change its title, author, marja, official/current state, or
religious approval status.
