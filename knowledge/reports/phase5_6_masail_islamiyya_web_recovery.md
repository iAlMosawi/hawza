# Phase 5.6: Official Web Text Recovery

## Result

The official web reading version was found. The library detail route links to
a separate public reading route:

`https://www.alshirazi.org/library-htmlItem/203?langs=AR`

The reader contains 532 table-of-contents entries covering the introduction,
theology, ethics, and the fiqh sections. Selecting a section loads Arabic HTML
into `#treatiseResults` through this public endpoint:

`POST https://www.alshirazi.org/esteftatreatiseBook`

The observed request parameters are `itemId`, `langs`, `catIdCur`,
`ShareTreatiseRoot`, and the page-provided CSRF token. The response is an HTML
fragment, not a JSON or GraphQL response. No login was required during the
public-reader inspection.

## Identity evidence

The official library identifies the work as `المسائل الاسلامية`, published by
`مكتب المرجع الشيرازي`. The reader’s table of contents includes sections such
as `أحكام الطهارة`, `الوضوء`, `أحكام الجنابة`, `التيمم`, `أحكام الصلاة`, and
`المسائل الحديثة`. The first selected section returned clean Arabic HTML
beginning with the book’s introduction.

## Redirect behavior

Direct automated requests to the library detail route follow a `www` canonical
redirect loop. The reader route itself loads in the browser. No authentication,
Cloudflare, or anti-bot restriction was bypassed.

## Acceptance status

This is a verified official-reader candidate, but it has **not** yet been
accepted as a replacement source. The required 25-passage PDF comparison and
full Phase 5 quality scan were not completed because browser automation timed
out while expanding the deeply nested table of contents. No web text was
written to a staging or production database.

The safe next step is a bounded read-only harvester for the identified public
endpoint. It must collect at least 25 passages across the beginning, middle,
and end of the work, compare them with rendered PDF pages, run the unchanged
Phase 5 gates, and only then create an isolated source-only database. The
legacy ID `risala-amaliyya-shirazi` must remain an alias and must not restore
the old incorrect title/author metadata.
