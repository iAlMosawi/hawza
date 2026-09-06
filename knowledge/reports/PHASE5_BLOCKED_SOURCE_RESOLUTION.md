# Noor Al-Hawza — Remaining Blocked Source Resolution

This document records the resolution work for the three sources that remained blocked after the clean Phase 5 corpus recovery. It changes no production database and does not itself approve evidence.

## 1. diyafa-bi-ayn-al-amin

**Canonical title:** ضيافة بعين الأمين

**Resolved identity/provenance:** public copies identify نور الحوزة as author/publisher. The published PDF contains an explicit `إجازة النشر` from `خدام نور الحوزة`, allowing electronic circulation while requiring content integrity.

**Legacy metadata correction:** the manifest author string `Abrar ghkh` is unverified and must not be used as canonical authorship.

**Repository legacy file:** `diyafa_ramadan.pdf` (145 pages in the Phase 5 audit).

**Remaining gate:** content-equivalence verification between the repository PDF and the verified publication copy, followed by normal clean extraction/corruption gates. Different byte size alone must not be treated as a content mismatch because PDF exports may differ.

**Status:** `identity_and_publication_provenance_verified_content_equivalence_pending`

Do not approve until the content-equivalence and extraction gates pass.

## 2. risala-ilmiyya-sayyid-qaid

**Legacy title:** الرسالة العلمية للسيد القائد

**Canonical title:** أجوبة الاستفتاءات

**Attribution:** السيد علي الحسيني الخامنئي

**Official structured source:** `https://www.leader.ir/ar/book/14/اجوبة-الإستفتاءات`

The official Leader.ir introduction states that the questions were received by the office of Sayyid Ali al-Husayni Khamenei, answered according to his rulings, and that he authorized the collection for publication after review. This resolves the previously ambiguous `السيد القائد` identity.

**Repository legacy file:** `knowledge/sources/alresala_alilmiya_lilsayyid_alqaed.pdf`, 706 pages according to the Phase 5 audit. The repository also contains an Arabic-named alias pointing to the same Git blob.

**Ingestion policy:** acquire the official structured HTML first. Do not rely on the legacy PDF text layer for production evidence. Preserve the legacy source ID for compatibility but use the official title and attribution in canonical metadata.

**Current-status warning:** do not infer `is_current=true`; current marja/ruling status must be an explicit policy decision rather than derived from the historical source identity.

**Status:** `official_identity_verified_structured_html_acquisition_pending`

## 3. risala-amaliyya-shirazi

**Recommended canonical source ID:** `masail-islamiyya-sadiq-al-shirazi`

**Legacy alias:** `risala-amaliyya-shirazi`

**Canonical title:** المسائل الإسلامية

**Attribution:** السيد صادق الحسيني الشيرازي

**Official reader:** `https://www.alshirazi.org/library-htmlItem/203?langs=AR`

**Official section endpoint:** `https://www.alshirazi.org/esteftatreatiseBook`

**Official PDF:** `https://alshirazi.org/data/library/pdf/1-1680299880-resaleh-web.pdf`

Identity is resolved. The PDF's visual content is authoritative, but its embedded Unicode layer is unsafe and must never be ingested. The repository already contains the specialized resumable `knowledge/build/official_reader_harvest.py` built for the official dynamic reader and its 532-entry TOC.

**Remaining gate:** complete the official reader harvest, preserve section provenance/hashes, run corruption gates and beginning/middle/end completeness checks, then stage only clean chunks.

**Status:** `official_identity_verified_specialized_reader_harvest_required`

## Production decision

None of the three sources should be silently substituted or admitted merely because identity has been resolved.

- Diyafa: identity/provenance resolved; content-equivalence + extraction still required.
- Sayyid al-Qaid: identity resolved as `أجوبة الاستفتاءات`; official structured HTML acquisition still required.
- Shirazi: identity resolved as `المسائل الإسلامية`; specialized official reader harvesting still required.

Production remains unchanged until these acquisition/quality gates pass and an approved-only database is built without `--include-reviewed`.
