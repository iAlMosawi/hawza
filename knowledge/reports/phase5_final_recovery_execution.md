# Noor Al-Hawza Phase 5 Recovery Execution

This is an isolated pre-production recovery result. The production database was not modified or deployed.

- Sources processed: 22
- Sources acquired: 17
- Sources blocked: 5
- Staging chunks: 1038
- Staging FTS rows: 1038
- Staging SHA-256: `831b73a3de56ce11a2c255db268352a72d84095a9b512d172ec531153425d878`
- Review state: all acquired sources remain `reviewed`; no source was marked `approved`.

## Source Results

| Source | Result | Text chars | Identity/provenance |
|---|---|---:|---|
| `diyafa-bi-ayn-al-amin` | blocked | 0 | No public reader URL in authoritative registry |
| `durus-fikr-sadr` | acquired | 223685 | human review required |
| `tabligh-dini` | acquired | 209184 | human review required |
| `shakhsiyya-qiyadiyya` | acquired | 118990 | human review required |
| `durus-usul-aqidah` | acquired | 148109 | human review required |
| `wilayat-faqih` | acquired | 135196 | human review required |
| `tarbiyah-wilaiyyah` | acquired | 146516 | human review required |
| `durus-sirah` | acquired | 372101 | human review required |
| `durus-fikr-khamenei-1` | blocked | 0 | No public reader URL in authoritative registry |
| `durus-fikr-khamenei-2` | blocked | 0 | No public reader URL in authoritative registry |
| `durus-fikr-khomeini` | acquired | 262341 | human review required |
| `madkhal-usul` | acquired | 92841 | human review required |
| `madkhal-fiqh` | acquired | 100020 | human review required |
| `rihab-aqidah` | acquired | 242161 | human review required |
| `madkhal-kalam` | acquired | 88383 | human review required |
| `dirasat-ilahiyyat` | acquired | 414025 | human review required |
| `thaqafat-intizar` | acquired | 289819 | human review required |
| `nahj-rasul` | acquired | 320880 | human review required |
| `maaref-islam` | acquired | 464699 | human review required |
| `risala-ilmiyya-sayyid-qaid` | blocked | 0 | No public reader URL in authoritative registry |
| `minhaj-salihin-1445` | acquired | 20317 | human review required |
| `risala-amaliyya-shirazi` | blocked | 0 | No public reader URL in authoritative registry |

## Verification

- SQLite integrity check: `ok`.
- FTS smoke searches returned results for التوكل, الإمامة, أهل البيت, and الفقه.
- Existing build/unit tests: 13 passed.
- Phase 5 production corruption gate: passed for staging evidence.
- The five blocked sources remain unresolved and were not substituted with uncertain material.

## Deployment Decision

Do not deploy this staging database yet. Human review must confirm identity, edition, provenance, and religious suitability before any source is promoted to `approved`.
