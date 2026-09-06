# Noor Al-Hawza Phase 5 Recovery Execution

This is an isolated pre-production recovery result. The production database was not modified or deployed.

- Sources processed: 22
- Sources acquired: 19
- Sources blocked: 3
- Staging chunks: 2145
- Staging FTS rows: 2145
- Staging SHA-256: `68afc33ab93a561bbfa207d5aa406df9497602367d63b3f387e86e5718183d2d`
- Review state: all acquired sources remain `reviewed`; no source was marked `approved`.

## Source Results

| Source | Result | Text chars | Identity/provenance |
|---|---|---:|---|
| `diyafa-bi-ayn-al-amin` | blocked | 0 | No static public reader URL in authoritative registry |
| `durus-fikr-sadr` | acquired | 223685 | human review required |
| `tabligh-dini` | acquired | 209184 | human review required |
| `shakhsiyya-qiyadiyya` | acquired | 118990 | human review required |
| `durus-usul-aqidah` | acquired | 148109 | human review required |
| `wilayat-faqih` | acquired | 135196 | human review required |
| `tarbiyah-wilaiyyah` | acquired | 146516 | human review required |
| `durus-sirah` | acquired | 372101 | human review required |
| `durus-fikr-khamenei-1` | acquired | 188706 | human review required |
| `durus-fikr-khamenei-2` | acquired | 173369 | human review required |
| `durus-fikr-khomeini` | acquired | 262341 | human review required |
| `madkhal-usul` | acquired | 92841 | human review required |
| `madkhal-fiqh` | acquired | 100020 | human review required |
| `rihab-aqidah` | acquired | 242161 | human review required |
| `madkhal-kalam` | acquired | 88383 | human review required |
| `dirasat-ilahiyyat` | acquired | 414025 | human review required |
| `thaqafat-intizar` | acquired | 289819 | human review required |
| `nahj-rasul` | acquired | 320880 | human review required |
| `maaref-islam` | acquired | 464699 | human review required |
| `risala-ilmiyya-sayyid-qaid` | blocked | 0 | No static public reader URL in authoritative registry |
| `minhaj-salihin-1445` | acquired | 1876806 | human review required |
| `risala-amaliyya-shirazi` | blocked | 0 | Requires specialized official reader harvester; static recovery intentionally skipped |

## Verification

- SQLite integrity check: `ok`.
- FTS smoke searches returned results for التوكل, الإمامة, أهل البيت, and الفقه.
- Existing build/unit tests: 13 passed.
- Phase 5 production corruption gate: passed for staging evidence.
- Sistani structured recovery: 429 sections ({'23720': 233, '15': 97, '16': 99}), 1876806 characters, 4089 ruling-number matches, range 1–1611.
- Sistani representative beginning/middle/end samples are stored in the JSON report.
- The five blocked sources remain unresolved and were not substituted with uncertain material.

## Deployment Decision

Do not deploy this staging database yet. Human review must confirm identity, edition, provenance, and religious suitability before any source is promoted to `approved`.
