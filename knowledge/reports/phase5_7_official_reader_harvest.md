# Phase 5.7: Official Reader Harvest and Verification

## Result

The bounded read-only harvester is implemented at
`knowledge/build/official_reader_harvest.py`. It is limited to the verified
source `masail-islamiyya-sadiq-al-shirazi` and preserves
`risala-amaliyya-shirazi` only as a legacy alias.

No production database, staging database, manifest corpus, or source content
was modified. No source #2 was processed.

## Reader contract

| Item | Value |
| --- | --- |
| Reader | `https://www.alshirazi.org/library-htmlItem/203?langs=AR` |
| Section endpoint | `POST https://www.alshirazi.org/esteftatreatiseBook` |
| Required parameters | `itemId`, `langs`, `catIdCur`, `ShareTreatiseRoot`, `_token` |
| Session | Cookie-jar session preserved by the client |
| CSRF | Extracted from the reader page and sent as `_token` |
| Response | UTF-8 HTML fragment; semantic content is extracted only from `.rtl` |
| Cache | Local temporary output only, one HTML response per section ID |
| Safety | Minimum 0.5-second interval, bounded retries/backoff, fail-closed partial status |

The browser inspection previously confirmed 532 TOC entries and the same
endpoint contract. The local client does not click every section; it submits
the public reader’s documented request shape directly.

## 25-section preflight

The preflight did not pass. The deterministic local client timed out while
loading the official reader page before it could extract its CSRF token and
TOC. It therefore made no section requests, created no harvest corpus, and
did not silently treat the run as complete.

Run result:

```text
status: failed
error: The read operation timed out
reader_url: https://www.alshirazi.org/library-htmlItem/203?langs=AR
```

The existing browser session can render the reader, but its session state is
not exported to the local client. No authentication or anti-bot control was
bypassed.

## Verification status

The required 25 HTML-to-rendered-PDF comparisons, full quality-gate scan,
ruling-number continuity report, source-only database, and retrieval tests
remain pending. They must not be performed against incomplete or unverified
output.

## Tests

The complete knowledge build test suite passes: 12 tests. This includes the
three new harvester parser/sample tests plus the existing Phase 5 compatibility
and corruption-gate tests.

## Next safe step

Run the client from an environment that can reach the public reader with a
normal cookie/session exchange, or manually provide a browser-exported public
session only if the user explicitly wants that workflow. Then run the 25-item
preflight, perform rendered-PDF comparison, and continue to a full harvest only
after the sample passes.
